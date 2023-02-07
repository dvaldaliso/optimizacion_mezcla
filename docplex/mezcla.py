from model_externo import *
import model_data as md
from docplex.mp.model import Model
import pandas as pd


def run(pInt, pFin, pIntC, pFinC, demandaPF, Destil):

    model = Model(name='Mezcla de Gasolina')

    # transferencias = [(i, j) for i in pInt for j in pFin]
    # x = model.continuous_var_dict(transferencias, name='x', lb=0)

    x = model.continuous_var_matrix(
        keys1=pInt, keys2=pFin, lb=0, name='X')
    ar = model.continuous_var(name='Alimentacion al reformador', lb=0, ub=1526)
    gx = model.continuous_var_dict(pFin, name='gasolina final', lb=0)

    # Balance de materiales (Lo que se extrae de los productos intermedios no sobrepasara la existencia)
    # flujos
    model.add_constraint(x['Nvl', '83'] + x['Nvl', '90'] + x['Nvl', '94'] + x['Nvl', 'Nex']
                         <= pIntC['Nvl']['Rendimiento'] * Destil, ctname='MB Nafta Virgen Ligera')
    model.add_constraint(x['Np', '83'] + x['Np', '90'] + x['Np', '94'] +
                         ar <= pIntC['Np']['Rendimiento'] * Destil, ctname='MB Nafta Virgen Pesada')
    # Reformador o Pool
    model.add_constraint(x['Ref', '83'] + x['Ref', '90'] + x['Ref', '94']
                         <= pIntC['Ref']['Rendimiento'] * ar, ctname='MB Reformador')
    # Productos importados
    model.add_constraint(x['Ni', '83'] + x['Ni', '90'] + x['Ni', '94'] + x['Ni', 'Nex']
                         <= pIntC['Ni']['Rendimiento'], ctname='MB Nafta Importada')
    model.add_constraint(x['Ncraq', '83'] + x['Ncraq', '90'] + x['Ncraq', '94'] + x['Ncraq', 'Nex']
                         <= pIntC['Ncraq']['Rendimiento'], ctname='MB Nafta Craqueda')

    # gasolinaj
    for j in pFin:
        if j != 'Nex':
            model.add_constraint(model.sum(x[i, j]
                                           for i in pInt) == gx[j], ctname='Gasolina '+j)
    model.add_constraint(x['Nvl', 'Nex']+x['Ni', 'Nex'] +
                         x['Ncraq', 'Nex'] == gx['Nex'], ctname='Nafta exceso')

    densidad = ''
    # Calidad
    for j in pFin:
        if j != 'Nex':
            model.add_constraint(model.sum(x[i, j]*pIntC[i]['RBN']
                                           for i in pInt) - pFinC[j]['RBNmin']*gx[j] >= 0, ctname='Calidad Octano min '+j)
            densidad = model.add_constraint(model.sum(x[i, j]*pIntC[i]['Densidad']
                                                      for i in pInt) - pFinC[j]['Densidadmin']*gx[j] >= 0, ctname='Calidad Densidad min'+j)
            model.add_constraint(model.sum(x[i, j]*pIntC[i]['IMPVR']
                                           for i in pInt) - pFinC[j]['IMPVRmax']*gx[j] <= 0, ctname='Calidad Presion de vapor max '+j)
            model.add_constraint(model.sum(x[i, j]*pIntC[i]['PAzufre']
                                           for i in pInt) - pFinC[j]['Azufemax']*gx[j] <= 0, ctname='Calidad Azufre max'+j)

    # Demanda
    for j in pFin:
        if isinstance(demandaPF[j]['Min'], (int, float)):
            model.add_constraint(gx[j] >= demandaPF[j]
                                 ['Min'], ctname='Demanda por Min '+j)
        if isinstance(demandaPF[j]['Max'], (int, float)):
            model.add_constraint(gx[j] <= demandaPF[j]
                                 ['Max'], ctname='Demanda por Max '+j)

    # Funcion Objetivo
    def pintsum(j):
        pIntaux = pInt
        if j == 'Nex':
            pIntaux = {'Nvl', 'Ni', 'Ncraq'}
        return sum(x[i, j] for i in pIntaux)

    ganancia_neta = model.sum(pFinC[j]['price'] * pintsum(j) for j in pFin)

    model.set_objective("Max", ganancia_neta)

    solucion = model.solve()

    if solucion is None:
        print("!! Error al resolver el modelo")
        print(model.export_to_string())
        return -1
    assert solucion, "Solve failed"+str(model.get_solve_status())
    model.print_information()
    model.report()
    model.print_solution()

    cantLin = 30
    dens_coefi = getCoeficientes(densidad, cantLin)

    result = resultDic(solucion, model)

    # Numero Restricciones
    n_cons = model.number_of_constraints
    # Lista de restriccinoes
    const = [model.get_constraint_by_index(i) for i in range(n_cons)]

    h = model.slack_values(const)
    # La variable no negativa s1 es la holgura (o cantidad no utilizada) del recurso M1
    # La cantidad de S1 representa el exceso de toneladas de la mezcla sobre el mínimo requerido

    restricciones_lhs = restriccionesLhs(model, n_cons)

    result_holguras = holgura(n_cons, const, h, cantLin)

    # Precios duales o sombra
    # El nombre valor unitario de un recurso es una descripción adecuada de la
    # tasa de cambio de la función objetivo por unidad de cambio de un recurso.
    # función objetivo por unidad de cambio de un recurso. No obstante, los primeros
    # desarrollos de LP acuñaron el nombre abstracto de precio dual (o sombra)

    precios_duales, valor_duales = preciosDuales(model, const, n_cons, cantLin)
    df = pd.DataFrame(precios_duales)
    print(df)

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

    var_list = [model.get_var_by_index(i) for i in range(len(x)+len(gx)+1)]
    result_costos_reducidos, costos_reducidos = costosReducidos(
        var_list, cantLin)

    # Sensibilidad de la solución óptima a las variaciones del beneficio unitario o del coste unitario
    # (coeficientes de la función objetivo)

    result_sensibilidad_FO = sensibilidad_FO(
        var_list, of, costos_reducidos, cantLin)

    sensibilidad_rhs = sensibilidadRHS(n_cons, b, valor_duales, const, cantLin)

    result_bounds = ubSensibilidad(n_cons, const, ub, cantLin)

    return result


