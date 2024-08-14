import math

diamGlobe = 0.05


def fTd(Ta, RH):
    RHD = RH / 100
    fTd = 237.3 * (math.log(RHD) / 17.27 + Ta / (237.3 + Ta)) / (1 - math.log(RHD) / 17.27 - Ta / (237.3 + Ta))
    return fTd


def emis_atm(Ta, RH):
    # Reference: Oke (2nd edition), page 373.
    e = RH * esat(Ta)
    emis_atm = 0.575 * (e ** 0.143)
    return emis_atm


def esat(Tk):
    # Purpose: calculate the saturation vapor pressure (mb) over liquid water given the temperature (K).
    # Reference: Buck's (1981) approximation (eqn 3) of Wexler's (1976) formulae.
    # over liquid water
    esat = 6.1121 * math.exp(17.502 * (Tk - 273.15) / (Tk - 32.18))
    esat = 1.004 * esat
    return esat


def viscosity(Tair):
    # Purpose: Compute the viscosity of air, kg/(m s) given temperature, K, Reference: BSL, page 23.
    omega = (Tair / 97 - 2.9) / 0.4 * (-0.034) + 1.048
    viscosity = 0.0000026693 * (28.97 * Tair) ** 0.5 / (3.617 ** 2 * omega)
    return viscosity


def h_sphere_in_air(Tair, Pair, speed, speedMin):
    # Purpose: to calculate the convective heat tranfer coefficient for flow around a sphere.
    # Reference: Bird, Stewart, and Lightfoot (BSL), page 409.
    Rair = 8314.34 / 28.97
    Pr = 1003.5 / (1003.5 + 1.25 * Rair)
    thermal_con = (1003.5 + 1.25 * 8314.34 / 28.97) * viscosity(Tair)
    density = Pair * 100 / (Rair * Tair)  # kg/m3
    if speed < speedMin:
        speed = speedMin
    Re = speed * density * diamGlobe / viscosity(Tair)
    Nu = 2 + 0.6 * Re ** 0.5 * Pr ** 0.3333
    h_sphere_in_air = Nu * thermal_con / diamGlobe  # W/(m2 K)
    return h_sphere_in_air


def sunpos(jday, tm, lat):
    pi = 3.1415926
    sh = False
    hr_rad = 15 * pi / 180
    theta = (jday - 1) * (2 * pi) / 365
    # for southern hemisphere
    if lat < 0:
        theta = theta + pi % 2 * pi
        sh = True
        lat = abs(lat)
    # declination angle
    dec = 0.006918 - 0.399912 * math.cos(theta) + 0.070257 * math.sin(theta) - 0.006758 * math.cos(2 * theta)
    + 0.000907 * math.sin(2 * theta) - 0.002697 * math.cos(3 * theta) + 0.00148 * math.sin(3 * theta)
    # all the changes are from stull, meteorology for scientists and
    # engineers 2000 - note: the current definition of hl give the solar
    # position based on local mean solar time - to have solar position as
    # as function of standard time in the time zone, must use stull's
    # equation 2.9 on p. 26
    hl = tm * hr_rad
    cz = (math.sin(lat) * math.sin(dec)) - (math.cos(lat) * math.cos(dec) * math.cos(hl))
    zen = math.acos(cz)
    return zen


def getZenith(yd, timeis, xlat):
    pi = 3.1415926
    LAT = xlat * pi / 180
    TM = timeis % 24
    yd_actual = yd + (TM / 24)
    yd_actual = yd_actual % 365
    zeni = sunpos(yd_actual, TM, LAT)
    zen = zeni * 180 / pi
    return zen


def radianToDegree(radian):
    pi = 3.1415926
    R_to_D = 180 / pi
    radianToDegree = radian * R_to_D
    return radianToDegree


def getFdir(zenith, solar):
    d = 1  # should calculate earth-sun distance, but set to mean value (1 A.U.)
    zenDegrees = radianToDegree(zenith)
    fdir = 0  # default, for zenDegrees > 89.5
    if zenDegrees <= 89.5:
        s0 = 1367
        smax = s0 * math.cos(zenith) / d * d
        sstar = solar / smax
        # division by zero error
        if sstar == 0:
            sstar += 0.000001
        fdir = math.exp(3.0 - 1.34 * sstar - 1.65 / sstar)
    return fdir


