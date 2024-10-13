"""


This module calcuates the surface energy balances using the Local-scale Urban Parameterisation Scheme from Grimmond & Oke (2002)

see section 3.2 tech notes for details

inputs:
    rad     = radiation dictionary
    cs      = constants dictionary
    cfM     = main control file
    met     = met forcing data frame
    surf    = current surface type   
    Dats    = dates dictionary
    i       = current index 
    
Outputs:
    Qe = latent heat flux for surface type
    Qh = sensible heat flux for surface type
    Qg = ground heat flux for surface type 


"""


from datetime import timedelta


def LUMPS(rad,cs,cfM,met,surf,Dats,i):


    if Dats['dte'] <= Dats['date1A'] +  timedelta(minutes=(2*int(cfM['timestep']))):
        
        Qh=0.
        Qe=0.
        Qg=0.
        alphapm=0.
    
    else:

        Qg = (cs['LUMPS1'][surf][0] * rad['Rn']) + (cs['LUMPS1'][surf][1] * rad['Rnstar']) + (cs['LUMPS1'][surf][2])

    ## ALPHA PARAMETER
    alphapm = cs['alphapm'][surf]

    ##  BETA PARAMETER
    betA = cs['beta'][surf]

    Lambda =  2.501 - 0.002361 * met['Ta'][i]                                 # MJ / kg -  latent heat of vaporization

    gamma  = ((met['P'][i]/10) * cs['cp']) / (cs['e'] * Lambda)                         # kPa / C- psychrometric constant
    ew = 6.1121 * (1.0007 + 3.46e-6 * (met['P'][i] / 10)) ** ((17.502 * (met['Ta'][i])) / (240.97 + (met['Ta'][i])))          # in kPa
    s  = 0.62197 * (ew / ((met['P'][i] / 10) - 0.378 * ew))


    Qh = ((((1.-alphapm) + gamma / s) / (1. + gamma / s) ) * (rad['Rn'] - Qg)) - betA
    Qe = (alphapm / (1. + (gamma / s))) * (rad['Rn'] - Qg) + betA


    return {'Qh':Qh, 'Qg':Qg, 'Qe':Qe, 'alphapm':alphapm }

