# -*- coding: utf-8 -*-
"""
calculates canyon air temperature (Tac)

see section 3.5 tech notes for details

inputs:
    H           = average building height
    W           = average street width
    qH          = average sensible heat flux
    Tsurf       = average surface temperature
    cs          = constants dictionary
    cfM         = main control file
    Dats        = dates dictionary
    obs         = observed wind speed
    i           = current index


Outputs:
    Ta_f = canyon air temperature (Tac)
    Tb   = air temperature above the canyon (Tb)
    ra   = resistance between the canyon and atmopshere
    Ucan = canyon wind speed
"""

import math
from target.scripts.LcSort import lc_sort
from target.scripts.SfcRi import sfc_ri
from target.scripts.Httc import httc
import numpy as np


def calc_ta(cs, cfM, lc_data, grid, i, met_d, z_URef, z_Hx2, Tb_rur, mod_data_ts_, mod_rslts_prev, httc_rur):
    metTa0 = met_d['Ta'][i]
    metWS0 = met_d['WS'][i]
    H = lc_data['H'][grid]
    W = lc_data['W'][grid]

    LC = [lc_data['roof'][grid], lc_data['road'][grid], lc_data['watr'][grid], lc_data['conc'][grid],
          lc_data['Veg'][grid], lc_data['dry'][grid], lc_data['irr'][grid]]

    lc_stuff = lc_sort(cs, LC, H, W)

    # define surface temperature of trees as canyon air temperature
    if i == 0 or mod_rslts_prev[i - 1][grid] == -999.0:
        mod_data_ts_[i][9]['Veg'] = metTa0
    else:
        mod_data_ts_[i][9]['Veg'] = mod_rslts_prev[i - 1][grid]
    LC = lc_stuff['LC']
    LC_wRoofAvg = lc_stuff['LC_wRoofAvg']

    fw = lc_stuff['fw']
    fg = lc_stuff['fg']

    zavg = cs['zavg']
    if "zavg" in cfM.keys():
        zavg = float(cfM['zavg'])
    Hz = max(H, zavg)

    z0m_urb = 0.1 * Hz
    z0h_urb = z0m_urb / 10.0

    Uz = max(metWS0 * (math.log(Hz / z0m_urb) / math.log(z_URef / z0m_urb)), 0.1)

    lcStuffWTree = lc_stuff['Wtree']
    Ucan = Uz * math.exp(-0.386 * (Hz / lcStuffWTree))

    rs_can = cs['pa'] * cs['cpair'] / (11.8 + 4.2 * Ucan)
    httc_can = 1.0 / rs_can

    roofIndex = 0
    roadIndex = 1
    wallIndex = 7
    dryIndex = 5
    concIndex = 3
    VegIndex = 4
    irrIndex = 6
    watrIndex = 2

    LCroof = LC[roofIndex]
    LCcan = LC[roadIndex] + LC[watrIndex] + LC[concIndex] + LC[VegIndex] + LC[dryIndex] + LC[irrIndex]
    # LCcan = lc_data['road'][grid] + lc_data['watr'][grid] + lc_data['conc'][grid] + lc_data['Veg'][grid] + \
    #         lc_data['dry'][grid] + lc_data['irr'][grid]
    LChorz = LCroof + LCcan
    PlanCan = LCcan / LChorz

    if i != 0 and mod_rslts_prev[i - 1][grid] != -999.0:
        Tacprv = mod_rslts_prev[i - 1][grid]
        roofTsrfT = mod_data_ts_[i - 1][9]['roof']
    else:
        Tacprv = metTa0
        roofTsrfT = metTa0

    Tac_can_roof = (LCroof / LChorz) * roofTsrfT + (LCcan / LChorz) * Tacprv
    z_Hx2 = Hz * 2
    dz = z_Hx2 - H - z0m_urb
    # Uz = max(metWS0 * (math.log(z_Hx2 / z0m_urb) / math.log(z_URef / z0m_urb)), 0.1)
    Ri_return = sfc_ri(dz, Tb_rur, Tac_can_roof, Uz)
    Ri_urb_new = Ri_return['Ri']
    httcReturn = httc(Ri_urb_new, Uz, dz, z0m_urb, z0h_urb, met_d, i)
    httc_urb_new = httcReturn['httc']

    Tsurf_can = (mod_data_ts_[i][9]['roof'] * LC[roofIndex] +
                 mod_data_ts_[i][fg]['conc'] * LC[concIndex] +
                 mod_data_ts_[i][fg]['road'] * LC[roadIndex] +
                 mod_data_ts_[i][fg]['watr'] * LC[watrIndex] +
                 mod_data_ts_[i][fg]['dry'] * LC[dryIndex] +
                 mod_data_ts_[i][fg]['irr'] * LC[irrIndex] +
                 mod_data_ts_[i][fw]['wall'] * LC[wallIndex] +
                 mod_data_ts_[i][9]['Veg'] * LC[VegIndex])

    LcH = LC_wRoofAvg

    Tsurf_horz = (mod_data_ts_[i][9]['roof'] * LcH[roofIndex] +
                  mod_data_ts_[i][fg]['conc'] * LcH[concIndex] +
                  mod_data_ts_[i][fg]['road'] * LcH[roadIndex] +
                  mod_data_ts_[i][fg]['watr'] * LcH[watrIndex] +
                  mod_data_ts_[i][fg]['dry'] * LcH[dryIndex] +
                  mod_data_ts_[i][fg]['irr'] * LcH[irrIndex] +
                  mod_data_ts_[i][9]['Veg'] * LcH[VegIndex])

    Tsurf_wall = mod_data_ts_[i][fw]['wall']

    if cfM['include roofs'] == "Y":
        Tac = (mod_data_ts_[i][fg]['conc'] * httc_can * LC[concIndex] +
               mod_data_ts_[i][9]['roof'] / (1 / httc_can + 1 / httc_urb_new) * LC[roofIndex]
               + mod_data_ts_[i][fg]['road'] * httc_can * LC[roadIndex]
               + mod_data_ts_[i][fg]['watr'] * httc_can * LC[watrIndex]
               + mod_data_ts_[i][fg]['dry'] * httc_can * LC[dryIndex]
               + mod_data_ts_[i][fg]['irr'] * httc_can * LC[irrIndex]
               + mod_data_ts_[i][fw]['wall'] * httc_can * LC[wallIndex]
               + mod_data_ts_[i][9]['Veg'] * httc_can * LC[VegIndex]
               + (Tb_rur * httc_urb_new * PlanCan)) / (
                      httc_can * LC[concIndex] + LC[roofIndex] / (1 / httc_can + 1 / httc_urb_new)
                      + httc_can * LC[roadIndex] + httc_can * LC[watrIndex] + httc_can * LC[dryIndex]
                      + httc_can * LC[irrIndex] + httc_can * LC[wallIndex] + httc_can * LC[VegIndex]
                      + httc_urb_new * PlanCan)
    else:
        Tac = (mod_data_ts_[i][fg]['conc'] * httc_can * LC[concIndex]
               + mod_data_ts_[i][fg]['road'] * httc_can * LC[roadIndex]
               + mod_data_ts_[i][fg]['watr'] * httc_can * LC[watrIndex]
               + mod_data_ts_[i][fg]['dry'] * httc_can * LC[dryIndex]
               + mod_data_ts_[i][fg]['irr'] * httc_can * LC[irrIndex]
               + mod_data_ts_[i][fw]['wall'] * httc_can * LC[wallIndex]
               + mod_data_ts_[i][9]['Veg'] * httc_can * LC[VegIndex]
               + Tb_rur * httc_rur * PlanCan) / (
                      httc_can * LC[concIndex] + httc_can * LC[roadIndex] + httc_can * LC[watrIndex]
                      + httc_can * LC[dryIndex] + httc_can * LC[irrIndex] + httc_can * LC[wallIndex]
                      + httc_can * LC[VegIndex] + httc_rur * PlanCan)

    if LC[roofIndex] > 0.75:
        Tac = -999.0
        Tsurf_horz = mod_data_ts_[i][9]['roof'] * LcH[roofIndex]

    return {'Ucan': Ucan, 'Ts_horz': Tsurf_horz, 'Ts_can': Tsurf_can, 'Ts_wall': Tsurf_wall, 'Tac': Tac,
            'Tac_can_roof': Tac_can_roof, 'roofTsrfT': roofTsrfT, 'Tacprv': Tacprv, 'Tcorrhi': Ri_return['Tcorrhi'],
            'httc_urb_new': httc_urb_new, 'Fh': httcReturn['Fh'], 'httc_can': httc_can, 'Twall': Tsurf_wall, 'fg': fg,
            'fw': fw}

