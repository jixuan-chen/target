import os
import zipfile

__conf_str_inp = """
[DEFAULT]

#---------------------------------------------------------------------------------------------------------
####### Example Control File #######
#---------------------------------------------------------------------------------------------------------
####### INPUTS #######
#output path
work_dir={work_dir}
#parameters json file
para_json_path={parameter_dir}
# site name (string)
site_name={site_name}
# run name (string)
run_name ={run_name}
# input meteorolgical file (i.e. forcing file)
inpt_met_file={met_file_name}
#  input land cover data file
inpt_lc_file={lc_file_name}
# format of datetime in input met files
date_fmt=%Y-%m-%d %H:%M:%S
# time step (minutes)
timestep=15

mod_ldwn=N
domainDim=32,31
latEdge=47.3769
lonEdge=8.5417
latResolution=0.00090933
lonResolution=0.00130123

#---------------------------------------------------------------------------------------------------------
# dates
#---------------------------------------------------------------------------------------------------------
# year,month,day,hour	#start date for simulation (should be a minimum of 24 hours prior to date1)
#date1a=2017,6,20,0
date1a=2023,7,8,0
# year,month,day,hour	## the date/time for period of interest (i.e. before this will not be saved)
#date1=2017,6,21,0
date1=2023,7,9,0
# year,month,day,hour	# end date for validation period
#date2=2017,6,22,0
date2=2023,7,12,0
######################
"""

__conf_str_obs = """
##### Validation Info ####
## observed AWS data (for validation)
inpt_obs_file =   30min_no_grid_obs.csv

radius=25m
 # year,month,day,hour # start date/time for obs Ts data (AWS)
date1Ts1=2017,6,20,0
# year,month,day,hour # end   date/time for obs Ts data (AWS)
date1Ts2=2017,6,21,0
# year,month,day,hour # start date/time for obs Ts data (AWS) 
date2Ts1=2017,2,15,2
# year,month,day,hour # end   date/time for obs Ts data (AWS)
date2Ts2=2011,2,15,3
# names for Ts test periods
Ts_prd1 = day
 # names for Ts test periods
Ts_prd2 = night

STa = '01','02','03','04','05','06','07','08','09','10','11','12','13','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30'
########################
"""

