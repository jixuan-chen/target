import math


def cd(Ri, z, z0m, z0h):
    z0h = max(z0m / 200., z0h)
    mu = max(0., math.log(z0m/z0h))

    Cstarm = 6.8741 + 2.6933 * mu - 0.3601 * mu ** 2 + 0.0154 * mu ** 3
    pm = 0.5233 - 0.0815 * mu + 0.0135 * mu ** 2 - 0.001 * mu ** 3

    lnzz0m = math.log(z/z0m)
    aa = (0.4/lnzz0m) ** 2

    Cm = Cstarm * aa * 9.4 * (z/z0m) ** pm

    if Ri > 0:
        Fm = (1. + 4.7 * Ri) ** (-2)
    else:
        Fm = 1. - 9.4 * Ri / (1. + Cm * abs(Ri) ** 0.5)

    cd_out = aa * Fm

    return {'cd_out': cd_out, 'Fm': Fm}