def fTg4(Ta, relh, PairIn, speed, solar, fdir, zenith, speedMin, Tsfc, emisAtmValue, lIn, lOut):
    SurfAlbedo = 0.15
    stefanb = 0.000000056696
    diamGlobe = 0.15
    diamWick = 0.007
    lenWick = 0.0254
    propDirect = 0.8  # Assume a proportion of direct radiation = direct/(diffuse + direct)

    ZenithAngle = 0.  # angle of sun from directly above
    MinWindSpeed = 0.1  # 0 wind speed upsets log function
    AtmPressure = 101  # Atmospheric pressure in kPa
    ERROR_RETURN = -9999

    # Purpose: to calculate the globe temperature
    # Author: James C. Liljegren
    # Decision and Information Sciences Division
    # Argonne National Laboratory
    # Pressure in kPa (Atm =101 kPa)
    # Fix up out-of bounds problems with zenith
    if zenith <= 0:
        zenith = 0.0000000001
    if zenith > 1.57:
        zenith = 1.57

    Pair = PairIn * 10
    cza = math.cos(zenith)
    converge = 0.05
    alb_sfc = SurfAlbedo
    alb_globe = 0.05
    emis_globe = 0.95
    emis_sfc = 0.999
    Tair = Ta + 273.15
    RH = relh * 0.01

    TsfcK = Tsfc + 273.15
    Tglobe_prev = Tair
    area = 3.1415 * diamGlobe * diamGlobe

    # Do iteration
    testno = 1
    continueLoop = True
    Tglobe = 0

    while continueLoop:
        testno += 1
        if testno > 1000:
            print("No convergence: values too extreme")
            fTg4 = ERROR_RETURN
            return fTg4

        # Evaluate properties at the average temperature
        Tref = 0.5 * (Tglobe_prev + Tair)

        h = h_sphere_in_air(Tref, Pair, speed, speedMin)
        # a=area * 0.5 * emis_globe * stefanb * (emisAtmValue * Tair**4 +  emis_sfc * TsfcK**4 )
        # term for energy gained by globe due to thermal radiation from atm and surface
        a = area * 0.5 * emis_globe * (lIn + lOut)
        # term for energy gained due to diffuse irradiance
        b = area * 0.5 * (1 - alb_globe) * (1 - fdir) * solar
        # term for energy gained due to direct irradiance
        c = area * 0.25 * (1 - alb_globe) * fdir * solar / cza
        # # term for solar irradiance reflected from the surface that is absorbed by the globe
        d = area * 0.5 * (1 - alb_globe) * alb_sfc * solar
        # term for energy lost from the globe due to convection
        e = area * h * (Tglobe_prev - Tair)

        Tglobe = math.pow(((a + b + c + d - e) / (area * emis_globe * stefanb)), 0.25)
        dT = Tglobe - Tglobe_prev

        if (abs(dT) < converge):
            continueLoop = False
        else:
            Tglobe_prev = (0.9 * Tglobe_prev + 0.1 * Tglobe)
            continueLoop = True

    fTg4 = Tglobe - 273.15
    return fTg4


def getTmrtForGrid_RH(Ta, relh, speed, solar, tsfc, ldown, lup, yd_actual, TM, LAT):
    zenith = getZenith(yd_actual, TM, LAT)
    Pair = 100.0
    speedMin = 0.5
    emisAtmValue = emis_atm(Ta + 273.15, relh * 0.01)
    if solar < 50:
        emisAtmValue = 0.99
    fdir = getFdir(zenith, solar)
    Tg = fTg4(Ta, relh, Pair, speed, solar, fdir, zenith, speedMin, tsfc, emisAtmValue, ldown, lup)
    tmrtC = fTmrtD(Ta, Tg, speed)
    getTmrtForGrid = tmrtC
    return getTmrtForGrid


def fTmrtD(Ta, Tg, ws):
    # from Kantor and Unger 2011
    emis_globe = 0.95
    diamGlobe = 0.15
    wsCm = ws / 100  # convert m/s to cm/s
    Tmrt = (((((Tg + 273.15) ** 4) + (1.1 * (10 ** 8) * (wsCm ** 0.6) / (emis_globe * (diamGlobe ** 0.4)))
              * (Tg - Ta))) ** 0.25) - 273.15
    return Tmrt


def getUTCIForGrid_RH(Ta, ws, RH, tmrt):
    # getUTCIForGrid = fUTCI2(Ta, ws, RH, tmrt)
    getUTCIForGrid = UTCI_fortran(Ta, ws, RH, tmrt)
    return getUTCIForGrid