__para_str = """   
{
    "res":{
        "value": 100,
        "comment": "resolution"
    },
    "karman": {
        "value": 0.4,
        "comment": "von Karman constant"
    },
    "sb": {
        "value": 5.67e-08,
        "comment": "Stefan-Boltzman constant, W/m2/K4"
    },
    "alb": {
        "value": {
            "roof": 0.15,
            "wall": 0.15,
            "road": 0.08,
            "watr": 0.10,
            "conc": 0.20,
            "Veg": 0.10,
            "dry": 0.19,
            "irr": 0.19
        },
        "comment": "albedos"
    },
    "emis": {
        "value": {
            "roof": 0.9,
            "wall": 0.9,
            "road": 0.95,
            "watr": 0.97,
            "conc": 0.94,
            "Veg": 0.98,
            "dry": 0.98,
            "irr": 0.98
        },
        "comment": "emissivities"
    },
    "rs": {
        "value": {
            "roof": -999.0,
            "wall": -999.0,
            "road": -999.0,
            "watr": 0.0,
            "conc": -999.0,
            "Veg": 40.0,
            "dry": -999.0,
            "irr": 40.0
        },
        "comment": "stomatal resistances"
    },
    "C": {
        "value": {
            "roof": 1250000.0,
            "wall": 1250000.0,
            "road": 1940000.0,
            "watr": 4180000.0,
            "conc": 2110000.0,
            "dry": 1350000.0,
            "irr": 2190000.0,
            "soilW": 3030000.0
        },
        "comment": "heat capacity  (J m^-3 K^-1)"
    },
    "K": {
        "value": {
            "roof": 0.00000005,
            "wall": 0.00000005,
            "road": 0.00000038,
            "watr": 0.00000014,
            "conc": 0.00000072,
            "dry": 0.00000021,
            "irr": 0.00000042,
            "soilW": 0.00000063
        },
        "comment": "thermal diffusivity (m^2 s^-1)"
    },
    "Tm": {
        "value": {
            "roof": 25.0,
            "wall": 25.0,
            "road": 26.0,
            "watr": 24.5,
            "conc": 26.0,
            "dry": 22.4,
            "irr": 21.5
        },
        "comment": "Tm intial conditions [SPIN2 - good]"
    },
    "Ts": {
        "value": {
            "roof": 20.0,
            "wall": 20.0,
            "road": 20.0,
            "watr": 20.0,
            "conc": 20.0,
            "dry": 20.0,
            "irr": 20.0
        },
        "comment": "Ts intial conditions [BASE]"
    },
    "dW": {
        "value": "formula_math.sqrt(2*$K_soilW/(2*math.pi / 86400))",
        "comment": ""
    },
    "ww": {
        "value": "formula_(2*math.pi / 86400)",
        "comment": ""
    },
    "Kw": {
        "value": 6.18e-07,
        "comment": "eddy diffusivity of water (m^2 s^-1) - [used for the water Ts part.]"
    },
    "cp": {
        "value": 0.001013,
        "comment": "specific heat of air (J / kg C)"
    },
    "e": {
        "value": 0.622,
        "comment": "Unitless - ratio of molecular weight of water to dry air"
    },
    "pa": {
        "value": 1.2,
        "comment": "density of dry air (1.2 kg m-3)"
    },
    "cpair": {
        "value": 1004.67,
        "comment": "heat cpacity of air"
    },
    "hv": {
        "value": 0.0014,
        "comment": "bulk transfer coefficient for water energy balance modelled"
    },
    "betaW": {
        "value": 0.45,
        "comment": "amount of radiation immediately absorbed by the first layer of water (set to 0.45) (martinez et al., 2006)."
    },
    "zW": {
        "value": 0.3,
        "comment": "depth of the water layer (m)"
    },
    "NW": {
        "value": "formula_(1.1925*$zW**(-0.424))",
        "comment": "extinction coefficient after Subin et al., (2012)"
    },
    "Lv": {
        "value": 2430000.0,
        "comment": "the latent heat of vaporisation (MJ Kg^-1)"
    },
    "z_TaRef": {
        "value": 2.0,
        "comment": "BOM reference height"
    },
    "z_URef": {
        "value": 28.05,
        "comment": "BOM reference height"
    },
    "z0m": {
        "value": 1.0,
        "comment": "roughness length, used in new Ta module."
    },
    "zavg": {
        "value": 10.7296,
        "comment": "average building height in domain"
    },
    "LUMPS1": {
        "value": {
            "roof": [
                0.12,
                0.24,
                -4.5
            ],
            "wall": [
                0.12,
                0.24,
                -4.5
            ],
            "road": [
                0.50,
                0.28,
                -31.45
            ],
            "conc": [
                0.61,
                0.28,
                -23.9
            ],
            "Veg": [
                0.11,
                0.11,
                -12.3
            ],
            "dry": [
                0.27,
                0.33,
                -21.75
            ],
            "irr": [
                0.32,
                0.54,
                -27.4
            ]
        },
        "comment": ""
    },
    "alphapm": {
        "value": {
            "roof": 0.0,
            "wall": 0.0,
            "road": 0.0,
            "conc": 0.0,
            "Veg": 1.2,
            "dry": 0.2,
            "irr": 1.2
        },
        "comment": ""
    },
    "beta": {
        "value": {
            "roof": 3.0,
            "wall": 3.0,
            "road": 3.0,
            "conc": 3.0,
            "Veg": 3.0,
            "dry": 3.0,
            "irr": 3.0
        },
        "comment": ""
    }
}
"""


def gen_conf_inp(path, site_name, run_name, met_file_name, lc_file_name):
    global __conf_str_inp

    conf = __conf_str_inp.format(
        work_dir=os.path.split(path)[0],
        parameter_dir=os.path.join(path, "parameters.json"),
        site_name=site_name,
        run_name=run_name,
        met_file_name=met_file_name,
        lc_file_name=lc_file_name
    )

    return conf

def gen_conf_obs():
    global __conf_str_obs
    return __conf_str_obs

def write_conf(path, conf):
    with open(os.path.join(path, "config.ini"), "w+") as f:
        f.write(
            conf
        )

def write_para(path):
    global __para_str
    with open(os.path.join(path, "parameters.json"), "w+") as f:
        f.write(
            __para_str
        )
    return


