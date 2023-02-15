from model_externo import *
import model_data as md
from docplex.mp.model import Model
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sympy as sym

path_excel = r'/media/desarrollo/datos/Matemática Aplicada/tesis/Tesis Mezcaldo gasolina/Tesis versiones/Agregado/Analisando resultados/resultado.xlsx'


def run(pInt, pFin, pIntC, pFinC, demandaPF, Destil):

    model = Model(name='Mezcla de Gasolina')

    # transferencias = [(i, j) for i in pInt for j in pFin]
    # x = model.continuous_var_dict(transferencias, name='x', lb=0)

    x = model.continuous_var_matrix(
        keys1=pInt, keys2=pFin, lb=0, name='X')

    ar = model.continuous_var(name='Alimentacion al reformador', lb=0, ub=1526)
    #gx = model.continuous_var_dict(pFin, name='gasolina final', lb=0)

    # Balance de materiales (Lo que se extrae de los productos intermedios no sobrepasara la existencia)
    # flujos
    mbNvl = model.add_constraint(x['Nvl', '83'] + x['Nvl', '90'] + x['Nvl', '94'] + x['Nvl', 'Nex']
                                 <= pIntC['Nvl']['Rendimiento'] * Destil, ctname='MB Nafta Virgen Ligera')
    mbNp = model.add_constraint(x['Np', '83'] + x['Np', '90'] + x['Np', '94'] +
                                ar <= pIntC['Np']['Rendimiento'] * Destil, ctname='MB Nafta Virgen Pesada')

    # Reformador o Pool salida
    mbReformada = model.add_constraint(x['Ref', '83'] + x['Ref', '90'] + x['Ref', '94']
                                       <= pIntC['Ref']['Rendimiento'] * ar, ctname='MB Reformador')
    # Productos importados
    mbNi = model.add_constraint(x['Ni', '83'] + x['Ni', '90'] + x['Ni', '94'] + x['Ni', 'Nex']
                                <= pIntC['Ni']['Rendimiento'], ctname='MB Nafta Importada')
    mbNcraq = model.add_constraint(x['Ncraq', '83'] + x['Ncraq', '90'] + x['Ncraq', '94'] + x['Ncraq', 'Nex']
                                   <= pIntC['Ncraq']['Rendimiento'], ctname='MB Nafta Craqueda')
    # gasolinaj
    # for j in pFin:
    #    if j != 'Nex':
    #        model.add_constraint(model.sum(x[i, j]
    #                                       for i in pInt) == gx[j], ctname='Gasolina '+j)
    # model.add_constraint(x['Nvl', 'Nex']+x['Ni', 'Nex'] +
    #                     x['Ncraq', 'Nex'] == gx['Nex'], ctname='Nafta exceso')

    densidad = {}
    octano = {}
    RVP = {}
    Azufre = {}
    # Calidad
    for j in pFin:
        if j != 'Nex':
            octano[j] = model.add_constraint(model.sum(x[i, j]*pIntC[i]['RBN']
                                                       for i in pInt) >= pFinC[j]['RBNmin']*pintsum(x, j), ctname='Calidad Octano min '+j)
            densidad[j] = model.add_constraint(model.sum(x[i, j]*pIntC[i]['Densidad']
                                                         for i in pInt) >= pFinC[j]['Densidadmin']*pintsum(x, j), ctname='Calidad Densidad min'+j)
            RVP[j] = model.add_constraint(model.sum(x[i, j]*pIntC[i]['IMPVR']
                                                    for i in pInt) <= pFinC[j]['IMPVRmax']*pintsum(x, j), ctname='Calidad Presion de vapor max '+j)
            Azufre[j] = model.add_constraint(model.sum(x[i, j]*pIntC[i]['PAzufre']
                                                       for i in pInt) <= pFinC[j]['Azufemax']*wgasolina(x, j), ctname='Calidad Azufre max'+j)

    # Demanda
    demanda = {}
    for j in pFin:
        if isinstance(demandaPF[j]['Min'], (int, float)):
            demanda[j+'Min'] = model.add_constraint(pintsum(x, j) >= demandaPF[j]
                                                    ['Min'], ctname='Demanda por Min '+j)
        if isinstance(demandaPF[j]['Max'], (int, float)):
            demanda[j+'Max'] = model.add_constraint(pintsum(x, j) <= demandaPF[j]
                                                    ['Max'], ctname='Demanda por Max '+j)
    print(demanda)
    # Funcion Objetivo

    ganancia = model.sum(pFinC[j]['price'] * pintsum(x, j) for j in pFin)
    # Costos de todo lo que va de los productos intermedios a final mas lo que va de Np a reformador
    costo = model.sum(pintsum(x, j, True)
                      for j in pFin) + ar*pIntC['Np']['costo']
    print(ganancia)
    #ganancia = ganancia-costo
    model.set_objective("Max", ganancia)

    solucion = model.solve()

    if solucion is None:
        print("!! Error al resolver el modelo")
        print(model.export_to_string())
        return -1
    assert solucion, "Fallo la solucion "+str(model.get_solve_status())

    model.print_information()
    model.report()
    model.print_solution()

    cantLin = 30
    dens_coefi = getCoeficientes(densidad, cantLin)

    result = resultDic(solucion, model, True)
    result_list = resultDic(solucion, model, False)

    # Numero Restricciones
    n_cons = model.number_of_constraints
    # Lista de restricciones
    const = [model.get_constraint_by_index(i) for i in range(n_cons)]

    # La variable no negativa s1 es la holgura (o cantidad no utilizada) del recurso M1
    # La cantidad de S1 representa el exceso de toneladas de la mezcla sobre el mínimo requerido

    restricciones_lhs = restriccionesLhs(model, n_cons)

    result_holguras = holgura(n_cons, const, model, cantLin)
    df = pd.DataFrame(result_holguras)
    df.to_excel(path_excel, index=False)

    # Precios duales o sombra
    # El nombre valor unitario de un recurso es una descripción adecuada de la
    # tasa de cambio de la función objetivo por unidad de cambio de un recurso.
    # función objetivo por unidad de cambio de un recurso. No obstante, los primeros
    # desarrollos de LP acuñaron el nombre abstracto de precio dual (o sombra)

    precios_duales, valor_duales = preciosDuales(model, const, n_cons, cantLin)
    df_p = pd.DataFrame(precios_duales)
    #df_p.to_excel(path_excel, sheet_name='Precios duales', index=False)
    # Analisis de sensibilidad

    # El análisis de sensibilidad, que trata de determinar las condiciones que mantendrán inalterada
    # la solución actual(Cuando se dice solucion actual es le valor de las variables no el de la funcion objetivo).

    # Rangos en que el modelo es factible
    cpx = model.get_engine().get_cplex()
    of = cpx.solution.sensitivity.objective()
    b = cpx.solution.sensitivity.rhs()
    lb = cpx.solution.sensitivity.lower_bounds()
    ub = cpx.solution.sensitivity.upper_bounds()
    bounds = cpx.solution.sensitivity.bounds()
    names = cpx.linear_constraints.get_names()
    indexConstraint = names.index("MB Reformador")
    print("right info for the constraint ", b[indexConstraint])
    # Sensibilidad de la solución óptima a los cambios en la disponibilidad de los recursos
    # (lado derecho de las restricciones)

    var_list = [model.get_var_by_index(i) for i in range(len(x))]
    result_costos_reducidos, costos_reducidos = costosReducidos(
        var_list, cantLin)
    df_cr = pd.DataFrame(result_costos_reducidos)
    # Sensibilidad de la solución óptima a las variaciones del beneficio unitario o del coste unitario
    # (coeficientes de la función objetivo)

    result_sensibilidad_FO = sensibilidad_FO(
        var_list, of, costos_reducidos, cantLin, result_list[: -1], ganancia)
    df_senFO = pd.DataFrame(result_sensibilidad_FO)

    sensibilidad_rhs, rhsVal = sensibilidadRHS(
        n_cons, b, valor_duales, const, model, cantLin)
    df_senRHS = pd.DataFrame(sensibilidad_rhs)

    result_bounds = ubSensibilidad(n_cons, const, ub, cantLin)
    df_bounds = pd.DataFrame(result_bounds)
    with pd.ExcelWriter(path_excel) as writer:
        df.to_excel(writer, sheet_name='holgura')
        df_p.to_excel(writer, sheet_name='precios duales')
        df_cr.to_excel(writer, sheet_name='Costos reducidos')
        df_senFO.to_excel(writer, sheet_name='SensibilidadFo')
        df_senRHS.to_excel(writer, sheet_name='SensibilidadRHS')
        df_bounds.to_excel(writer, sheet_name='Bounds')
    graficarResult(result)
    #matriz_optima(model, rhsVal)
    return result


