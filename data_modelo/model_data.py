from assay_data import data as ad  # relative import
# Este metodo se usa para calcular las caracteristicas reformadas m3d y tpd


def obtenerReformado(prodCarat1, prodCarat2):
    return prodCarat1 + prodCarat2

# Este metodo se usa para calcular las caracteristicas reformadas
# Densidad "gravedad especifica" (desidadProd1 * m3dProducto1 + desidadProd2 * m3dProducto2) / m3dReformado
# Azufre (azufreProd1 * tpdProd1 + azufreProd2 * tpdProd2) / tpdReformado
# RBN (rbnProd1 * m3dProd1 + rbnProd2 * m3dProd2) / m3dReformado
# IMPVR (IMPVRProd1 * m3dProducto1 + IMPVRProd2 * m3dProducto2) / m3dReformado
# volumen de nafta (naftaProd1 * m3dProducto1 + naftaProd2 * m3dProducto2) / m3dReformado
# Arom vol (aromProd1 * m3dProducto1 + aromProd2 * m3dProducto2) / m3dReformado


def sumaPonderada(caratTipo1Prod1, volumenProd1, caratTipo1Prod2, volumenProd2):
    return (caratTipo1Prod1 * volumenProd1 + caratTipo1Prod2 * volumenProd2) / (volumenProd1+volumenProd2)

# Indice lineal RBN to get RON


def obtenerRBNtoRON(rbnReformado):
    a = -1903.4286
    b = 101.70157
    c = -1.9829933
    d = 0.017595832
    e = -0.00005976918
    x = rbnReformado
    return a + b*x + (c * pow(x, 2)) + (d * pow(x, 3)) + (e * pow(x, 4))

# Indice lineal IMPVR to get RVP


def obtenerIMPVtoRVP(IMPVRRef):
    return pow(IMPVRRef, 0.82)

# nafta + 2* arom


def na(nafta, arom):
    return nafta + (2 * arom)


def boxc(ron, na):
    return 85.9485 + (0.230559 * na) + (-0.749819 * ron)


def c5(boxc):
    x = 21114.8614
    y = 0.33333333
    z = (boxc - 1) * x + 1
    return pow(z, y)


def obtenerRONtoRBN(ron):
    a = 285.24097
    b = -13.216411
    c = 0.27474217
    d = -0.00250797
    e = 0.00000868
    x = ron
    return a + b*x + (c * pow(x, 2)) + (d * pow(x, 3)) + (e * pow(x, 4))


def rvp(rvp):
    return rvp * 0.9


def imrvp(rvp):
    return pow(rvp, 1.25)


def azufre(azufre):
    a = 1.00072
    b = -0.0000244344
    c = 0.000000123264
    d = -0.00000000018195
    return azufre * (1 - (a + b * azufre + (c * pow(azufre, 2)) + (d * pow(azufre, 3))))


def densidad(dens):
    return dens * 1.05


def getNpMezclada(data):
    nvm = data.loc[1, :].values.tolist()
    nvp = data.loc[2, :].values.tolist()
    pesada = []
    pesada.append('Np')
    pesada.append(nvm[1] + nvp[1])
    pesada.append(nvm[2] + nvp[2])
    pesada.append(nvm[3] + nvp[3])
    pesada.append(sumaPonderada(nvm[4], nvm[1], nvp[4], nvp[1]))
    pesada.append(sumaPonderada(nvm[5], nvm[3], nvp[5], nvp[3]))
    rbn = sumaPonderada(nvm[7], nvm[1], nvp[7], nvp[1])
    ron = obtenerRBNtoRON(rbn)
    pesada.append(ron)
    pesada.append(rbn)
    impvr = sumaPonderada(nvm[9], nvm[1], nvp[9], nvp[1])
    rvp = obtenerIMPVtoRVP(impvr)
    pesada.append(rvp)
    pesada.append(impvr)
    pesada.append(sumaPonderada(nvm[10], nvm[1], nvp[10], nvp[1]))
    pesada.append(sumaPonderada(nvm[11], nvm[1], nvp[11], nvp[1]))
    data.loc[len(data.index)] = pesada
    return data


def getRendimientoReformado(data, ron):
    np = data.loc[3, :].values.tolist()
    reformda = {}
    nfa = na(np[10], np[11])
    rn = boxc(ron, nfa)
    rp = rvp(np[8])

    reformda['RON'] = ron
    reformda['N+2A'] = nfa
    reformda['boxc5+'] = rn
    reformda['C5+'] = round(c5(rn), 2)
    reformda['RBN'] = round(obtenerRONtoRBN(ron), 2)
    reformda['RVP'] = rp
    reformda['IMPVR'] = round(imrvp(rp), 4)
    reformda['Azufre'] = azufre(np[5])
    reformda['Dens'] = densidad(np[4])
    data.loc[len(data.index)] = ['Ref', reformda['C5+']/100, 0, 0, reformda['Dens'],
                                 reformda['Azufre'], ron, reformda['RBN'], rp, reformda['IMPVR'], 0, 0]
    return data


def setData(data):
    data = getNpMezclada(data)
    data = getRendimientoReformado(data, 94)
    return data


def getData(fc2, destil, crudos_precio):
    data = ad.datos(fc2, destil, crudos_precio)
    return setData(data)


if (__name__ == '__main__'):
    fc2 = 0.200
    destil = 8744
    crudos_precio = {'Ural': 2352.059*6.2898, 'Leona': 2303.83*6.2898}
    data = getData(fc2, destil, crudos_precio)
    print(data)
