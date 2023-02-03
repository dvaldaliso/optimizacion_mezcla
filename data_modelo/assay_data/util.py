import pandas as pd


def getTonDia(tablaCrudo, data):
    c1 = tablaCrudo['m3/d'][0]*data.values[2][1]
    c2 = tablaCrudo['m3/d'][1]*data.values[2][2]
    return [round(c1, 2), round(c2, 2), round(c1+c2, 2)]


def getFaccpeso(tablaCrudo):
    c1 = tablaCrudo['Ton/Dia'][0]
    c2 = tablaCrudo['Ton/Dia'][1]
    tc = tablaCrudo['Ton/Dia'][2]

    return [round(c1/tc, 3), round(c2/tc, 3), round(c1/tc, 3) + round(c2/tc, 3)]


def getPrecio(crudoPrecio, tablaCrudo):
    c1 = tablaCrudo['Fraccion Vol'][0]*crudoPrecio['Ural']
    c2 = tablaCrudo['Fraccion Vol'][1]*crudoPrecio['Leona']
    return [round(crudoPrecio['Ural'], 3), round(crudoPrecio['Leona'], 3), round(c1 + c2, 3)]


def dfTodict(df):
    return df.T.to_dict().values()

# Tabla Crudo


def getTablaCrudo(fc2, destil, crudos_precio, data):
    fc1 = 1-fc2
    tablaCrudo = {'Crudos': {}, 'Fraccion Vol': {}, 'Fraccion peso': {
    }, 'Precio $/m3': {}, 'm3/d': {}, "Ton/Dia": {}}

    tablaCrudo = pd.DataFrame(tablaCrudo)
    nombreCrudo = ['Ural', 'Leona', 'Total']
    fraccionVol = [fc1, fc2, 1]
    m3d = [destil*fc1, destil*fc2, destil*fc1+destil*fc2]

    tablaCrudo['Crudos'] = nombreCrudo
    tablaCrudo['Fraccion Vol'] = fraccionVol
    tablaCrudo['m3/d'] = m3d

    tablaCrudo['Ton/Dia'] = getTonDia(tablaCrudo, data)
    tablaCrudo['Fraccion peso'] = getFaccpeso(tablaCrudo)
    tablaCrudo['Precio $/m3'] = getPrecio(crudos_precio, tablaCrudo)
    return tablaCrudo

# Mezcla Crudo


def setDataMezcla(mezclaCrudo, tablaCrudo):
    fP = tablaCrudo['Fraccion peso'][:-1]
    fV = tablaCrudo['Fraccion Vol'][:-1]

    posPeso = [1, 26, 27, 28, 42, 43, 44, 101, 102, 103]
    posVol = [93, 94, 95, 113, 114, 115, 133, 134, 135, 138, 139, 140]
    dat = {}
    for x in posPeso:
        item = mezclaCrudo.loc[x, :].values.tolist()[1:]
        dat[x] = sum(item[i]*fP[i] for i in range(len(item)))
        dat[x] = round(dat[x], 4)

    for x in posVol:
        item = mezclaCrudo.loc[x, :].values.tolist()[1:]
        dat[x] = sum(item[i]*fV[i] for i in range(len(item)))
        dat[x] = round(dat[x], 4)

    posNaftaVol = [10, 11, 12]
    i = 0
    for x in posNaftaVol:
        LnPeso = dat[posPeso[1+i]]
        CalSpecGrav = dat[posPeso[0]]
        SpecifiGravi = dat[posPeso[4+i]]
        valor = (LnPeso*CalSpecGrav)/SpecifiGravi
        dat[x] = valor
        i = i+1
    return dat


def getDataMezcla(values, tablaCrudo):
    dataArray = values
    mezclaCrudo = pd.DataFrame(dataArray[1:], columns=dataArray[0])
    mezclaCrudo['mezcla'] = setDataMezcla(mezclaCrudo, tablaCrudo)
    return mezclaCrudo
# Obtencion de Prodctos Intermedios


def getMetCubDia(mezclaCrudo, destil):
    nvl = mezclaCrudo['mezcla'][10]*destil
    nvm = mezclaCrudo['mezcla'][11]*destil
    nvp = mezclaCrudo['mezcla'][12]*destil
    return [nvl, nvm, nvp]


