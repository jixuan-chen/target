"""
This module can module Ldown if Ldown data is unavailable
After Loridan et al. (2010)

see tech notes appendix 

"""

def ld_mod(met):

    import math

    bcof = 0.015+((1.9*(10**-4))*(met['Ta']))  # eq 7 Loridan et al., (2010)
    flcd = 0.185*((math.exp(bcof*met['RH'])-1))         # eq 6 Loridan et al., (2010)
    ea =0.611*math.exp(17.27*met['Ta']/(237.3+met['Ta']))/100*met['RH']
    w = 46.5*(ea/met['Ta'])   # eq 6 Loridan et al., (2010)
    Emis_clr = 1-(1+w)*math.exp(-math.sqrt(1.2+(3*w)))
    #Emis_sky = Emis_clr+(1-Emis_clr)*(flcd^2)
    LD = (Emis_clr+(1-Emis_clr)*flcd)*(((met['Ta']+273.15)**4)*(5.67*(10**-8)))  ## eq 9 Loridan et al., (2010)
    
    return{'Ld_md':LD}