def pintsum(x, j, costo=False):
    pIntaux = pInt
    if j == 'Nex':
        pIntaux = {'Nvl', 'Ni', 'Ncraq'}
    if costo:
        return sum(pIntC[i]['costo']*x[i, j] for i in pIntaux)
    return sum(x[i, j] for i in pIntaux)


def wgasolina(x, j):
    pIntaux = pInt
    if j == 'Nex':
        pIntaux = {'Nvl', 'Ni', 'Ncraq'}
    return sum(x[i, j] for i in pIntaux)


def getResult(resultado):
    result = {'Nvl': [], 'Np': [], 'Ref': [], 'Ni': [], 'Ncraq': []}
    for index in result:
        for x in resultado['solucion']:
            if index not in x:
                continue
            if x[2] == '83':
                result[index].insert(0, round(x[3], 2))
            if x[2] == '90':
                result[index].insert(1, round(x[3], 2))
            if x[2] == '94':
                result[index].insert(2, round(x[3], 2))
            if x[2] == 'Nex':
                result[index].insert(3, round(x[3], 2))
    return result


def graficarResult(result):
    # set width of bars
    barWidth = 0.20
    resultData = getResult(result)
    # set heights of bars
    Nvl = resultData['Nvl']
    Np = resultData['Np']
    Ref = resultData['Ref']
    Ni = resultData['Ni']
    Ncraq = resultData['Ncraq']
    bart = Nvl+Np+Ref+Ni+Ncraq

    # Set position of bar on X axis
    r1 = np.arange(len(Nvl))
    r2 = [x + barWidth for x in r1]
    r3 = [x + barWidth for x in r2]
    r4 = [x + barWidth for x in r3]
    r5 = [x + barWidth for x in r4]
    r6 = np.concatenate((r1, r2, r3, r4, r5), axis=None)

    # Make the plot
    plt.bar(r1, Nvl, color='#7f6d5f', width=barWidth,
            edgecolor='white', label='Nafta Virgen Ligera')
    plt.bar(r2, Np, color='#557f2d', width=barWidth,
            edgecolor='white', label='Nafta Pesada')
    plt.bar(r3, Ref, color='#2d7f5e', width=barWidth,
            edgecolor='white', label='Reformada')
    plt.bar(r4, Ni, color='lightgreen', width=barWidth,
            edgecolor='white', label='Nafta Importada')
    plt.bar(r5, Ncraq, color='cadetblue', width=barWidth,
            edgecolor='white', label='Nafta Craqueada')

    # Text on the top of each bar
    for i in range(len(r6)):
        plt.text(x=r6[i]-0.10, y=bart[i]+0.1, s=bart[i]
                 if bart[i] != 0 else '', size=10)
    # Add xticks on the middle of the group bars
    plt.xlabel('Gasolinas', fontweight='bold')
    plt.ylabel("Mezcla")
    plt.xticks([r + barWidth for r in range(len(Nvl))],
               ['83', '90', '94', 'Nexe'])

    # Create legend & Show graphic
    plt.legend()
    plt.show()


