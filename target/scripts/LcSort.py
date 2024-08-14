def lc_sort(cs, LC, H, W):
    # LC = [lc_data['roof'][grid], lc_data['road'][grid], lc_data['watr'][grid], lc_data['conc'][grid],
          # lc_data['Veg'][grid], lc_data['dry'][grid], lc_data['irr'][grid]]
    LC_canyon = LC[:]

    res = W*sum(LC)/(sum(LC) - LC[0])
    # res = cs['res']

    if W < 1.0:
        W = 1.0

    tree_area = res ** 2 * LC[4]
    tree_width = tree_area / res

    Wtree = W - tree_width

    if Wtree <= 1.0:
        Wtree = 1.0
    if H <= 1.5:
        H = 1.5

    LCgrndSum = LC[1] + LC[2] + LC[3] + LC[5] + LC[6]

    if LCgrndSum > 0:
        LC[1] = LC[1] + (LC[1] / LCgrndSum * LC[4])
        LC[2] = LC[2] + (LC[2] / LCgrndSum * LC[4])
        LC[3] = LC[3] + (LC[3] / LCgrndSum * LC[4])
        LC[5] = LC[5] + (LC[5] / LCgrndSum * LC[4])
        LC[6] = LC[6] + (LC[6] / LCgrndSum * LC[4])
    else:
        LC[3] = LC[3] + LC[4]

    LC_woRoofAvg = LC[:]

    f_roof = LC[0]
    if f_roof == 0:
        f_roof = 0.000000001
    f_wall = 2 * (H / W) * (1 - f_roof)
    f_roof_tree = f_roof / (1 - LC[4])
    f_wall_tree = 2 * (H / W) * (1 - f_roof)/ (1 - LC[4])

    H2W = (f_roof * f_wall) / (2 * f_roof * (1 - f_roof))
    H2W_tree = (f_roof_tree * f_wall_tree) / (2 * f_roof_tree * (1 - f_roof_tree))

    svfgA = (1 + (H2W_tree) ** 2) ** 0.5 - H2W_tree
    svfwA = 1/2 * (1 + 1/H2W - (1 + ((1/H2W) ** 2)) ** 0.5)

    # svfgA = (1 + (H / Wtree) ** 2) ** 0.5 - H / Wtree
    # svfwA = 1 / 2 * (1 + W / H - (1 + ((W / H) ** 2)) ** 0.5)

    wall_area = 2 * (H/W) * (1 - LC[0])

    LC_woRoofAvgN = LC[:]
    LC_wRoofAvg = LC[:]

    LC.append(wall_area)

    if LC_woRoofAvgN[0] <= 0.99:
        LC_woRoofAvgN[0] = 0

    LC_woRoofAvgNSum = sumSurfaces(LC_woRoofAvgN)
    if LC_woRoofAvgNSum != 0:
        value = LC_woRoofAvgN[1]
        LC_woRoofAvgN[1] = value / LC_woRoofAvgNSum

        value = LC_woRoofAvgN[2]
        LC_woRoofAvgN[2] = value / LC_woRoofAvgNSum

        value = LC_woRoofAvgN[3]
        LC_woRoofAvgN[3] = value / LC_woRoofAvgNSum

        value = LC_woRoofAvgN[4]
        LC_woRoofAvgN[4] = value / LC_woRoofAvgNSum

        value = LC_woRoofAvgN[5]
        LC_woRoofAvgN[5] = value / LC_woRoofAvgNSum

        value = LC_woRoofAvgN[6]
        LC_woRoofAvgN[6] = value / LC_woRoofAvgNSum

    LC_woRoofAvgN.append(wall_area)

    LC_wRoofAvgSum = sumSurfaces(LC_wRoofAvg)
    if LC_wRoofAvgSum != 0:
        value = LC_wRoofAvg[0]
        LC_wRoofAvg[0] = value / LC_wRoofAvgSum

        value = LC_wRoofAvg[1]
        LC_wRoofAvg[1] = value / LC_wRoofAvgSum

        value = LC_wRoofAvg[2]
        LC_wRoofAvg[2] = value / LC_wRoofAvgSum

        value = LC_wRoofAvg[3]
        LC_wRoofAvg[3] = value / LC_wRoofAvgSum

        value = LC_wRoofAvg[4]
        LC_wRoofAvg[4] = value / LC_wRoofAvgSum

        value = LC_wRoofAvg[5]
        LC_wRoofAvg[5] = value / LC_wRoofAvgSum

        value = LC_wRoofAvg[6]
        LC_wRoofAvg[6] = value / LC_wRoofAvgSum

    fg = 0
    fw = 0

    if svfgA < 0.1:
        fg = 0
    if 0.1 < svfgA <= 0.2:
        fg = 1
    if 0.2 < svfgA <= 0.3:
        fg = 2
    if 0.3 < svfgA <= 0.4:
        fg = 3
    if 0.4 < svfgA <= 0.5:
        fg = 4
    if 0.5 < svfgA <= 0.6:
        fg = 5
    if 0.6 < svfgA <= 0.7:
        fg = 6
    if 0.7 < svfgA <= 0.8:
        fg = 7
    if 0.8 < svfgA <= 0.9:
        fg = 8
    if svfgA > 0.9:
        fg = 9

    if svfwA < 0.1:
        fw = 0
    if 0.1 < svfwA <= 0.2:
        fw = 1
    if 0.2 < svfwA <= 0.3:
        fw = 2
    if 0.3 < svfwA <= 0.4:
        fw = 3
    if 0.4 < svfwA <= 0.5:
        fw = 4
    if 0.5 < svfwA <= 0.6:
        fw = 5
    if 0.6 < svfwA <= 0.7:
        fw = 6
    if 0.7 < svfwA <= 0.8:
        fw = 7
    if 0.8 < svfwA <= 0.9:
        fw = 8
    if svfwA > 0.9:
        fw = 9

    return {'LC': LC, 'LC_woRoofAvg': LC_woRoofAvg, 'LC_woRoofAvgN': LC_woRoofAvgN, 'LC_wRoofAvg': LC_wRoofAvg,
            'H': H, 'W': W, 'Wtree': Wtree, 'fw': fw, 'fg':fg, 'svfwA': svfwA, 'svfgA': svfgA}


def sumSurfaces(lc_data):
    roofArea = lc_data[0]
    LCSum = lc_data[1] + lc_data[2] + lc_data[3] + lc_data[4] + lc_data[5] + lc_data[6] + roofArea

    return LCSum