def fUTCI2(Ta, ws, RH, Tmrt):
    Td = fTd(Ta, RH)

    PA = 0.6108 * math.exp(17.29 * Td / (Td + 237.3))
    D_Tmrt = Tmrt - Ta

    ET1 = Ta + 0.607562052 - 0.0227712343 * Ta + 0.000806470249 * Ta * Ta - 0.000154271372 * Ta * Ta * Ta
    - 0.00000324651735 * Ta * Ta * Ta * Ta + 7.32602852E-08 * Ta * Ta * Ta * Ta * Ta + 1.35959073E-09 * Ta * Ta * Ta * Ta * Ta * Ta
    - 2.2583652 * ws + 0.0880326035 * Ta * ws + 0.00216844454 * Ta * Ta * ws - 0.0000153347087 * Ta * Ta * Ta * ws
    - 0.000000572983704 * Ta * Ta * Ta * Ta * ws - 2.55090145E-09 * Ta * Ta * Ta * Ta * Ta * ws
    - 0.751269505 * ws * ws - 0.00408350271 * Ta * ws * ws - 0.0000521670675 * Ta * Ta * ws * ws
    + 0.00000194544667 * Ta * Ta * Ta * ws * ws + 1.14099531E-08 * Ta * Ta * Ta * Ta * ws * ws
    + 0.158137256 * ws * ws * ws - 0.0000657263143 * Ta * ws * ws * ws + 0.000000222697524 * Ta * Ta * ws * ws * ws - 4.16117031E-08 * Ta * Ta * Ta * ws * ws * ws
    - 0.0127762753 * ws * ws * ws * ws + 0.00000966891875 * Ta * ws * ws * ws * ws + 2.52785852E-09 * Ta * Ta * ws * ws * ws * ws
    + 0.000456306672 * ws * ws * ws * ws * ws - 0.000000174202546 * Ta * ws * ws * ws * ws * ws - 0.00000591491269 * ws * ws * ws * ws * ws * ws
    + 0.398374029 * D_Tmrt + 0.000183945314 * Ta * D_Tmrt - 0.00017375451 * Ta * Ta * D_Tmrt
    - 0.000000760781159 * Ta * Ta * Ta * D_Tmrt + 3.77830287E-08 * Ta * Ta * Ta * Ta * D_Tmrt + 5.43079673E-10 * Ta * Ta * Ta * Ta * Ta * D_Tmrt
    - 0.0200518269 * ws * D_Tmrt + 0.000892859837 * Ta * ws * D_Tmrt + 0.00000345433048 * Ta * Ta * ws * D_Tmrt
    - 0.000000377925774 * Ta * Ta * Ta * ws * D_Tmrt - 1.69699377E-09 * Ta * Ta * Ta * Ta * ws * D_Tmrt + 0.000169992415 * ws * ws * D_Tmrt
    - 0.0000499204314 * Ta * ws * ws * D_Tmrt + 0.000000247417178 * Ta * Ta * ws * ws * D_Tmrt + 1.07596466E-08 * Ta * Ta * Ta * ws * ws * D_Tmrt
    + 0.0000849242932 * ws * ws * ws * D_Tmrt + 0.00000135191328 * Ta * ws * ws * ws * D_Tmrt - 6.21531254E-09 * Ta * Ta * ws * ws * ws * D_Tmrt
    - 0.00000499410301 * ws * ws * ws * ws * D_Tmrt - 1.89489258E-08 * Ta * ws * ws * ws * ws * D_Tmrt + 8.15300114E-08 * ws * ws * ws * ws * ws * D_Tmrt
    + 0.00075504309 * D_Tmrt * D_Tmrt

    ET3 = -0.0000565095215 * Ta * D_Tmrt * D_Tmrt + (-0.000000452166564) * Ta * Ta * D_Tmrt * D_Tmrt
    + (2.46688878E-08) * Ta * Ta * Ta * D_Tmrt * D_Tmrt + (2.42674348E-10) * Ta * Ta * Ta * Ta * D_Tmrt * D_Tmrt
    + (0.00015454725) * ws * D_Tmrt * D_Tmrt + (0.0000052411097) * Ta * ws * D_Tmrt * D_Tmrt
    + (-8.75874982E-08) * Ta * Ta * ws * D_Tmrt * D_Tmrt + (-1.50743064E-09) * Ta * Ta * Ta * ws * D_Tmrt * D_Tmrt
    + (-0.0000156236307) * ws * ws * D_Tmrt * D_Tmrt + (-0.000000133895614) * Ta * ws * ws * D_Tmrt * D_Tmrt
    + (2.49709824E-09) * Ta * Ta * ws * ws * D_Tmrt * D_Tmrt + (0.000000651711721) * ws * ws * ws * D_Tmrt * D_Tmrt
    + (1.94960053E-09) * Ta * ws * ws * ws * D_Tmrt * D_Tmrt + (-1.00361113E-08) * ws * ws * ws * ws * D_Tmrt * D_Tmrt
    + (-0.0000121206673) * D_Tmrt * D_Tmrt * D_Tmrt + (-0.00000021820366) * Ta * D_Tmrt * D_Tmrt * D_Tmrt
    + (7.51269482E-09) * Ta * Ta * D_Tmrt * D_Tmrt * D_Tmrt + (9.79063848E-11) * Ta * Ta * Ta * D_Tmrt * D_Tmrt * D_Tmrt
    + (0.00000125006734) * ws * D_Tmrt * D_Tmrt * D_Tmrt + (-1.81584736E-09) * Ta * ws * D_Tmrt * D_Tmrt * D_Tmrt
    + (-3.52197671E-10) * Ta * Ta * ws * D_Tmrt * D_Tmrt * D_Tmrt + (
        -0.000000033651463) * ws * ws * D_Tmrt * D_Tmrt * D_Tmrt
    + (1.35908359E-10) * Ta * ws * ws * D_Tmrt * D_Tmrt * D_Tmrt + (
        4.1703262E-10) * ws * ws * ws * D_Tmrt * D_Tmrt * D_Tmrt
    + (-1.30369025E-09) * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt

    ET4 = 4.13908461E-10 * Ta * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt + (
        9.22652254E-12) * Ta * Ta * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt
    + (-5.08220384E-09) * ws * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt + (
        -2.24730961E-11) * Ta * ws * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt
    + (1.17139133E-10) * ws * ws * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt + (
        6.62154879E-10) * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt
    + (4.0386326E-13) * Ta * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt + (
        1.95087203E-12) * ws * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt
    + (-4.73602469E-12) * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt + (5.12733497) * PA + (
        -0.312788561) * Ta * PA
    + (-0.0196701861) * Ta * Ta * PA + (0.00099969087) * Ta * Ta * Ta * PA + (0.00000951738512) * Ta * Ta * Ta * Ta * PA
    + (-0.000000466426341) * Ta * Ta * Ta * Ta * Ta * PA + (0.548050612) * ws * PA + (-0.00330552823) * Ta * ws * PA
    + (-0.0016411944) * Ta * Ta * ws * PA + (-0.00000516670694) * Ta * Ta * Ta * ws * PA + (
        0.000000952692432) * Ta * Ta * Ta * Ta * ws * PA
    + (-0.0429223622) * ws * ws * PA + (0.00500845667) * Ta * ws * ws * PA + (0.00000100601257) * Ta * Ta * ws * ws * PA
    + (-0.00000181748644) * Ta * Ta * Ta * ws * ws * PA + (-0.00125813502) * ws * ws * ws * PA

    ET5 = -0.000179330391 * Ta * ws * ws * ws * PA + (0.00000234994441) * Ta * Ta * ws * ws * ws * PA + (
        0.000129735808) * ws * ws * ws * ws * PA
    + (0.0000012906487) * Ta * ws * ws * ws * ws * PA + (-0.00000228558686) * ws * ws * ws * ws * ws * PA + (
        -0.0369476348) * D_Tmrt * PA
    + (0.00162325322) * Ta * D_Tmrt * PA + (-0.000031427968) * Ta * Ta * D_Tmrt * PA + (
        0.00000259835559) * Ta * Ta * Ta * D_Tmrt * PA
    + (-4.77136523E-08) * Ta * Ta * Ta * Ta * D_Tmrt * PA + (0.0086420339) * ws * D_Tmrt * PA + (
        -0.000687405181) * Ta * ws * D_Tmrt * PA
    + (-0.00000913863872) * Ta * Ta * ws * D_Tmrt * PA + (0.000000515916806) * Ta * Ta * Ta * ws * D_Tmrt * PA + (
        -0.0000359217476) * ws * ws * D_Tmrt * PA
    + (0.0000328696511) * Ta * ws * ws * D_Tmrt * PA + (-0.000000710542454) * Ta * Ta * ws * ws * D_Tmrt * PA + (
        -0.00001243823) * ws * ws * ws * D_Tmrt * PA
    + (-0.000000007385844) * Ta * ws * ws * ws * D_Tmrt * PA + (0.000000220609296) * ws * ws * ws * ws * D_Tmrt * PA
    + (-0.00073246918) * D_Tmrt * D_Tmrt * PA + (-0.0000187381964) * Ta * D_Tmrt * D_Tmrt * PA + (
        0.00000480925239) * Ta * Ta * D_Tmrt * D_Tmrt * PA
    + (-0.000000087549204) * Ta * Ta * Ta * D_Tmrt * D_Tmrt * PA + (0.000027786293) * ws * D_Tmrt * D_Tmrt * PA

    ET6 = -0.00000506004592 * Ta * ws * D_Tmrt * D_Tmrt * PA + (0.000000114325367) * Ta * Ta * ws * D_Tmrt * D_Tmrt * PA
    + (0.00000253016723) * ws * ws * D_Tmrt * D_Tmrt * PA + (-1.72857035E-08) * Ta * ws * ws * D_Tmrt * D_Tmrt * PA
    + (-3.95079398E-08) * ws * ws * ws * D_Tmrt * D_Tmrt * PA + (-0.000000359413173) * D_Tmrt * D_Tmrt * D_Tmrt * PA
    + (0.000000704388046) * Ta * D_Tmrt * D_Tmrt * D_Tmrt * PA + (
        -1.89309167E-08) * Ta * Ta * D_Tmrt * D_Tmrt * D_Tmrt * PA
    + (-0.000000479768731) * ws * D_Tmrt * D_Tmrt * D_Tmrt * PA + (
        7.96079978E-09) * Ta * ws * D_Tmrt * D_Tmrt * D_Tmrt * PA
    + (1.62897058E-09) * ws * ws * D_Tmrt * D_Tmrt * D_Tmrt * PA + (
        3.94367674E-08) * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt * PA
    + (-1.18566247E-09) * Ta * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt * PA + (
        3.34678041E-10) * ws * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt * PA
    + (-1.15606447E-10) * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt * PA + (-2.80626406) * PA * PA + (
        0.548712484) * Ta * PA * PA
    + (-0.0039942841) * Ta * Ta * PA * PA + (-0.000954009191) * Ta * Ta * Ta * PA * PA + (
        0.0000193090978) * Ta * Ta * Ta * Ta * PA * PA
    + (-0.308806365) * ws * PA * PA + (0.0116952364) * Ta * ws * PA * PA + (0.000495271903) * Ta * Ta * ws * PA * PA
    + (-0.0000190710882) * Ta * Ta * Ta * ws * PA * PA + (0.00210787756) * ws * ws * PA * PA

    ET7 = -0.000698445738 * Ta * ws * ws * PA * PA + (0.0000230109073) * Ta * Ta * ws * ws * PA * PA + (
        0.00041785659) * ws * ws * ws * PA * PA
    + (-0.0000127043871) * Ta * ws * ws * ws * PA * PA + (-0.00000304620472) * ws * ws * ws * ws * PA * PA + (
        0.0514507424) * D_Tmrt * PA * PA
    + (-0.00432510997) * Ta * D_Tmrt * PA * PA + (0.0000899281156) * Ta * Ta * D_Tmrt * PA * PA + (
        -0.000000714663943) * Ta * Ta * Ta * D_Tmrt * PA * PA
    + (-0.000266016305) * ws * D_Tmrt * PA * PA + (0.000263789586) * Ta * ws * D_Tmrt * PA * PA + (
        -0.00000701199003) * Ta * Ta * ws * D_Tmrt * PA * PA
    + (-0.000106823306) * ws * ws * D_Tmrt * PA * PA + (0.00000361341136) * Ta * ws * ws * D_Tmrt * PA * PA
    + (0.000000229748967) * ws * ws * ws * D_Tmrt * PA * PA + (0.000304788893) * D_Tmrt * D_Tmrt * PA * PA
    + (-0.0000642070836) * Ta * D_Tmrt * D_Tmrt * PA * PA + (0.00000116257971) * Ta * Ta * D_Tmrt * D_Tmrt * PA * PA
    + (0.00000768023384) * ws * D_Tmrt * D_Tmrt * PA * PA + (-0.000000547446896) * Ta * ws * D_Tmrt * D_Tmrt * PA * PA
    + (-0.000000035993791) * ws * ws * D_Tmrt * D_Tmrt * PA * PA + (
        -0.00000436497725) * D_Tmrt * D_Tmrt * D_Tmrt * PA * PA
    + (0.000000168737969) * Ta * D_Tmrt * D_Tmrt * D_Tmrt * PA * PA + (
        2.67489271E-08) * ws * D_Tmrt * D_Tmrt * D_Tmrt * PA * PA
    + (3.23926897E-09) * D_Tmrt * D_Tmrt * D_Tmrt * D_Tmrt * PA * PA

    ET8 = -0.0353874123 * PA * PA * PA + (-0.22120119) * Ta * PA * PA * PA + (0.0155126038) * Ta * Ta * PA * PA * PA
    + (-0.000263917279) * Ta * Ta * Ta * PA * PA * PA + (0.0453433455) * ws * PA * PA * PA + (
        -0.00432943862) * Ta * ws * PA * PA * PA
    + (0.000145389826) * Ta * Ta * ws * PA * PA * PA + (0.00021750861) * ws * ws * PA * PA * PA + (
        -0.0000666724702) * Ta * ws * ws * PA * PA * PA
    + (0.000033321714) * ws * ws * ws * PA * PA * PA + (-0.00226921615) * D_Tmrt * PA * PA * PA + (
        0.000380261982) * Ta * D_Tmrt * PA * PA * PA
    + (-5.45314314E-09) * Ta * Ta * D_Tmrt * PA * PA * PA + (-0.000796355448) * ws * D_Tmrt * PA * PA * PA + (
        0.0000253458034) * Ta * ws * D_Tmrt * PA * PA * PA
    + (-0.00000631223658) * ws * ws * D_Tmrt * PA * PA * PA + (0.000302122035) * D_Tmrt * D_Tmrt * PA * PA * PA
    + (-0.00000477403547) * Ta * D_Tmrt * D_Tmrt * PA * PA * PA + (
        0.00000173825715) * ws * D_Tmrt * D_Tmrt * PA * PA * PA
    + (-0.000000409087898) * D_Tmrt * D_Tmrt * D_Tmrt * PA * PA * PA + (0.614155345) * PA * PA * PA * PA
    + (-0.0616755931) * Ta * PA * PA * PA * PA + (0.00133374846) * Ta * Ta * PA * PA * PA * PA + (
        0.00355375387) * ws * PA * PA * PA * PA
    + (-0.000513027851) * Ta * ws * PA * PA * PA * PA

    ET9 = 0.000102449757 * ws * ws * PA * PA * PA * PA + (-0.00148526421) * D_Tmrt * PA * PA * PA * PA
    + (-0.0000411469183) * Ta * D_Tmrt * PA * PA * PA * PA + (-0.00000680434415) * ws * D_Tmrt * PA * PA * PA * PA
    + (-0.00000977675906) * D_Tmrt * D_Tmrt * PA * PA * PA * PA + (0.0882773108) * PA * PA * PA * PA * PA
    + (-0.00301859306) * Ta * PA * PA * PA * PA * PA + (0.00104452989) * ws * PA * PA * PA * PA * PA
    + (0.000247090539) * D_Tmrt * PA * PA * PA * PA * PA + (0.00148348065) * PA * PA * PA * PA * PA * PA

    fUTCI = ET1 + ET3 + ET4 + ET5 + ET6 + ET7 + ET8 + ET9
    return fUTCI