def getCoeficientesOBJ(obj):
    coeficientes = []
    for v in obj.iter_variables():
        coeficientes.append(obj.get_coef(v))
    return coeficientes


def getCoeficientes(densidad, cantLin):
    print('-'*cantLin+'Coeficientes'+'-'*cantLin)
    nombre_var = []
    coeficiente = []
    for v in densidad['94'].iter_variables():
        nombre_var.append(v)
        coeficiente.append(densidad['94'].lhs.get_coef(v))
    return {'nombre': nombre_var, 'valor': coeficiente}


def resultDic(solucion, model, como_diccionario):
    if como_diccionario == True:
        result = {}
        result['solucion'] = [v.name.split(
            '_') + [solucion.get_value(v)] for v in model.iter_variables()]
        return result
    result = []
    for v in model.iter_variables():
        result.append(solucion.get_value(v))
    return result


def restriccionesLhs(model, n_cons):
    lhs_model = [model.get_constraint_by_index(i).lhs for i in range(n_cons)]
    restricciones = []
    for n in range(len(lhs_model)):
        restricciones.append(lhs_model[n])
    return {'lado derecho': restricciones}


def ubSensibilidad(n_cons, const, ub, cantLin):
    print('-'*cantLin+'SENSIBILIDAD ub'+'-'*cantLin)
    name_bounds = []
    valor_bounds = []
    for n in range(n_cons-1):
        name_bounds.append(const[n].lp_name)
        valor_bounds.append(str(ub[n]))
    return {"nombre": name_bounds, "valor": valor_bounds}


