#from sympy import solve, Eq, Symbol


error_return = -9999
iterations = 900000

def converge(dz, ref_ta, UTb, mod_U_TaRef, i, Ri_rur):
    lowRiRur = False
    previousValue = 0
    testValue = 15

    if Ri_rur < -400:
        testValue = 17.0
        lowRiRur = True
    elif Ri_rur < -200:
        testValue = 22.0
        lowRiRur = True
    elif Ri_rur < -50:
        testValue = 20.0
        lowRiRur = True
    elif Ri_rur < -44:
        testValue = 17.4
        lowRiRur = True
    elif Ri_rur < -37:
        testValue = 17.9
        lowRiRur = True
    elif Ri_rur < -34:
        testValue = 18.0
        lowRiRur = True
    elif Ri_rur < -28:
        testValue = 19.0
        lowRiRur = True
    elif Ri_rur < -23:
        testValue = 19.0
        lowRiRur = True
    elif Ri_rur < -20:
        testValue = 20.0
        lowRiRur = True

    count = 0
    while count < iterations:
        returnValue = calculateExpression(dz, ref_ta, UTb, mod_U_TaRef[i], Ri_rur, testValue)
        scale = abs(returnValue/testValue)
        previousValueDifference = returnValue - previousValue
        scaleIncrement = 0.01
        if previousValueDifference < 0:
            scale = scale * -1
        if lowRiRur:
            testValue = getAlternativeIncrement(returnValue, testValue, scaleIncrement, Ri_rur)
        else:
            testValue = testValue - (1.0 * scale)

        if abs(returnValue) < 1.0e-12:
            break
        if count == iterations - 1:
            if lowRiRur and abs(returnValue) < 1.0e-2:
                break
            testValue = error_return
            break
        count += 1

        return testValue

def convergeNewVersion(dz, ref_ta, UTb, mod_U_TaRef, i, Ri_rur):
    lowestNegativeTestResult = -99999.
    lowestPositiveTestResult = 99999.
    previousNegativeTestValue = 0
    previousPositiveTestValue = 100
    testValue = 18.0
    converged = False

    count = 0
    while count < iterations:
        testValue = (previousNegativeTestValue + previousPositiveTestValue) / 2
        count += 1

        returnValue = calculateExpression(dz, ref_ta, UTb, mod_U_TaRef[i], Ri_rur, testValue)
        if abs(returnValue) < 10 ** (-12):
            converged = True
            break

        testValueDifference = previousNegativeTestValue - previousPositiveTestValue
        if returnValue < 0:
            if returnValue > lowestNegativeTestResult:
                lowestNegativeTestResult = returnValue
                previousNegativeTestValue = testValue
            else:
                previousNegativeTestValue = previousNegativeTestValue - testValueDifference / 1.000000001
        else:
            if returnValue < lowestPositiveTestResult:
                lowestPositiveTestResult = returnValue
                previousPositiveTestValue = testValue
            else:
                previousPositiveTestValue = previousPositiveTestValue + testValueDifference / 1.000000001
    # print('result=' + str(testValue) + " iterations=" + str(count))
    if converged:
        return testValue
    else:
        print('Error result='+str(testValue)+" iterations="+str(count))
        return(converge(dz, ref_ta, UTb, mod_U_TaRef, i, Ri_rur))


def getAlternativeIncrement(returnValue, testValue, scaleIncrement, Ri_rur):
    absReturnValue = abs(returnValue)

    if Ri_rur > -50:
        if returnValue > 0:
            scaleIncrement = scaleIncrement * -1
        if absReturnValue > 10:
            newTestValue = testValue + scaleIncrement
        elif absReturnValue > 5:
            newTestValue = testValue + scaleIncrement * 0.5
        elif absReturnValue > 2.5:
            newTestValue = testValue + scaleIncrement * 0.25
        elif absReturnValue > 1:
            newTestValue = testValue + scaleIncrement * 0.25 * 0.5
        elif absReturnValue > 0.1:
            newTestValue = testValue + scaleIncrement * 0.25 * 0.5 * 0.5 * 0.5
        elif absReturnValue > 0.001:
            newTestValue = testValue + scaleIncrement * 0.000001
        else:
            newTestValue = testValue + scaleIncrement * 0.00000001
        return newTestValue

    if Ri_rur > -500:
        if returnValue > 0:
            scaleIncrement = scaleIncrement * -1
        if absReturnValue > 10:
            newTestValue = testValue + scaleIncrement
        elif absReturnValue > 5:
            newTestValue = testValue + scaleIncrement * 0.5
        elif absReturnValue > 2.5:
            newTestValue = testValue + scaleIncrement * 0.25
        elif absReturnValue > 1:
            newTestValue = testValue + scaleIncrement * 0.001
        elif absReturnValue > 0.1:
            newTestValue = testValue + scaleIncrement * 0.00001
        elif absReturnValue > 0.001:
            newTestValue = testValue + scaleIncrement * 0.0000001
        else:
            newTestValue = testValue + scaleIncrement * 0.000000001
        return newTestValue

    if returnValue > 0:
        scaleIncrement = scaleIncrement * -1

    if absReturnValue > 10:
        newTestValue = testValue + scaleIncrement
    elif absReturnValue > 5:
        newTestValue = testValue + scaleIncrement * 0.5
    elif absReturnValue > 2.5:
        newTestValue = testValue + scaleIncrement * 0.25
    elif absReturnValue > 1:
        newTestValue = testValue + scaleIncrement * 0.25 * 0.5
    elif absReturnValue > 0.1:
        newTestValue = testValue + scaleIncrement * 0.25 * 0.5 * 0.5 * 0.5
    elif absReturnValue > 0.001:
        newTestValue = testValue + scaleIncrement * 0.0000001
    else:
        newTestValue = testValue + scaleIncrement * 0.0000000001
    return  newTestValue

def calculateExpression(dz, ref_ta, UTb, mod_U_TaRef, Ri_rur, Thi_tb):
    expressionValue = 9.806 * dz * (Thi_tb - ref_ta) * 2 / (Thi_tb + ref_ta) / ((UTb - mod_U_TaRef) ** 2) - Ri_rur
    return expressionValue


#def pythonsolver(dz, ref_ta, UTb, mod_U_TaRef, i, Ri_rur):
#    Thi_tb = Symbol('Thi_tb')
#    Tb_rur = solve(9.806 * dz * (Thi_tb - ref_ta) * 2.0 / (Thi_tb + ref_ta) / (UTb - mod_U_TaRef[i]) ** 2.0 - Ri_rur,
#                   Thi_tb)[0]
#    return Tb_rur