def getRendimiento(mezclaCrudo):
    nvl = mezclaCrudo['mezcla'][10]
    nvm = mezclaCrudo['mezcla'][11]
    nvp = mezclaCrudo['mezcla'][12]
    return [nvl, nvm, nvp]


def getDesTonMetrCub(mezclaCrudo):
    nvl = mezclaCrudo['mezcla'][42]
    nvm = mezclaCrudo['mezcla'][43]
    nvp = mezclaCrudo['mezcla'][44]
    return [nvl, nvm, nvp]


def getTPD(tablaPIntermedios):
    result = {}
    for i in range(len(tablaPIntermedios['PI'])):
        metrCub = tablaPIntermedios['m3/d'][i]
        densidad = tablaPIntermedios['Dens, TON/M3'][i]
        result[i] = metrCub/6.2898*densidad
    return result


def getRON(mezclaCrudo):
    nvl = mezclaCrudo['mezcla'][113]
    nvm = mezclaCrudo['mezcla'][114]
    nvp = mezclaCrudo['mezcla'][115]
    rnvl = getRONToRBN(nvl)
    rnvm = getRONToRBN(nvm)
    rnvp = getRONToRBN(nvp)
    return [nvl, nvm, nvp], [rnvl, rnvm, rnvp]


def getRVP(mezclaCrudo):
    nvl = mezclaCrudo['mezcla'][93]/14.6959
    nvm = mezclaCrudo['mezcla'][94]/14.6959
    nvp = mezclaCrudo['mezcla'][95]/14.6959
    invl = getRvpToImpvr(nvl)
    invm = getRvpToImpvr(nvm)
    invp = getRvpToImpvr(nvp)
    return [nvl, nvm, nvp], [invl, invm, invp]


def getAzufre(mezclaCrudo):
    nvl = mezclaCrudo['mezcla'][101]*10000
    nvm = mezclaCrudo['mezcla'][102]*10000
    nvp = mezclaCrudo['mezcla'][103]*10000
    return [nvl, nvm, nvp]


def getNAFT(mezclaCrudo):
    nvl = mezclaCrudo['mezcla'][133]
    nvm = mezclaCrudo['mezcla'][134]
    nvp = mezclaCrudo['mezcla'][135]
    return [nvl, nvm, nvp]


def getArom(mezclaCrudo):
    nvl = mezclaCrudo['mezcla'][138]
    nvm = mezclaCrudo['mezcla'][139]
    nvp = mezclaCrudo['mezcla'][140]
    return [nvl, nvm, nvp]


def getRONToRBN(x):
    a = 285.24097
    b = -13.216411
    c = 0.27474217
    d = -0.00250797
    e = 0.00000868
    return a + b*x + (c*pow(x, 2)) + (d*pow(x, 3)) + (e*pow(x, 4))


def getRvpToImpvr(x):
    return pow(x, 1.25)


def getDataPI(mezclaCrudo, destil):
    tablaPIntermedios = {
        'PI': {}, 'Rendimiento': {}, 'm3/d': {},  'TPD': {}, 'Dens, TON/M3': {}, 'Azufre, PPM': {}, 'RON': {}, 'RBN': {}, "RVP, atm": {}, 'IMPVR': {}, 'Naft. % Vol': {}, 'Arom. %Vol': {}
    }
    tablaPIntermedios = pd.DataFrame(tablaPIntermedios)
    tablaPIntermedios['PI'] = ['NVL', 'NVM', 'NVP']
    tablaPIntermedios['m3/d'] = getMetCubDia(mezclaCrudo, destil)
    tablaPIntermedios['Rendimiento'] = getRendimiento(mezclaCrudo)
    tablaPIntermedios['Dens, TON/M3'] = getDesTonMetrCub(mezclaCrudo)
    tablaPIntermedios['Azufre, PPM'] = getAzufre(mezclaCrudo)
    tablaPIntermedios['TPD'] = getTPD(tablaPIntermedios)
    tablaPIntermedios['RON'], tablaPIntermedios['RBN'] = getRON(mezclaCrudo)
    tablaPIntermedios['RVP, atm'], tablaPIntermedios['IMPVR'] = getRVP(
        mezclaCrudo)
    tablaPIntermedios['Naft. % Vol'] = getNAFT(mezclaCrudo)
    tablaPIntermedios['Arom. %Vol'] = getArom(mezclaCrudo)

    return tablaPIntermedios