def sensibilidadRHS(n_cons, b, valor_duales, const, model, cantLin):
    print('-'*cantLin+'SENSIBILIDAD LADO DERECHO'+'-'*cantLin)
    name_rango_ladoDerecho = []
    valor_rango_ladoDerecho = []
    rhs = []
    for n in range(n_cons):
        name_rango_ladoDerecho.append(const[n].lp_name)
        valor_rango_ladoDerecho.append(str(b[n]))
        rhs.append(model.get_constraint_by_name(const[n].lp_name).rhs)
    return {"nombre": name_rango_ladoDerecho, 'duales': valor_duales, "RHS": rhs, "valor": valor_rango_ladoDerecho}, rhs


def sensibilidad_FO(var_list, of, costos_reducidos, cantLin, result_list, obj):
    print('-'*cantLin+'SENSIBILIDAD FO'+'-'*cantLin)
    name_sensibilidad_FO = []
    valor_sensibilidad_FO = []
    coeficientes = []
    for n in range(len(var_list)):
        name_sensibilidad_FO.append(var_list[n])
        valor_sensibilidad_FO.append(of[n])
        coeficientes.append(obj.get_coef(var_list[n]))

    return {"nombre": name_sensibilidad_FO, 'FinalValor': result_list,  "costoReducido": costos_reducidos, 'OBJcoeficientes': coeficientes, "rango": valor_sensibilidad_FO}


def costosReducidos(var_list, cantLin):
    print('-'*cantLin+'Costo reducido'+'-'*cantLin)
    name_costos_reducidos = []
    valor_costos_reducidos = []
    for n in range(len(var_list)):
        name_costos_reducidos.append(str(var_list[n]))
        valor_costos_reducidos.append(var_list[n].reduced_cost)
    return {"nombre": name_costos_reducidos, "valor": valor_costos_reducidos}, valor_costos_reducidos


def preciosDuales(model, const, n_cons, cantLin):
    print('-'*cantLin+'Precios Duales'+'-'*cantLin)
    precios_duales = model.dual_values(const)
    name_duales = []
    valor_duales = []
    for n in range(n_cons):
        name_duales.append(const[n].lp_name)
        valor_duales.append(precios_duales[n])
    return {"nombre": name_duales, "valor": valor_duales}, valor_duales


