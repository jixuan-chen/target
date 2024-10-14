"""

calculates net radiation for current, previous, and next time step

see section 3.1 tech description for more details

inputs:
    cs      = constants dictionary
    met     = met forcing data frame
    surf    = current surface type   
    Dats    = dates dictionary
    mod_ts  = surface temperature data frame
    i       = current index 
    
Outputs:
    Rn     = net radiation
    Rnprev = net radiation (t-1)
    Rnstar = 0.5*(Rn(t-1) + Rn(t+1))
    
    
    
"""


def rn_calc(cs, met, surf, Dats, mod_ts, i, svf):
    albedo = cs['alb'][surf]  # surface albedo
    emiss = cs['emis'][surf]  # surface emissivity

    if Dats['dte'] == Dats['date1A']:
        # intial values set to 0.
        Rn = 0.
        Rnprev = 0.
        Rnnext = 0.
        Rnstar = 0.
    else:
        Ta_srfp = mod_ts[2]  # "previous" modelled T_surf (3 timesteps back)
        Ta_srf = mod_ts[1]  # "current" modelled T_Surf (2 time steps back)
        Ta_srfn = mod_ts[0]  # "next" modelled T_Surf (1 time steps back)

        if surf != 'roof':
            Rn = met['Kd'][i] * (1 - albedo) * svf + emiss * (met['Ld'][i] - cs['sb'] * (
                        Ta_srf + 273.15) ** 4) * svf  # modified version of eq 11 Loridan et al. (2011)
            Rnprev = met['Kd'][i - 1] * (1 - albedo) * svf + emiss * (
                        met['Ld'][i - 1] - cs['sb'] * (Ta_srfp + 273.15) ** 4) * svf
            Rnnext = met['Kd'][i + 1] * (1 - albedo) * svf + emiss * (
                        met['Ld'][i + 1] - cs['sb'] * (Ta_srfn + 273.15) ** 4) * svf
            Rnstar = 0.5 * (Rnnext - Rnprev)
        else:
            Rn = met['Kd'][i] * (1 - albedo) + emiss * (met['Ld'][i] - cs['sb'] * (
                        Ta_srf + 273.15) ** 4)  # modified version of eq 11 Loridan et al. (2011)
            Rnprev = met['Kd'][i - 1] * (1 - albedo) + emiss * (met['Ld'][i - 1] - cs['sb'] * (Ta_srfp + 273.15) ** 4)
            Rnnext = met['Kd'][i + 1] * (1 - albedo) * svf + emiss * (
                        met['Ld'][i + 1] - cs['sb'] * (Ta_srfn + 273.15) ** 4)
            Rnstar = 0.5 * (Rnnext - Rnprev)

    return {'Rn': Rn, 'Rnprev': Rnprev, 'Rnstar': Rnstar}
