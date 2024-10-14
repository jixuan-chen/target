"""

simple water body model 

calculates water surface temperature AND water energy balance 

see section 3.4 tech description for more details

inputs:
    cs      = constants dictionary
    cfM     = main control file
    met_d   = met forcing data frame
    Dats    = dates dictionary
    mod_ts  = surface temperature (Tsurf) data frame
    mod_tm  = ground temperature (Tm) data frame
    i       = current index 
    rad     = net radiation dictionary 
    
Outputs:
    TsW  = surface temperature water
    TSOIL = soil surface temperature below water body
    QeW  = latent heat over water
    QhW  = sensible heat flux water
    QgH  = storage heat flux water 
    TM   =  The average soil (ground) temperature below TSOIL layer 
        
    
"""

from datetime import  timedelta
import math	

def Ts_EB_W(met_d,cs,cfM,mod_ts, mod_tm, Dats,i,rad,vf):

	

    if Dats['dte'] <= Dats['date1A'] +  timedelta(minutes=(2*int(cfM['timestep']))):

        Tw1   = cs['Ts']['watr']			## intial conditions
        Tsoil = cs['Ts']['dry']				## intial conditions
        Gw       = 0.
        LEw 	 = 0.
        Hs       = 0.              
        tM = cs['Tm']['watr']

    else:

        RnW     = rad['Rn']											# net radiation water surface 
        
        Sab = (met_d['Kd'][i]*(1-0.08))*(cs['betaW'] + ((1 - cs['betaW']) * (1 - (math.exp(-(cs['NW'])))))) 		# Kd that penetrates based on Beer's law
        Hs  = cs['pa'] * (cs['cp'] * 1000000.) * cs['hv'] * met_d['WS'][i] * (met_d['Ta'][i] - mod_ts[i - 1][vf]['watr'])			# The sensible heat flux is given by Martinez et al. (2006)
                
        Gw      = -cs['C']['watr'] * cs['Kw'] * ((mod_ts[i - 1][vf]['TSOIL'] - mod_ts[i - 1][vf]['watr']) / cs['zW'])					# the convective heat flux at the bottom of the water layer (and into the soil below)
        
        dlt_soil = ((2 / (cs['C']['soilW'] * cs['dW']) * Gw)) - (cs['ww'] * (mod_ts[i - 1][vf]['TSOIL'] - mod_tm[i - 1][vf]['watr']))				# force restore calc -- change soil temperature change
        Tsoil = mod_ts[i - 1][vf]['TSOIL']+(dlt_soil*int(cfM['timestep'])* 60.)											# soil layer temperature (C)
        
        	
        es = 0.611*math.exp(17.27*mod_ts[i - 1][vf]['watr']/(237.3+mod_ts[i - 1][vf]['watr']))								# saturation vapour pressure (es) (kPA) at the water surface
        ea = 0.611*math.exp(17.27*met_d['Ta'][i]/(237.3+met_d['Ta'][i]))/100*met_d['RH'][i]						# vapour pressure (kPa) of the air (ea)
        qs = (0.622*es)/101.3												# saturated specific humidity (qs) (kg kg-1)
        pu = 101325./(287.04*((mod_ts[i - 1][vf]['watr']+273.15)*1.+0.61*qs))									# density of moist air (pv) (kg m-3)
        qa = (0.622*ea)/101.3												# specific humidity of air (qa), 
        LEw = pu * cs['Lv'] * cs['hv'] * met_d['WS'][i] * (qs - qa)										# The latent heat flux (Qe) (W m-2)
        Q1 = (Sab+(RnW-(met_d['Kd'][i]*(1-0.08))))+Hs-LEw-Gw										# The chage in heat storage of water layer 
        
        dlt_Tw = Q1 / (cs['C']['watr'] * cs['zW']) * int(cfM['timestep']) * 60. 										#  change in surface water Temperature (C)
        Tw1 = mod_ts[i - 1][vf]['watr'] + dlt_Tw

        D = math.sqrt((2 * cs['K']['watr']) / ((2 * math.pi) / 86400.))	# the damping depth for the annual temperature cycle
        Dy = D * math.sqrt(365.)												#  surface water temperature (C) 
        delta_Tm = Gw/(cs['C']['soilW'] * Dy)		## change in Tm per second
        tM = mod_tm[i - 1][vf]['watr'] + (delta_Tm*int(cfM['timestep'])* 60.)


    return {"TsW":Tw1, "TSOIL":Tsoil, 'QeW': LEw, 'QhW': Hs, 'QgW':Gw , 'TM':tM}