def holgura(n_cons, const, model, cantLin):
    print('-'*cantLin+'Holguras'+'-'*cantLin)
    h = model.slack_values(const)
    name_holgura = []
    valor_holgura = []
    for n in range(n_cons):
        name_holgura.append(const[n].lp_name)
        valor_holgura.append(h[n])
    # load data into a DataFrame object:
    return {"nombre": name_holgura, "valor": valor_holgura}


def matriz_optima(model, rhsval):
    print('-----Matriz Soluction Optima-----------')
    cp = model.get_cplex()
    print('B inversa * A'+'-'*8)
    BInversaPorA = np.array(cp.solution.advanced.binvarow())
    print('B inversa * b'+'-'*8)
    BInversaPorb = np.array(cp.solution.advanced.binvrow())
    x = sym.symbols('x')
    rhsval[2] = x
    c = BInversaPorb@rhsval
    print(c)

    # Análisis postóptimo, que trata de encontrar una nueva solución óptima cuando cambian los datos del modelo.
if (__name__ == '__main__'):

    # Datos y Estructuras
    pInt = {'Nvl', 'Np', 'Ref', 'Ni', 'Ncraq'}
    pFin = {'83', '90', '94', 'Nex'}
    # productos Intermedios caracterisiticas
    pIntC = {
        'Nvl': {'costo': 704.25, 'Rendimiento': 0.04776, 'RBN': 55.48230, 'IMPVR': 0.61140, 'PAzufre': 64.72995, 'Densidad': 0.66703},
        'Np':  {'costo': 2239.46, 'Rendimiento': 0.151957, 'RBN': 52.52652, 'IMPVR': 0.03713, 'PAzufre': 345.32027, 'Densidad': 0.74964},
        'Ref': {'costo': 197.4284, 'Rendimiento': 0.82455, 'RBN': 65.13, 'IMPVR': 0.02998, 'PAzufre': 0.78492, 'Densidad': 0.78712},
        'Ni': {'costo': 13754.56, 'Rendimiento': 0, 'RBN': 0, 'IMPVR': 0, 'PAzufre': 0, 'Densidad': 0},
        'Ncraq': {'costo': 23437.54, 'Rendimiento': 0, 'RBN': 0, 'IMPVR': 0, 'PAzufre': 0, 'Densidad': 0}
    }
    # traer datos del Assat
    fc2 = 0.200
    destil = 8744
    crudos_precio = {'Ural': 2352.059*6.2898, 'Leona': 2303.83*6.2898}
    data = md.getData(fc2, destil, crudos_precio)
    importados = {'PI': ['Ni', 'Ncraq'],
                  'Rendimiento': [0, 0],
                  'RBN': [0, 0],
                  'IMPVR': [0, 0],
                  'PAzufre': [0, 0],
                  'Densidad': [0, 0,]
                  }
    importadosdf = pd.DataFrame(importados)

    data = pd.concat([data, importadosdf], ignore_index=True)
    data = data.set_index('PI')
    data.rename(index={"NVL": "Nvl"},
                inplace=True)
    #pIntC = data.T.to_dict()
    # productos Finales caracterisiticas
    pFinC = {
        '83': {'price': 22371, 'RBNmin': 58.89, 'IMPVRmax': 0.617498832595756, 'Azufemax': 1000, 'Densidadmin': 0.7200},
        '90': {'price': 23438, 'RBNmin': 62.36, 'IMPVRmax': 0.617498832595756, 'Azufemax': 1000, 'Densidadmin': 0.7200},
        '94': {'price': 23971, 'RBNmin': 65.13, 'IMPVRmax': 0.617498832595756, 'Azufemax': 1000, 'Densidadmin': 0.7200},
        'Nex': {'price': 13755}
    }

    demandaPF = {
        '83': {'Min': 0, 'Max': 300},
        '90': {'Min': 750, 'Max': 'M'},
        '94': {'Min': 400, 'Max': 'M'},
        'Nex': {'Min': 0, 'Max': 'M'},
    }
    Destil = 8744
    run(pInt, pFin, pIntC, pFinC, demandaPF, Destil)
