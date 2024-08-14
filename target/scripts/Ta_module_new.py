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


def calc_ta(cs, lc_data, grid, i, met_d, z_URef, z_Hx2, Tb_rur, mod_data_ts_, mod_rslts_prev, httc_rur):
    skipTa = False
    metTa0 = met_d['Ta'][i]
    metWS0 = met_d['WS'][i]
    H = lc_data['H'][grid]
    W = cs['res'] * (1 - lc_data['roof'][grid])

    if i == 0 or mod_rslts_prev[i - 1][grid] == -999.0:
        mod_data_ts_[i][9]['Veg'] = metTa0
    else:
        mod_data_ts_[i][9]['Veg'] = mod_rslts_prev[i - 1][grid]

    LC = [lc_data['roof'][grid], lc_data['road'][grid], lc_data['watr'][grid], lc_data['conc'][grid],
          lc_data['Veg'][grid], lc_data['dry'][grid], lc_data['irr'][grid]]

    # if max(LC) > 0.5:
    #     skipTa = True

    lc_stuff = lc_sort(cs, LC, H, W)

    LC = lc_stuff['LC']
    LC_wRoofAvg = lc_stuff['LC_wRoofAvg']
    H = lc_stuff['H']

    fw = lc_stuff['fw']
    fg = lc_stuff['fg']

    Hz = max(H, cs['zavg'])
    z0m_urb = 0.1 * Hz
    z0h_urb = z0m_urb/10.0

    Uz = max(metWS0 * math.log(Hz/z0m_urb)/math.log(z_URef/z0m_urb), 0.1)
    lcStuffWTree = lc_stuff['Wtree']
    Ucan = Uz * math.exp(-0.386 * (Hz/lcStuffWTree))
    rs_can = cs['pa'] * cs['cpair'] / (11.8 + 4.2 * Ucan)
    httc_can = 1.0 / rs_can

    LCroof = LC[0]
    LCcan = LC[1] + LC[2] + LC[3] + LC[4] + LC[5] + LC[6]
    LChorz = LCroof + LCcan
    PlanCan = LCcan/LChorz

    roofIndex = 0
    roadIndex = 1
    wallIndex = 7
    dryIndex = 5
    concIndex = 3
    VegIndex = 4
    irrIndex = 6
    watrIndex = 2

    if i != 0 and mod_rslts_prev[i-1][grid] != -999.0:
        Tacprv = mod_rslts_prev[i-1][grid]
        roofTsrfT = mod_data_ts_[i-1][9][roofIndex]

    else:
        Tacprv = metTa0
        roofTsrfT = metTa0

    Tac_can_roof = (LCroof/LChorz)*roofTsrfT + (LCcan/LChorz)*Tacprv
    Ri_return = sfc_ri(z_Hx2-H-z0m_urb, Tb_rur, Tac_can_roof, Uz)
    Ri_urb_new = Ri_return['Ri']
    httcReturn = httc(Ri_urb_new, Uz, z_Hx2-H-z0m_urb, z0m_urb, z0h_urb, met_d, i)
    httc_urb_new = httcReturn['httc']

    Tsurf_can = mod_data_ts_[i][9][roofIndex]*LC[roofIndex] + mod_data_ts_[i][fg][concIndex]*LC[concIndex] \
                + mod_data_ts_[i][fg][roadIndex]*LC[roadIndex] + mod_data_ts_[i][fg][watrIndex]*LC[watrIndex] \
                + mod_data_ts_[i][fg][dryIndex]*LC[dryIndex] + mod_data_ts_[i][fg][irrIndex]*LC[irrIndex] \
                + mod_data_ts_[i][fw][wallIndex]*LC[wallIndex] + mod_data_ts_[i][9][VegIndex]*LC[VegIndex]

    LcH = LC_wRoofAvg[:]
    Tsurf_horz = mod_data_ts_[i][9][roofIndex]*LcH[roofIndex] + mod_data_ts_[i][fg][concIndex]*LcH[concIndex] \
                + mod_data_ts_[i][fg][roadIndex]*LcH[roadIndex] + mod_data_ts_[i][fg][watrIndex]*LcH[watrIndex] \
                + mod_data_ts_[i][fg][dryIndex]*LcH[dryIndex] + mod_data_ts_[i][fg][irrIndex]*LcH[irrIndex] \
                + mod_data_ts_[i][9][VegIndex]*LcH[VegIndex]


    Tsurf_wall = mod_data_ts_[i][fw][wallIndex]

    includeRoofs = True

    if includeRoofs:
        Tac = (mod_data_ts_[i][fg][concIndex]*httc_can*LC[concIndex]
               + mod_data_ts_[i][9][roofIndex]/(1/httc_can+1/httc_urb_new)*LC[roofIndex]
               + mod_data_ts_[i][fg][roadIndex]*httc_can*LC[roadIndex]
               + mod_data_ts_[i][fg][watrIndex]*httc_can*LC[watrIndex]
               + mod_data_ts_[i][fg][dryIndex]*httc_can*LC[dryIndex]
               + mod_data_ts_[i][fg][irrIndex]*httc_can*LC[irrIndex]
               + mod_data_ts_[i][fw][wallIndex]*httc_can*LC[wallIndex]
               + mod_data_ts_[i][9][VegIndex]*httc_can*LC[VegIndex]
               + (Tb_rur*httc_urb_new*PlanCan)) / (httc_can*LC[concIndex] + LC[roofIndex]/(1/httc_can+1/httc_urb_new)
                                                  + httc_can*LC[roadIndex] + httc_can*LC[watrIndex] + httc_can*LC[dryIndex]
                                                  + httc_can*LC[irrIndex] + httc_can*LC[wallIndex] + httc_can*LC[VegIndex]
                                                  + httc_urb_new*PlanCan)
    else:
        Tac = (mod_data_ts_[i][fg][concIndex]*httc_can*LC[concIndex]
               + mod_data_ts_[i][fg][roadIndex]*httc_can*LC[roadIndex]
               + mod_data_ts_[i][fg][watrIndex]*httc_can*LC[watrIndex]
               + mod_data_ts_[i][fg][dryIndex]*httc_can*LC[dryIndex]
               + mod_data_ts_[i][fg][irrIndex]*httc_can*LC[irrIndex]
               + mod_data_ts_[i][fw][wallIndex]*httc_can*LC[wallIndex]
               + mod_data_ts_[i][9][VegIndex]*httc_can*LC[VegIndex]
               + Tb_rur*httc_rur*PlanCan)/(httc_can*LC[concIndex] + httc_can*LC[roadIndex] + httc_can*LC[watrIndex]
                                           + httc_can*LC[dryIndex] + httc_can*LC[irrIndex] + httc_can*LC[wallIndex]
                                           + httc_can*LC[VegIndex] + httc_rur*PlanCan)

    if LC[roofIndex] > 0.75:
        Tac = -999.0
        Tsurf_horz = mod_data_ts_[i][9][roofIndex]*LcH[roofIndex]

    if skipTa:
        Tac = -999.0

    # Ts_in_frac = []
    #
    # Ts_in_frac.append(mod_data_ts_[i][9][roofIndex] * LC[roofIndex])
    # Ts_in_frac.append(mod_data_ts_[i][fg][roadIndex] * LC[roadIndex])
    # Ts_in_frac.append(mod_data_ts_[i][fg][watrIndex] * LC[watrIndex])
    # Ts_in_frac.append(mod_data_ts_[i][fg][concIndex] * LC[concIndex])
    # Ts_in_frac.append(mod_data_ts_[i][9][VegIndex] * LC[VegIndex])
    # Ts_in_frac.append(mod_data_ts_[i][fg][dryIndex] * LC[dryIndex])
    # Ts_in_frac.append(mod_data_ts_[i][fg][irrIndex] * LC[irrIndex])
    # Ts_in_frac.append(mod_data_ts_[i][fw][wallIndex] * LC[wallIndex])

    # [4910, 10302, 24568, 30900, 8837, 14997]
    # if grid in [4910, 24568]:
    #     print('\n')
    #     print('Ta = ', Tac)
    #     print('httc_urb_new', httc_urb_new)
    #     print('z_Hx2-H-z0m_urb, Tb_rur, Tac_can_roof, Uz\n',
    #           z_Hx2-H-z0m_urb, Tb_rur, Tac_can_roof, Uz)
    #     print('Ri_urb_new, Uz, z_Hx2 - H - z0m_urb, z0m_urb, z0h_urb\n',
    #           Ri_urb_new, Uz, z_Hx2 - H - z0m_urb, z0m_urb, z0h_urb)

    # if Tac > Tsurf_horz and Tac > Tb_rur:
    #     print(Tac)
    #     print(str(i) + '\t' + str(grid))
    #     print(mod_data_ts_[i])
    #     print(LC)
    #     print('fg=' + str(fg) + '\tfw=' + str(fw))
    #     print(httc_can)
    #     print(Tb_rur)
    #     print(httc_urb_new)
    #     print(PlanCan)


    return {'Ucan': Ucan, 'Ts_horz': Tsurf_horz, 'Ts_can': Tsurf_can, 'Ts_wall': Tsurf_wall, 'Tac': Tac,
            'Tac_can_roof': Tac_can_roof, 'roofTsrfT': roofTsrfT, 'Tacprv': Tacprv, 'Tcorrhi': Ri_return['Tcorrhi'],
            'httc_urb_new': httc_urb_new, 'Fh': httcReturn['Fh'], 'httc_can': httc_can, 'Twall': Tsurf_wall, 'fg': fg,
            'fw': fw}

    # return{'Ts_in_frac': Ts_in_frac, 'LC': LC, 'Tac': Tac,}