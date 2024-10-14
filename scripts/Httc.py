import math


def httc(Ri, u, z, z0m, z0h, met, i):

    metTa0 = met['Ta'][i]
    metP0 = met['P'][i]

    rho = metP0 * 100 / 287.04 / (metTa0 + 273.15)

    # from Louis(1979)
    R = 0.74

    # checks: Mascart procedure not so good if these two conditions
    # are not met (i.e. z0m/z0h must be between 1 and 200)
    z0h = max(z0m / 200, z0h)
    mu = max(0., math.log(z0m/z0h))

    Cstarh = 3.2165 + 4.3431 * mu + 0.536 * (mu ** 2) - 0.0781 * (mu ** 3)
    ph = 0.5802 - 0.1571 * mu + 0.0327 * (mu ** 2) - 0.0026 * (mu ** 3)

    lnzz0m = math.log(z/z0m)
    lnzz0h = math.log(z/z0h)
    aa = (0.4 / lnzz0m) ** 2

    Ch = Cstarh * aa * 9.4 * (lnzz0m / lnzz0h) * ((z / z0h) ** ph)

    if Ri > 0:
        Fh = lnzz0m / lnzz0h * ((1. + 4.7 * Ri) ** (-2))
    else:
        Fh = lnzz0m / lnzz0h * (1. - 9.4 * Ri / (1. + Ch * (abs(Ri) ** 0.5)))

    httc_out = u * aa / R * Fh

    return {'httc': httc_out, 'Fh': Fh}