def gen_struct_inp(path):

    inp_folder = os.path.join(path, "input")
    if not os.path.exists(inp_folder):
        os.mkdir(inp_folder)

    met_folder = os.path.join(inp_folder, "MET")
    if not os.path.exists(met_folder):
        os.mkdir(met_folder)

    lc_folder = os.path.join(inp_folder, "LC")
    if not os.path.exists(lc_folder):
        os.mkdir(lc_folder)

def gen_struct_outp(path, grid):

    inp_folder = os.path.join(path, "obs")
    if not os.path.exists(inp_folder):
        os.mkdir(inp_folder)

    if grid:
        met_folder = os.path.join(inp_folder, "stations_MET")
        if not os.path.exists(met_folder):
            os.mkdir(met_folder)

        lst_folder = os.path.join(inp_folder, "stations_LST")
        if not os.path.exists(lst_folder):
            os.mkdir(lst_folder)
    else:
        met_folder = os.path.join(inp_folder, "stations_MET")
        if not os.path.exists(met_folder):
            os.mkdir(met_folder)

        lst_folder = os.path.join(inp_folder, "stations_LST")
        if not os.path.exists(lst_folder):
            os.mkdir(lst_folder)


def gen_data(path, met_file_name, lc_file_name, grid):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, "data", "30min_no_grid_met.csv"), 'rb') as met_data:
        with open(os.path.join(path, "input", "MET", met_file_name), "wb+") as met:
            met.write(met_data.read())

    if grid:
        source_lc = "30m_grid_lc.csv"
    else:
        source_lc = "25m-no_grid_lc.csv"

    with open(os.path.join(dir_path, "data", source_lc), 'rb') as met_data:
        with open(os.path.join(path, "input", "LC", lc_file_name), "wb+") as met:
            met.write(met_data.read())



def gen_obs(path, grid):
    dir_path = os.path.dirname(os.path.realpath(__file__))

    if grid:
        with zipfile.ZipFile(os.path.join(dir_path, "data", "stations_LST.zip"), 'r') as zip_ref:
            zip_ref.extractall(os.path.join(path, "obs", "stations_LST"))

        with open(os.path.join(dir_path, "data", "30min_no_grid_obs.csv"), 'rb') as met_data:
            with open(os.path.join(path, "obs", "stations_MET", "30min_no_grid_obs.csv"), "wb+") as met:
                met.write(met_data.read())
    else:

        with zipfile.ZipFile(os.path.join(dir_path, "data", "stations_LST.zip"), 'r') as zip_ref:
            zip_ref.extractall(os.path.join(path, "obs", "stations_LST"))

        with open(os.path.join(dir_path, "data", "30min_no_grid_obs.csv"), 'rb') as met_data:
            with open(os.path.join(path, "obs", "stations_MET", "30min_no_grid_obs.csv"), "wb+") as met:
                met.write(met_data.read())


def generate_example(
        path,
        site_name=None,
        run_name=None,
        obs=False,
        grid=False,
        empty=False
):

    if empty and obs:
        raise ValueError("obs and empty cannot be used together.")

    if grid:
        lc_name = "30m_grid_lc.csv"
    else:
        lc_name = "25m-no_grid_lc.csv"

    met_name = "30min_no_grid_met.csv"

    if run_name is None:
        run_name = "run_name"

    if site_name is None:
        site_name = "site_name"

    full_path = os.path.join(path, site_name)

    if not os.path.exists(full_path):
        os.mkdir(full_path)

    gen_struct_inp(full_path)

    if empty:

        conf = gen_conf_inp(
            full_path,
            site_name=site_name,
            run_name=run_name,
            lc_file_name="InnerZurich_LC_test.csv",
            met_file_name="SMA_2023_15min.csv"
        )

        write_conf(
            full_path,
            conf
        )

        write_para(
            full_path
        )

    else:

        gen_data(
            full_path,
            lc_file_name=lc_name,
            met_file_name=met_name,
            grid=grid
        )

        conf = gen_conf_inp(
            full_path,
            site_name=site_name,
            run_name=run_name,
            lc_file_name=lc_name,
            met_file_name=met_name
        )

        if obs:
            gen_struct_outp(
                full_path,
                grid
            )

            gen_obs(
                full_path,
                grid=grid
            )

            conf_obs = gen_conf_obs()
            conf += conf_obs

        write_conf(
            full_path,
            conf
        )

        write_para(
            full_path
        )

    return