def getCoeficientes(densidad, cantLin):
    print('-'*cantLin+'Coeficientes'+'-'*cantLin)
    nombre_var = []
    coeficiente = []
    for v in densidad.iter_variables():
        nombre_var.append(v)
        coeficiente.append(densidad.lhs.get_coef(v))
    return {'nombre': nombre_var, 'valor': coeficiente}


def resultDic(solucion, model):
    result = {}
    result['solucion'] = [v.name.split(
        '_') + [solucion.get_value(v)] for v in model.iter_variables()]
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


def sensibilidadRHS(n_cons, b, valor_duales, const, cantLin):
    print('-'*cantLin+'SENSIBILIDAD LADO DERECHO'+'-'*cantLin)
    name_rango_ladoDerecho = []
    valor_rango_ladoDerecho = []
    for n in range(n_cons):
        name_rango_ladoDerecho.append(const[n].lp_name)
        valor_rango_ladoDerecho.append(str(b[n]))
    return {"nombre": name_rango_ladoDerecho, 'duales': valor_duales, "valor": valor_rango_ladoDerecho}


def sensibilidad_FO(var_list, of, costos_reducidos, cantLin):
    print('-'*cantLin+'SENSIBILIDAD FO'+'-'*cantLin)
    name_sensibilidad_FO = []
    valor_sensibilidad_FO = []
    for n in range(len(var_list)):
        name_sensibilidad_FO.append(var_list[n])
        valor_sensibilidad_FO.append(of[n])
    return {"nombre": name_sensibilidad_FO, "costo_reducido": costos_reducidos, "valor": valor_sensibilidad_FO}


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


def holgura(n_cons, const, h, cantLin):
    print('-'*cantLin+'Holguras'+'-'*cantLin)
    name_holgura = []
    valor_holgura = []
    for n in range(n_cons):
        name_holgura.append(const[n].lp_name)
        valor_holgura.append(h[n])
    # load data into a DataFrame object:
    return {"nombre": name_holgura, "valor": valor_holgura}


def matriz_optima(model):
    print('-----Matriz Soluction Optima-----------')
    cp = model.get_cplex()

    for fila in cp.solution.advanced.binvarow():
        print(fila)
    print('-'*8)
    for fila in cp.solution.advanced.binvrow():
        print(fila)

    # Análisis postóptimo, que trata de encontrar una nueva solución óptima cuando cambian los datos del modelo.
if (__name__ == '__main__'):

    # Datos y Estructuras
    pInt = {'Nvl', 'Np', 'Ref', 'Ni', 'Ncraq'}
    pFin = {'83', '90', '94', 'Nex'}
    # productos Intermedios caracterisiticas
    pIntC = {
        'Nvl': {'Rendimiento': 0.04776, 'RBN': 55.48230, 'IMPVR': 0.61140, 'PAzufre': 64.72995, 'Densidad': 0.66703},
        'Np':  {'Rendimiento': 0.151957, 'RBN': 52.52652, 'IMPVR': 0.03713, 'PAzufre': 345.32027, 'Densidad': 0.74964},
        'Ref': {'Rendimiento': 0.82455, 'RBN': 65.13, 'IMPVR': 0.02998, 'PAzufre': 0.78492, 'Densidad': 0.78712},
        'Ni': {'Rendimiento': 0, 'RBN': 0, 'IMPVR': 0, 'PAzufre': 0, 'Densidad': 0},
        'Ncraq': {'Rendimiento': 0, 'RBN': 0, 'IMPVR': 0, 'PAzufre': 0, 'Densidad': 0}
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
