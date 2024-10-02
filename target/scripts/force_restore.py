"""
calculates surface temperature using force-restore method (Jacobs, 2000)
 
see section 3.3 tech notes for details

inputs:
    eng_bal     = energy balance dictionary
    cs          = constants dictionary
    cfM         = main control file
    mod_ts      = modelled surface temperature dataframe
    mod_tm      = modelled ground temperature dataframe 
    surf        = current surface type   
    Dats        = dates dictionary
    i           = current index 
    
Outputs:
    Ts = modelled surface temperature (Tsurf)
    Tm = modelled soil (ground)  temperature (Tm)
 
 
 
"""
import math
from datetime import timedelta


def Ts_calc_surf(eng_bal, cs, cfM, mod_ts, mod_tm, Dats, surf, i):
    if Dats['dte'] <= Dats['date1A'] + timedelta(minutes=(2 * int(cfM['timestep']))):
        tS = float(cs['Ts'][surf])  # initial conditions for Tsurf
        tM = float(cs['Tm'][surf])  # initial conditions for Tm

    else:
        # calculate ground heat flux
        QGS = eng_bal['Qg']
        # the damping depth for the annual temperature cycle
        D = math.sqrt((2 * cs['K'][surf]) / ((2 * math.pi) / 86400))
        Dy = D * math.sqrt(365)

        # change in Tsurf per second
        delta_Tg = 2 / (cs['C'][surf] * D) * QGS - (2 * math.pi / 86400) * (mod_ts[0] - mod_tm[0])
        # change in Tm per second
        delta_Tm = QGS / (cs['C'][surf] * Dy)

        # update Tm (60 seconds in a minute timestep)
        tM = mod_tm[0] + (delta_Tm * int(cfM['timestep']) * 60)
        # update Tsurf (3600. seconds in an hour timestep)
        tS = mod_ts[0] + (delta_Tg * int(cfM['timestep']) * 60)

    return {'TS': tS, 'TM': tM}
