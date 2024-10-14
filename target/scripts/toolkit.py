import os
import sys
import math
from tqdm import tqdm
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ..ui.utils import read_config, load_json, npy_to_csv
from ..ui.logger import LOG

################## functions used by the code
from ..scripts.rn_calc import rn_calc  # net radiation calcs  (3.1 tech notes)
from ..scripts.LUMPS import LUMPS  # energy balance calcs (3.2 tech notes)
from ..scripts.force_restore import Ts_calc_surf  # force restore calcs (3.3 tech notes)
from ..scripts.simple_water import Ts_EB_W  # simple water body model (3.4 tech notes)
from ..scripts.ld_mod import ld_mod  # model ldown (appendix tech notes)
from ..scripts.Ta_module_new import calc_ta  # air temperature module (3.5 tech notes)
from ..scripts.plotting import val_ts, val_ta, gis  # , gis   # Ash Broadbent's plotting functions
from ..scripts.SfcRi import sfc_ri
from ..scripts.Httc import httc
from ..scripts.CD import cd
from ..scripts import TbRurSolver
from ..scripts import UTCI


class Target:
    def __init__(self, control_file_name, progress=False):
        self.__validated = False

        ## surfaces types that are modelled.
        self.surfs = ['roof', 'road', 'watr', 'conc', 'Veg', 'dry', 'irr', 'wall']
        self.control_file_name = control_file_name
        self.progress = not progress

    def load_config(self):
        LOG.info("loading config")
        self.cfM = read_config(self.control_file_name)
        # parse dates for input met file using format defined in control file
        date_format = self.cfM['date_fmt']
        self.dateparse = lambda x: pd.to_datetime(x, format=date_format)
        # model run name
        self.run = self.cfM['run_name']
        # time step (minutes)
        self.tmstp = self.cfM['timestep']

        ######### DEFINE START AND FINISH DATES HERE ########
        ## the date/time that the simulation starts
        self.date1A = datetime.strptime(self.cfM['date1a'], "%Y,%m,%d,%H")
        ## the date/time for period of interest (i.e. before this will not be saved)
        self.date1 = datetime.strptime(self.cfM['date1'], "%Y,%m,%d,%H")
        ## end date/time of simulation
        self.date2 = datetime.strptime(self.cfM['date2'], "%Y,%m,%d,%H")
        ## tyime difference between start and end date
        tD = self.date2 - self.date1A

        # number of timesteps
        self.nt = divmod(tD.days * 86400 + tD.seconds,
                         (60 * int(self.tmstp)))[0]

        # date range for model period
        date_range = pd.date_range(self.date1,
                                   self.date2,
                                   freq=self.tmstp + 'T')

        # date range for model period (i.e. including spin-up period)
        date_range1A = pd.date_range(self.date1A,
                                     (self.date2 - timedelta(hours=1)),
                                     freq=self.tmstp + 'T')

        # this is a dictionary with all the date/time information
        self.Dats = {'date1A': self.date1A,
                     'date1': self.date1,
                     'date2': self.date2,
                     'date_range': date_range,
                     'date_rangeA': date_range1A}

        ###########################################################################################
        ### DEFINING PATHS

        if self.cfM["work_dir"] == "./":
            self.cfM["work_dir"] = os.getcwd()

        if self.cfM["para_json_path"].startswith("./"):
            self.cfM["para_json_path"] = self.cfM["para_json_path"].replace("./", os.getcwd())

        self.parameters = load_json(self.cfM['para_json_path'])

        self.LC_DATA = os.path.join(self.cfM['work_dir'], self.cfM['site_name'], 'input', 'LC',
                                    self.cfM['inpt_lc_file'])
        self.MET_FILE = os.path.join(self.cfM['work_dir'], self.cfM['site_name'], 'input', 'MET',
                                     self.cfM['inpt_met_file'])
        self.OUT_DIR = os.path.join(self.cfM['work_dir'], self.cfM['site_name'], 'output')
        self.SETTINGS_DIR = os.path.join(self.cfM['work_dir'], self.cfM['site_name'], 'settings')

    def run_simulation(self, save_csv=False, paras=None):

        LOG.info("running simulation")
        ################# read LC data  #####################
        # reads the input land cover data
        lc_data = pd.read_csv(self.LC_DATA)

        if paras is not None:

            self.parameters['alb']['roof'] = paras[0]
            self.parameters['alb']['road'] = paras[1]
            self.parameters['alb']['conc'] = paras[2]
            self.parameters['alb']['dry'] = paras[3]
            self.parameters['alb']['irr'] = paras[4]
            self.parameters['alb']['Veg'] = paras[5]

            self.parameters['emis']['roof'] = paras[6]
            self.parameters['emis']['road'] = paras[7]
            self.parameters['emis']['conc'] = paras[8]
            self.parameters['emis']['dry'] = paras[9]
            self.parameters['emis']['irr'] = paras[10]
            self.parameters['emis']['Veg'] = paras[11]

            self.parameters['K']['roof'] = paras[12]
            self.parameters['K']['road'] = paras[13]
            self.parameters['K']['conc'] = paras[14]
            self.parameters['K']['dry'] = paras[15]
            self.parameters['K']['irr'] = paras[16]

            self.parameters['C']['roof'] = paras[17]
            self.parameters['C']['road'] = paras[18]
            self.parameters['C']['conc'] = paras[19]
            self.parameters['C']['dry'] = paras[20]
            self.parameters['C']['irr'] = paras[21]

            # lc_data['H'][0] = paras[22]

        # if W is not in the input LC file, W is calculated as (cell size *  (1 - roof fraction))
        if not 'W' in lc_data.columns:
            lc_data['W'] = self.parameters['res'] * (1 - lc_data['roof'])
        elif lc_data['W'].isnull().all():
            lc_data['W'] = self.parameters['res'] * (1 - lc_data['roof'])

        zavg = self.parameters['zavg']
        if "zavg" in self.cfM.keys():
            zavg = float(self.cfM['zavg'])
        maxH = max(max(lc_data['H']), zavg)
        maxW = max(lc_data['W'])

        ########## DEFINE INPUT MET FILE LOCATION HERE #######
        # input meteorological forcing data file
        # convert to data frame
        self.met_data = pd.read_csv(self.MET_FILE, parse_dates=['datetime'], date_parser=self.dateparse,
                                    index_col=['datetime'])

        # read lat&lon info
        self.lonResolution = float(self.cfM['lonresolution'])
        self.latResolution = float(self.cfM['latresolution'])
        self.lonEdge = float(self.cfM['lonedge'])
        self.latEdge = float(self.cfM['latedge'])

        met_data_all = self.met_data.loc[
                       self.date1A:self.date2]  # main forcing meteorological dataframe (including spin up)
        met_data_all = met_data_all.interpolate(method='time')  # interpolates forcing data

        # if no longwave radiation is provided in the input, or if user wishes, Ld is modelled by TARGET ld_mod
        if not 'Ld' in met_data_all.columns:
            met_data_all['Ld'] = ld_mod(met_data_all)
        elif met_data_all['Ld'].isnull().all():
            met_data_all['Ld'] = ld_mod(met_data_all)
        elif self.cfM['mod_ldwn'] == 'Y':
            met_data_all['Ld'] = ld_mod(met_data_all)

        ########## DEFINE MAIN DATAFRAME ####################  dataframe for different modelled variables
        numberOfVf = 11
        mod_data_ts_ = np.zeros((self.nt, numberOfVf), np.dtype(
            [('roof', '<f8'), ('road', '<f8'), ('watr', '<f8'), ('conc', '<f8'), ('Veg', '<f8'), ('dry', '<f8'),
             ('irr', '<f8'), ('wall', '<f8'), ('TSOIL', '<f8'), ('avg', '<f8'), ('date', object)]))  # surface temperature of each surface
        mod_data_tm_ = np.zeros((self.nt, numberOfVf), np.dtype(
            [('roof', '<f8'), ('road', '<f8'), ('watr', '<f8'), ('conc', '<f8'), ('Veg', '<f8'), ('dry', '<f8'),
             ('irr', '<f8'), ('wall', '<f8'), ('TSOIL', '<f8'), ('avg', '<f8'), ('date', object)]))  # ground temperature of each surface
        mod_data_qh_ = np.zeros(numberOfVf, np.dtype(
            [('roof', '<f8'), ('road', '<f8'), ('watr', '<f8'), ('conc', '<f8'), ('Veg', '<f8'), ('dry', '<f8'),
             ('irr', '<f8'), ('wall', '<f8'), ('TSOIL', '<f8'), ('avg', '<f8'), ('date', object)]))  # sensible heat flux of each surface
        mod_data_qe_ = np.zeros(numberOfVf, np.dtype(
            [('roof', '<f8'), ('road', '<f8'), ('watr', '<f8'), ('conc', '<f8'), ('Veg', '<f8'), ('dry', '<f8'),
             ('irr', '<f8'), ('wall', '<f8'), ('TSOIL', '<f8'), ('avg', '<f8'), ('date', object)]))  # latent heat flux of each surface
        mod_data_qg_ = np.zeros(numberOfVf, np.dtype(
            [('roof', '<f8'), ('road', '<f8'), ('watr', '<f8'), ('conc', '<f8'), ('Veg', '<f8'), ('dry', '<f8'),
             ('irr', '<f8'), ('wall', '<f8'), ('TSOIL', '<f8'), ('avg', '<f8'), ('date', object)]))  # storage heat flux of each surface
        mod_data_rn_ = np.zeros(numberOfVf, np.dtype(
            [('roof', '<f8'), ('road', '<f8'), ('watr', '<f8'), ('conc', '<f8'), ('Veg', '<f8'), ('dry', '<f8'),
             ('irr', '<f8'), ('wall', '<f8'), ('TSOIL', '<f8'), ('avg', '<f8'), ('date', object)]))  # net radiation of each surface
        mod_data_kd_ = np.zeros(numberOfVf, np.dtype(
            [('roof', '<f8'), ('road', '<f8'), ('watr', '<f8'), ('conc', '<f8'), ('Veg', '<f8'), ('dry', '<f8'),
             ('irr', '<f8'), ('wall', '<f8'), ('TSOIL', '<f8'), ('avg', '<f8'), ('date', object)]))
        mod_data_ku_ = np.zeros(numberOfVf, np.dtype(
            [('roof', '<f8'), ('road', '<f8'), ('watr', '<f8'), ('conc', '<f8'), ('Veg', '<f8'), ('dry', '<f8'),
             ('irr', '<f8'), ('wall', '<f8'), ('TSOIL', '<f8'), ('avg', '<f8'), ('date', object)]))
        mod_data_ld_ = np.zeros(numberOfVf, np.dtype(
            [('roof', '<f8'), ('road', '<f8'), ('watr', '<f8'), ('conc', '<f8'), ('Veg', '<f8'), ('dry', '<f8'),
             ('irr', '<f8'), ('wall', '<f8'), ('TSOIL', '<f8'), ('avg', '<f8'), ('date', object)]))
        mod_data_lu_ = np.zeros(numberOfVf, np.dtype(
            [('roof', '<f8'), ('road', '<f8'), ('watr', '<f8'), ('conc', '<f8'), ('Veg', '<f8'), ('dry', '<f8'),
             ('irr', '<f8'), ('wall', '<f8'), ('TSOIL', '<f8'), ('avg', '<f8'), ('date', object)]))
        ## NB: "TSOIL" is the soil temperature below the water layer
        mod_rslts = np.zeros((self.nt, len(lc_data), 1), np.dtype(
            [('ID', np.int32), ('Ws', '<f8'), ('Ta', '<f8'), ('Ts_horz', '<f8'),
             ('Tac_can_roof', '<f8'), ('roofTsrfT', '<f8'), ('Tmrt', '<f8'), ('UTCI', '<f8'), ('UTCI_cat', '<f8'),
             ('httc_urb_new', '<f8'), ('Tb_rur', '<f8'), ('date', object)]))  # this is the main data array where surface averaged outputs are stored

        self.stations = lc_data['FID'].values

        mod_fm = np.zeros(self.nt)
        mod_cd = np.zeros(self.nt)
        mod_U_TaRef = np.zeros(self.nt)
        Tb_rur_prev = 0.0
        previousTacValues = []

        # begin looping through the met forcing data file
        for i in tqdm(range(0, len(met_data_all))):
            if i != len(met_data_all) - 1:
                ############ Met variables for each time step (generate dataframe) ##########
                dte = self.date1A
                dte = dte + timedelta(minutes=(i * int(self.tmstp)))  # current timestep
                self.Dats['dte'] = dte
                met_d = met_data_all

                ## BEGIN CALCULATION of Tb_rur
                ref_surf1 = 'dry'
                ref_surf2 = 'conc'

                # override these values if they are in the control file
                if 'ref_surf1' in self.cfM.keys():
                    ref_surf1 = self.cfM['ref_surf1']
                if 'ref_surf2' in self.cfM.keys():
                    ref_surf2 = self.cfM['ref_surf2']

                ## radiation balance
                prevTsRef1 = []
                prevTsRef2 = []

                if i < 1:
                    prevTsRef1.append(0)
                    prevTsRef1.append(0)
                    prevTsRef1.append(0)

                    prevTsRef2.append(0)
                    prevTsRef2.append(0)
                    prevTsRef2.append(0)
                elif i < 2:
                    prevTsRef1.append(mod_data_ts_[i - 1][9][ref_surf1])
                    prevTsRef1.append(0)
                    prevTsRef1.append(0)

                    prevTsRef2.append(mod_data_ts_[i - 1][9][ref_surf2])
                    prevTsRef2.append(0)
                    prevTsRef2.append(0)
                elif i < 3:
                    prevTsRef1.append(mod_data_ts_[i - 1][9][ref_surf1])
                    prevTsRef1.append(mod_data_ts_[i - 2][9][ref_surf1])
                    prevTsRef1.append(0)

                    prevTsRef2.append(mod_data_ts_[i - 1][9][ref_surf2])
                    prevTsRef2.append(mod_data_ts_[i - 2][9][ref_surf2])
                    prevTsRef2.append(0)
                else:
                    prevTsRef1.append(mod_data_ts_[i - 1][9][ref_surf1])
                    prevTsRef1.append(mod_data_ts_[i - 2][9][ref_surf1])
                    prevTsRef1.append(mod_data_ts_[i - 3][9][ref_surf1])

                    prevTsRef2.append(mod_data_ts_[i - 1][9][ref_surf2])
                    prevTsRef2.append(mod_data_ts_[i - 2][9][ref_surf2])
                    prevTsRef2.append(mod_data_ts_[i - 3][9][ref_surf2])

                rad_rur1 = rn_calc(self.parameters, met_d, ref_surf1, self.Dats, prevTsRef1, i, 1.0)
                rad_rur2 = rn_calc(self.parameters, met_d, ref_surf2, self.Dats, prevTsRef2, i, 1.0)
                #################ENG BALANCE for "reference" site ######################
                eng_bals_rur1 = LUMPS(rad_rur1, self.parameters, self.cfM, met_d, ref_surf1, self.Dats, i)
                eng_bals_rur2 = LUMPS(rad_rur2, self.parameters, self.cfM, met_d, ref_surf2, self.Dats, i)
                ################# CALC LST for "reference" site ########################
                prevTmRefForce1 = []
                prevTmRefForce2 = []
                if i < 1:
                    prevTmRefForce1.append(0)
                    prevTmRefForce2.append(0)
                else:
                    prevTmRefForce1.append(mod_data_tm_[i - 1][9][ref_surf1])
                    prevTmRefForce2.append(mod_data_tm_[i - 1][9][ref_surf2])
                Ts_stfs_rur1 = Ts_calc_surf(eng_bals_rur1, self.parameters, self.cfM, prevTsRef1, prevTmRefForce1,
                                            self.Dats, ref_surf1, i)
                Ts_stfs_rur2 = Ts_calc_surf(eng_bals_rur2, self.parameters, self.cfM, prevTsRef2, prevTmRefForce2,
                                            self.Dats, ref_surf2, i)
                # Ts_stfs_rur = Ts_stfs_rur1['TS']
                Ts_stfs_rur = Ts_stfs_rur2['TS']
                ### these are the parameters for calculating Tb_rur and httc_rur - may need to add a method for calculating these from
                #   Roughness length for momentum (m)
                if 'z0m_rur' in self.cfM.keys():
                    z0m_rur = self.cfM['z0m_rur']
                else:
                    z0m_rur = 0.45
                #   Roughness length for heat (m)
                z0h_rur = z0m_rur / 10

                # height of Tb (2 x max building height) - this is the secondary height used for Tb above canyon
                z_Hx2 = maxH * 2.0
                # height of air temperature measurements (usually 2 m)
                z_TaRef = self.parameters['z_TaRef']
                # override the value if it is in the control file
                if 'z_TaRef' in self.cfM.keys():
                    z_TaRef = self.cfM['z_TaRef']
                # height of reference wind speed measurement (usually 10 m)
                z_Uref = self.parameters['z_URef']
                # override the value if it is in the control file
                if 'z_URef' in self.cfM.keys():
                    z_Uref = self.cfM['z_URef']
                # surface temperature at rural (reference) site
                Tlow_surf = Ts_stfs_rur
                # observed air temperature
                ref_ta = met_d['Ta'][i]

                ####### DEFINE REFERENCE WIND SPEED RURAL ########
                uTopHeightMinimumValue = 0.1
                uTopHeight = max(met_d['WS'][i] * math.log(z_TaRef/z0m_rur)/math.log(z_Uref/z0m_rur), uTopHeightMinimumValue)
                mod_U_TaRef[i] = uTopHeight

                ###### calculate Richardson's number and heat transfer coefficient for rural site
                Ri_rur = sfc_ri(z_TaRef-z0m_rur, ref_ta, Tlow_surf, mod_U_TaRef[i])['Ri']

                httc_rural = httc(Ri_rur, mod_U_TaRef[i], z_TaRef-z0m_rur, z0m_rur, z0h_rur, met_d, i)
                httc_rur = httc_rural['httc']

                ###### sensible heat flux
                # Qh_ = httc_rur*(Tlow_surf-ref_ta)

                ###### calculate cd, fm, ustar used for calculating wind speed
                cd_out = cd(Ri_rur, z_TaRef-z0m_rur, z0m_rur, z0h_rur)
                mod_fm[i] = cd_out['Fm']
                mod_cd[i] = cd_out['cd_out']
                ustar = math.sqrt(mod_cd[i]) * max(mod_U_TaRef[i], 0.1)
                UTb = max(ustar / self.parameters['karman'] * math.log(z_Hx2 / z0m_rur) / math.sqrt(mod_fm[i]), 0.1)

                ###### Solve Richardson's number eq for "high temperature" aka Tb_rur
                dz = z_Hx2 - z_TaRef
                dz = max(dz, 0.01)

                Tb_rur = TbRurSolver.convergeNewVersion(dz, ref_ta, UTb, mod_U_TaRef, i, Ri_rur)
                # Tb_rur = TbRurSolver.pythonsolver(dz, ref_ta, UTb, mod_U_TaRef, i, Ri_rur)
                if Tb_rur == TbRurSolver.error_return or Tb_rur == 0.0:
                    print("Error with Tb_rur, returned value = " + str(Tb_rur))
                    print("Called with " + i + " " + dz + " " + ref_ta + " " + UTb + " " + mod_U_TaRef[i] + " " + Ri_rur)
                    Tb_rur = Tb_rur_prev
                    print('using previous Tb_rur = ' + str(Tb_rur_prev))

                Tb_rur = Tb_rur - 9.806 / 1004.67 * dz

                ######Begin calculating modelled variables for 10 different SVF values...
                vf = 0
                while vf < 10:
                    svfg = (vf + 1) / 10.0
                    for surf in self.surfs:
                        if surf != 'watr' and surf != 'Veg':
                            prevTsRef = []
                            if i < 1:
                                prevTsRef.append(0)
                                prevTsRef.append(0)
                                prevTsRef.append(0)
                            elif i < 2:
                                prevTsRef.append(mod_data_ts_[i - 1][vf][surf])
                                prevTsRef.append(0)
                                prevTsRef.append(0)
                            elif i < 3:
                                prevTsRef.append(mod_data_ts_[i - 1][vf][surf])
                                prevTsRef.append(mod_data_ts_[i - 2][vf][surf])
                                prevTsRef.append(0)
                            else:
                                prevTsRef.append(mod_data_ts_[i - 1][vf][surf])
                                prevTsRef.append(mod_data_ts_[i - 2][vf][surf])
                                prevTsRef.append(mod_data_ts_[i - 3][vf][surf])
                            prevTmRefForce = []
                            if i < 1:
                                prevTmRefForce.append(0)
                            else:
                                prevTmRefForce.append(mod_data_tm_[i - 1][9][surf])

                            rad = rn_calc(self.parameters, met_d, surf, self.Dats, prevTsRef, i, svfg)
                            eng_bals = LUMPS(rad, self.parameters, self.cfM, met_d, surf, self.Dats, i)
                            Ts_stfs = Ts_calc_surf(eng_bals, self.parameters, self.cfM, prevTsRef, prevTmRefForce,
                                                   self.Dats, surf, i)

                            mod_data_ts_[i][vf][surf] = Ts_stfs['TS']
                            mod_data_tm_[i][vf][surf] = Ts_stfs['TM']
                            mod_data_qh_[vf][surf] = eng_bals['Qh']
                            mod_data_qe_[vf][surf] = eng_bals['Qe']
                            mod_data_qg_[vf][surf] = eng_bals['Qg']
                            mod_data_rn_[vf][surf] = rad['Rn']
                            # mod_data_kd_[vf][surf] = rad['Kd']
                            # mod_data_ku_[vf][surf] = rad['Ku']
                            # mod_data_ld_[vf][surf] = rad['Ld']
                            # mod_data_lu_[vf][surf] = rad['Lu']

                            # if surf == 'irr':
                            #     print("Qh ", eng_bals['Qh'])
                            #     print("Qe ", eng_bals['Qe'])
                            #     print("Qg ", eng_bals['Qg'])

                        if surf == 'watr':
                            prevTsRef = []
                            if i < 1:
                                prevTsRef.append(0)
                                prevTsRef.append(0)
                                prevTsRef.append(0)
                            elif i < 2:
                                prevTsRef.append(mod_data_ts_[i - 1][9][surf])
                                prevTsRef.append(0)
                                prevTsRef.append(0)
                            elif i < 3:
                                prevTsRef.append(mod_data_ts_[i - 1][9][surf])
                                prevTsRef.append(mod_data_ts_[i - 2][9][surf])
                                prevTsRef.append(0)
                            else:
                                prevTsRef.append(mod_data_ts_[i - 1][9][surf])
                                prevTsRef.append(mod_data_ts_[i - 2][9][surf])
                                prevTsRef.append(mod_data_ts_[i - 3][9][surf])

                            rad = rn_calc(self.parameters, met_d, surf, self.Dats, prevTsRef, i, svfg)
                            wtr_stf = Ts_EB_W(met_d, self.parameters, self.cfM, mod_data_ts_, mod_data_tm_, self.Dats,
                                              i, rad, vf)

                            mod_data_ts_[i][vf][surf] = wtr_stf['TsW']
                            mod_data_tm_[i][vf][surf] = wtr_stf['TM']
                            mod_data_ts_[i][vf]['TSOIL'] = wtr_stf['TSOIL']
                            mod_data_qh_[vf][surf] = wtr_stf['QhW']
                            mod_data_qe_[vf][surf] = wtr_stf['QeW']
                            mod_data_qg_[vf][surf] = wtr_stf['QgW']
                            mod_data_rn_[vf][surf] = rad['Rn']
                            # mod_data_kd_[vf][surf] = rad['Kd']
                            # mod_data_ku_[vf][surf] = rad['Ku']
                            # mod_data_ld_[vf][surf] = rad['Ld']
                            # mod_data_lu_[vf][surf] = rad['Lu']

                    vf += 1

                timestepsTacValues = []

                for grid in range(0, len(lc_data)):  # now cycle through each grid point
                    # counter += 1
                    ##################### CALC air temperature ########################
                    ta_rslts = calc_ta(self.parameters, self.cfM, lc_data, grid, i, met_d, z_Uref, z_Hx2, Tb_rur, mod_data_ts_,
                                       previousTacValues, httc_rur)  # dictionary for canopy air temperature and wind speed

                    # calculate UTCI
                    lat = self.latEdge

                    yd_actual = dte.day
                    TM = dte.hour

                    Tac = ta_rslts['Tac']
                    if Tac == -999.0:
                        tmrt = -999.0
                        utci = {'utci': -999.0, 'cat': -999}
                    else:
                        lup = self.parameters['sb'] * ((met_d['Ta'][i] + 273.15) ** 4)

                        tmrt = UTCI.getTmrtForGrid_RH(Tac, met_d['RH'][i], ta_rslts['Ucan'], met_d['Kd'][i],
                                                      ta_rslts['Ts_can'], met_d['Ld'][i], lup, yd_actual, TM,
                                                      lat)
                        utci = UTCI.getUTCIForGrid_RH(Tac, ta_rslts['Ucan'], met_d['RH'][i], tmrt)

                    ############################ append everyhing to output table #####
                    for_tab = (lc_data.loc[grid]['FID'], ta_rslts['Ucan'], ta_rslts['Tac'],
                               ta_rslts['Ts_horz'], ta_rslts['Tac_can_roof'], ta_rslts['roofTsrfT'],
                               tmrt, utci['utci'], utci['cat'], ta_rslts['httc_urb_new'], Tb_rur, dte)

                    ############################ append everyhing to output table #####
                    # for_tab = (lc_data.loc[grid]['FID'], ta_rslts['Ucan'], Tb_rur, ta_rslts['Tac'],
                    #            ta_rslts['Ts_horz'], ta_rslts['Tac_can_roof'], ta_rslts['roofTsrfT'],
                    #            ta_rslts['Tacprv'], ta_rslts['Tcorrhi'], ta_rslts['httc_urb_new'],
                    #            ta_rslts['Fh'], ta_rslts['httc_can'],ta_rslts['Twall'], dte)

                    mod_rslts[i][grid] = for_tab  ## append the main data to the main modelled data frame
                    timestepsTacValues.append(float(ta_rslts['Tac']))

            previousTacValues.append(timestepsTacValues)
        ##########################################################################################
        self.mod_rslts = mod_rslts[1:]  ### THIS IS THE FINAL DATA ARRAY WITH MODEL OUTPUTS  ######
        ##########################################################################################
        ## defines a director for outputing plot
        if not os.path.exists(self.OUT_DIR):
            os.makedirs(self.OUT_DIR)

        ### saves the output array as a numpy array can load with numpy.load
        np.save(os.path.join(self.OUT_DIR, self.run),
                mod_rslts)

        np.set_printoptions(threshold=sys.maxsize)

        if save_csv:
            LOG.info("converting results to csv")
            npy_to_csv(os.path.join(self.OUT_DIR, self.run + ".npy"), self.progress)

    def __init_validation(self):

        if not self.__validated:
            ######### Create a dir for figures ###########################
            self.FIG_DIR = os.path.join(self.cfM['work_dir'], self.cfM['site_name'], 'plots', self.run)
            if not os.path.exists(self.FIG_DIR):
                ## defines a director for outputing plots | only gets used if validating air temp (plotting.py)
                os.makedirs(self.FIG_DIR)

            self.OBS_FILE = os.path.join(self.cfM['work_dir'], self.cfM['site_name'], 'obs', 'stations_MET',
                                         self.cfM['inpt_obs_file'])
            ############## OBS AWS DATA files  #############################
            # file for observed AWS data
            # reads observed AWS data and puts in dataframe  | only gets used if validating air temp (plotting.py)
            self.obs_data = pd.read_csv(self.OBS_FILE, parse_dates=['TIMESTAMP'], date_parser=self.dateparse,
                                        index_col=['TIMESTAMP'])

            self.__validated = True

    def plot_val_ts(self):
        self.__init_validation()
        LOG.info("plotting val_ts")
        val_ts(self.cfM, self.stations, self.mod_rslts, self.progress)

    def plot_val_ta(self):
        self.__init_validation()
        LOG.info("plotting val_ta")
        val_ta(self.cfM, self.met_data, self.stations, self.obs_data, self.mod_rslts, self.Dats, self.progress)

    def plot_gis(self):
        self.__init_validation()
        LOG.info("plotting gis")
        gis(self.cfM, self.mod_rslts, self.run)

    def save_simulation_parameters(self):

        if not os.path.exists(self.SETTINGS_DIR):
            os.mkdir(self.SETTINGS_DIR)
        LOG.info("saving simulation parameters")

        ## save the control file....
        with open(self.control_file_name, 'r') as inp:
            with open(os.path.join(self.SETTINGS_DIR, 'config_{}.ini'.format(self.cfM['run_name'])), 'w+') as outp:
                outp.write(inp.read())

        ## save the constants file..
        with open(self.cfM['para_json_path'], 'r') as inp:
            with open(os.path.join(self.SETTINGS_DIR, 'parameters_{}.json'.format(self.cfM['run_name'])), 'w+') as outp:
                outp.write(inp.read())