def UTCI_cat(UTCI):
    if UTCI > 46:
        cat = 1
    elif 38 < UTCI <= 46:
        cat = 2
    elif 32 < UTCI <= 38:
        cat = 3
    elif 26 < UTCI <= 32:
        cat = 4
    elif 9 < UTCI <= 26:
        cat = 5
    elif 0 < UTCI <= 9:
        cat = 6
    elif -13 < UTCI <= 0:
        cat = 7
    elif -27 < UTCI <= -13:
        cat = 8
    elif -40 < UTCI <= -27:
        cat = 9
    elif UTCI == -999:
        cat = -999
    else:
        cat = 10
    return cat


def UTCI_fortran(Ta, ws, RH, Tmrt):
    Td = fTd(Ta, RH)

    PA = 0.6108 * math.exp(17.29 * Td / (Td + 237.3))
    D_Tmrt = Tmrt - Ta
    utci=Ta+ \
    (6.07562052e-01)+ \
    (-2.27712343e-02)*Ta+ \
    (8.06470249e-04)*Ta*Ta+ \
    (-1.54271372e-04)*Ta*Ta*Ta+ \
    (-3.24651735e-06)*Ta*Ta*Ta*Ta+ \
    (7.32602852e-08)*Ta*Ta*Ta*Ta*Ta+ \
    (1.35959073e-09)*Ta*Ta*Ta*Ta*Ta*Ta+ \
    (-2.25836520e+00)*ws+ \
    (8.80326035e-02)*Ta*ws+ \
    (2.16844454e-03)*Ta*Ta*ws+ \
    (-1.53347087e-05)*Ta*Ta*Ta*ws+ \
    (-5.72983704e-07)*Ta*Ta*Ta*Ta*ws+ \
    (-2.55090145e-09)*Ta*Ta*Ta*Ta*Ta*ws+ \
    (-7.51269505e-01)*ws*ws+ \
    (-4.08350271e-03)*Ta*ws*ws+ \
    (-5.21670675e-05)*Ta*Ta*ws*ws+ \
    (1.94544667e-06)*Ta*Ta*Ta*ws*ws+ \
    (1.14099531e-08)*Ta*Ta*Ta*Ta*ws*ws+ \
    (1.58137256e-01)*ws*ws*ws+ \
    (-6.57263143e-05)*Ta*ws*ws*ws+ \
    (2.22697524e-07)*Ta*Ta*ws*ws*ws+ \
    (-4.16117031e-08)*Ta*Ta*Ta*ws*ws*ws+ \
    (-1.27762753e-02)*ws*ws*ws*ws+ \
    (9.66891875e-06)*Ta*ws*ws*ws*ws+ \
    (2.52785852e-09)*Ta*Ta*ws*ws*ws*ws+ \
    (4.56306672e-04)*ws*ws*ws*ws*ws+ \
    (-1.74202546e-07)*Ta*ws*ws*ws*ws*ws+ \
    (-5.91491269e-06)*ws*ws*ws*ws*ws*ws+ \
    (3.98374029e-01)*D_Tmrt+ \
    (1.83945314e-04)*Ta*D_Tmrt+ \
    (-1.73754510e-04)*Ta*Ta*D_Tmrt+ \
    (-7.60781159e-07)*Ta*Ta*Ta*D_Tmrt+ \
    (3.77830287e-08)*Ta*Ta*Ta*Ta*D_Tmrt+ \
    (5.43079673e-10)*Ta*Ta*Ta*Ta*Ta*D_Tmrt+ \
    (-2.00518269e-02)*ws*D_Tmrt+ \
    (8.92859837e-04)*Ta*ws*D_Tmrt+ \
    (3.45433048e-06)*Ta*Ta*ws*D_Tmrt+ \
    (-3.77925774e-07)*Ta*Ta*Ta*ws*D_Tmrt+ \
    (-1.69699377e-09)*Ta*Ta*Ta*Ta*ws*D_Tmrt+ \
    (1.69992415e-04)*ws*ws*D_Tmrt+ \
    (-4.99204314e-05)*Ta*ws*ws*D_Tmrt+ \
    (2.47417178e-07)*Ta*Ta*ws*ws*D_Tmrt+ \
    (1.07596466e-08)*Ta*Ta*Ta*ws*ws*D_Tmrt+ \
    (8.49242932e-05)*ws*ws*ws*D_Tmrt+ \
    (1.35191328e-06)*Ta*ws*ws*ws*D_Tmrt+ \
    (-6.21531254e-09)*Ta*Ta*ws*ws*ws*D_Tmrt+ \
    (-4.99410301e-06)*ws*ws*ws*ws*D_Tmrt+ \
    (-1.89489258e-08)*Ta*ws*ws*ws*ws*D_Tmrt+ \
    (8.15300114e-08)*ws*ws*ws*ws*ws*D_Tmrt+ \
    (7.55043090e-04)*D_Tmrt*D_Tmrt+ \
    (-5.65095215e-05)*Ta*D_Tmrt*D_Tmrt+ \
    (-4.52166564e-07)*Ta*Ta*D_Tmrt*D_Tmrt+ \
    (2.46688878e-08)*Ta*Ta*Ta*D_Tmrt*D_Tmrt+ \
    (2.42674348e-10)*Ta*Ta*Ta*Ta*D_Tmrt*D_Tmrt+ \
    (1.54547250e-04)*ws*D_Tmrt*D_Tmrt+ \
    (5.24110970e-06)*Ta*ws*D_Tmrt*D_Tmrt+ \
    (-8.75874982e-08)*Ta*Ta*ws*D_Tmrt*D_Tmrt+ \
    (-1.50743064e-09)*Ta*Ta*Ta*ws*D_Tmrt*D_Tmrt+ \
    (-1.56236307e-05)*ws*ws*D_Tmrt*D_Tmrt+ \
    (-1.33895614e-07)*Ta*ws*ws*D_Tmrt*D_Tmrt+ \
    (2.49709824e-09)*Ta*Ta*ws*ws*D_Tmrt*D_Tmrt+ \
    (6.51711721e-07)*ws*ws*ws*D_Tmrt*D_Tmrt+ \
    (1.94960053e-09)*Ta*ws*ws*ws*D_Tmrt*D_Tmrt+ \
    (-1.00361113e-08)*ws*ws*ws*ws*D_Tmrt*D_Tmrt+ \
    (-1.21206673e-05)*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (-2.18203660e-07)*Ta*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (7.51269482e-09)*Ta*Ta*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (9.79063848e-11)*Ta*Ta*Ta*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (1.25006734e-06)*ws*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (-1.81584736e-09)*Ta*ws*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (-3.52197671e-10)*Ta*Ta*ws*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (-3.36514630e-08)*ws*ws*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (1.35908359e-10)*Ta*ws*ws*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (4.17032620e-10)*ws*ws*ws*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (-1.30369025e-09)*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (4.13908461e-10)*Ta*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (9.22652254e-12)*Ta*Ta*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (-5.08220384e-09)*ws*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (-2.24730961e-11)*Ta*ws*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (1.17139133e-10)*ws*ws*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (6.62154879e-10)*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (4.03863260e-13)*Ta*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (1.95087203e-12)*ws*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (-4.73602469e-12)*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt+ \
    (5.12733497e+00)*PA+ \
    (-3.12788561e-01)*Ta*PA+ \
    (-1.96701861e-02)*Ta*Ta*PA+ \
    (9.99690870e-04)*Ta*Ta*Ta*PA+ \
    (9.51738512e-06)*Ta*Ta*Ta*Ta*PA+ \
    (-4.66426341e-07)*Ta*Ta*Ta*Ta*Ta*PA+ \
    (5.48050612e-01)*ws*PA+ \
    (-3.30552823e-03)*Ta*ws*PA+ \
    (-1.64119440e-03)*Ta*Ta*ws*PA+ \
    (-5.16670694e-06)*Ta*Ta*Ta*ws*PA+ \
    (9.52692432e-07)*Ta*Ta*Ta*Ta*ws*PA+ \
    (-4.29223622e-02)*ws*ws*PA+ \
    (5.00845667e-03)*Ta*ws*ws*PA+ \
    (1.00601257e-06)*Ta*Ta*ws*ws*PA+ \
    (-1.81748644e-06)*Ta*Ta*Ta*ws*ws*PA+ \
    (-1.25813502e-03)*ws*ws*ws*PA+ \
    (-1.79330391e-04)*Ta*ws*ws*ws*PA+ \
    (2.34994441e-06)*Ta*Ta*ws*ws*ws*PA+ \
    (1.29735808e-04)*ws*ws*ws*ws*PA+ \
    (1.29064870e-06)*Ta*ws*ws*ws*ws*PA+ \
    (-2.28558686e-06)*ws*ws*ws*ws*ws*PA+ \
    (-3.69476348e-02)*D_Tmrt*PA+ \
    (1.62325322e-03)*Ta*D_Tmrt*PA+ \
    (-3.14279680e-05)*Ta*Ta*D_Tmrt*PA+ \
    (2.59835559e-06)*Ta*Ta*Ta*D_Tmrt*PA+ \
    (-4.77136523e-08)*Ta*Ta*Ta*Ta*D_Tmrt*PA+ \
    (8.64203390e-03)*ws*D_Tmrt*PA+ \
    (-6.87405181e-04)*Ta*ws*D_Tmrt*PA+ \
    (-9.13863872e-06)*Ta*Ta*ws*D_Tmrt*PA+ \
    (5.15916806e-07)*Ta*Ta*Ta*ws*D_Tmrt*PA+ \
    (-3.59217476e-05)*ws*ws*D_Tmrt*PA+ \
    (3.28696511e-05)*Ta*ws*ws*D_Tmrt*PA+ \
    (-7.10542454e-07)*Ta*Ta*ws*ws*D_Tmrt*PA+ \
    (-1.24382300e-05)*ws*ws*ws*D_Tmrt*PA+ \
    (-7.38584400e-09)*Ta*ws*ws*ws*D_Tmrt*PA+ \
    (2.20609296e-07)*ws*ws*ws*ws*D_Tmrt*PA+ \
    (-7.32469180e-04)*D_Tmrt*D_Tmrt*PA+ \
    (-1.87381964e-05)*Ta*D_Tmrt*D_Tmrt*PA+ \
    (4.80925239e-06)*Ta*Ta*D_Tmrt*D_Tmrt*PA+ \
    (-8.75492040e-08)*Ta*Ta*Ta*D_Tmrt*D_Tmrt*PA+ \
    (2.77862930e-05)*ws*D_Tmrt*D_Tmrt*PA+ \
    (-5.06004592e-06)*Ta*ws*D_Tmrt*D_Tmrt*PA+ \
    (1.14325367e-07)*Ta*Ta*ws*D_Tmrt*D_Tmrt*PA+ \
    (2.53016723e-06)*ws*ws*D_Tmrt*D_Tmrt*PA+ \
    (-1.72857035e-08)*Ta*ws*ws*D_Tmrt*D_Tmrt*PA+ \
    (-3.95079398e-08)*ws*ws*ws*D_Tmrt*D_Tmrt*PA+ \
    (-3.59413173e-07)*D_Tmrt*D_Tmrt*D_Tmrt*PA+ \
    (7.04388046e-07)*Ta*D_Tmrt*D_Tmrt*D_Tmrt*PA+ \
    (-1.89309167e-08)*Ta*Ta*D_Tmrt*D_Tmrt*D_Tmrt*PA+ \
    (-4.79768731e-07)*ws*D_Tmrt*D_Tmrt*D_Tmrt*PA+ \
    (7.96079978e-09)*Ta*ws*D_Tmrt*D_Tmrt*D_Tmrt*PA+ \
    (1.62897058e-09)*ws*ws*D_Tmrt*D_Tmrt*D_Tmrt*PA+ \
    (3.94367674e-08)*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*PA+ \
    (-1.18566247e-09)*Ta*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*PA+ \
    (3.34678041e-10)*ws*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*PA+ \
    (-1.15606447e-10)*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*PA+ \
    (-2.80626406e+00)*PA*PA+ \
    (5.48712484e-01)*Ta*PA*PA+ \
    (-3.99428410e-03)*Ta*Ta*PA*PA+ \
    (-9.54009191e-04)*Ta*Ta*Ta*PA*PA+ \
    (1.93090978e-05)*Ta*Ta*Ta*Ta*PA*PA+ \
    (-3.08806365e-01)*ws*PA*PA+ \
    (1.16952364e-02)*Ta*ws*PA*PA+ \
    (4.95271903e-04)*Ta*Ta*ws*PA*PA+ \
    (-1.90710882e-05)*Ta*Ta*Ta*ws*PA*PA+ \
    (2.10787756e-03)*ws*ws*PA*PA+ \
    (-6.98445738e-04)*Ta*ws*ws*PA*PA+ \
    (2.30109073e-05)*Ta*Ta*ws*ws*PA*PA+ \
    (4.17856590e-04)*ws*ws*ws*PA*PA+ \
    (-1.27043871e-05)*Ta*ws*ws*ws*PA*PA+ \
    (-3.04620472e-06)*ws*ws*ws*ws*PA*PA+ \
    (5.14507424e-02)*D_Tmrt*PA*PA+ \
    (-4.32510997e-03)*Ta*D_Tmrt*PA*PA+ \
    (8.99281156e-05)*Ta*Ta*D_Tmrt*PA*PA+ \
    (-7.14663943e-07)*Ta*Ta*Ta*D_Tmrt*PA*PA+ \
    (-2.66016305e-04)*ws*D_Tmrt*PA*PA+ \
    (2.63789586e-04)*Ta*ws*D_Tmrt*PA*PA+ \
    (-7.01199003e-06)*Ta*Ta*ws*D_Tmrt*PA*PA+ \
    (-1.06823306e-04)*ws*ws*D_Tmrt*PA*PA+ \
    (3.61341136e-06)*Ta*ws*ws*D_Tmrt*PA*PA+ \
    (2.29748967e-07)*ws*ws*ws*D_Tmrt*PA*PA+ \
    (3.04788893e-04)*D_Tmrt*D_Tmrt*PA*PA+ \
    (-6.42070836e-05)*Ta*D_Tmrt*D_Tmrt*PA*PA+ \
    (1.16257971e-06)*Ta*Ta*D_Tmrt*D_Tmrt*PA*PA+ \
    (7.68023384e-06)*ws*D_Tmrt*D_Tmrt*PA*PA+ \
    (-5.47446896e-07)*Ta*ws*D_Tmrt*D_Tmrt*PA*PA+ \
    (-3.59937910e-08)*ws*ws*D_Tmrt*D_Tmrt*PA*PA+ \
    (-4.36497725e-06)*D_Tmrt*D_Tmrt*D_Tmrt*PA*PA+ \
    (1.68737969e-07)*Ta*D_Tmrt*D_Tmrt*D_Tmrt*PA*PA+ \
    (2.67489271e-08)*ws*D_Tmrt*D_Tmrt*D_Tmrt*PA*PA+ \
    (3.23926897e-09)*D_Tmrt*D_Tmrt*D_Tmrt*D_Tmrt*PA*PA+ \
    (-3.53874123e-02)*PA*PA*PA+ \
    (-2.21201190e-01)*Ta*PA*PA*PA+ \
    (1.55126038e-02)*Ta*Ta*PA*PA*PA+ \
    (-2.63917279e-04)*Ta*Ta*Ta*PA*PA*PA+ \
    (4.53433455e-02)*ws*PA*PA*PA+ \
    (-4.32943862e-03)*Ta*ws*PA*PA*PA+ \
    (1.45389826e-04)*Ta*Ta*ws*PA*PA*PA+ \
    (2.17508610e-04)*ws*ws*PA*PA*PA+ \
    (-6.66724702e-05)*Ta*ws*ws*PA*PA*PA+ \
    (3.33217140e-05)*ws*ws*ws*PA*PA*PA+ \
    (-2.26921615e-03)*D_Tmrt*PA*PA*PA+ \
    (3.80261982e-04)*Ta*D_Tmrt*PA*PA*PA+ \
    (-5.45314314e-09)*Ta*Ta*D_Tmrt*PA*PA*PA+ \
    (-7.96355448e-04)*ws*D_Tmrt*PA*PA*PA+ \
    (2.53458034e-05)*Ta*ws*D_Tmrt*PA*PA*PA+ \
    (-6.31223658e-06)*ws*ws*D_Tmrt*PA*PA*PA+ \
    (3.02122035e-04)*D_Tmrt*D_Tmrt*PA*PA*PA+ \
    (-4.77403547e-06)*Ta*D_Tmrt*D_Tmrt*PA*PA*PA+ \
    (1.73825715e-06)*ws*D_Tmrt*D_Tmrt*PA*PA*PA+ \
    (-4.09087898e-07)*D_Tmrt*D_Tmrt*D_Tmrt*PA*PA*PA+ \
    (6.14155345e-01)*PA*PA*PA*PA+ \
    (-6.16755931e-02)*Ta*PA*PA*PA*PA+ \
    (1.33374846e-03)*Ta*Ta*PA*PA*PA*PA+ \
    (3.55375387e-03)*ws*PA*PA*PA*PA+ \
    (-5.13027851e-04)*Ta*ws*PA*PA*PA*PA+ \
    (1.02449757e-04)*ws*ws*PA*PA*PA*PA+ \
    (-1.48526421e-03)*D_Tmrt*PA*PA*PA*PA+ \
    (-4.11469183e-05)*Ta*D_Tmrt*PA*PA*PA*PA+ \
    (-6.80434415e-06)*ws*D_Tmrt*PA*PA*PA*PA+ \
    (-9.77675906e-06)*D_Tmrt*D_Tmrt*PA*PA*PA*PA+ \
    (8.82773108e-02)*PA*PA*PA*PA*PA+ \
    (-3.01859306e-03)*Ta*PA*PA*PA*PA*PA+ \
    (1.04452989e-03)*ws*PA*PA*PA*PA*PA+ \
    (2.47090539e-04)*D_Tmrt*PA*PA*PA*PA*PA+ \
    (1.48348065e-03)*PA*PA*PA*PA*PA*PA


    cat = UTCI_cat(utci)

    return {'utci': utci, 'cat': cat}



