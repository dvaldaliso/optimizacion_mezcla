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
    # Calidad
    for j in pFin:
        if j != 'Nex':
            model.add_constraint(model.sum(x[i, j]*pIntC[i]['RBN']
                                           for i in pInt) - pFinC[j]['RBNmin']*gx[j] >= 0, ctname='Calidad Octano '+j)
            model.add_constraint(model.sum(x[i, j]*pIntC[i]['Densidad']
                                           for i in pInt) - pFinC[j]['Densidadmin']*gx[j] >= 0, ctname='Calidad Densidad '+j)
            model.add_constraint(model.sum(x[i, j]*pIntC[i]['IMPVR']
                                           for i in pInt) - pFinC[j]['IMPVRmax']*gx[j] <= 0, ctname='Calidad Presion de vapor '+j)
            model.add_constraint(model.sum(x[i, j]*pIntC[i]['PAzufre']
                                           for i in pInt) - pFinC[j]['Azufemax']*gx[j] <= 0, ctname='Calidad Azufre'+j)

    # Demanda
    for j in pFin:
        if isinstance(demandaPF[j]['Min'], (int, float)):
            model.add_constraint(gx[j] >= demandaPF[j]
                                 ['Min'], ctname='Demanda por Min '+j)
        if isinstance(demandaPF[j]['Max'], (int, float)):
            model.add_constraint(gx[j] <= demandaPF[j]
                                 ['Max'], ctname='Demanda por Max '+j)

    # Funcion Objetivo
    ganancia_neta = model.sum(pFinC[j]['price']*gx[j] for j in pFin)
    model.set_objective("Max", ganancia_neta)
    solucion = model.solve()

    if solucion is None:
        print("!! Error al resolver el modelo")
        print(model.export_to_string())
        return -1
    assert solucion, "Solve failed"+str(model.get_solve_status())

    # model.print_information()
    # model.report()
    model.print_solution()

    result = {}
    result['solucion'] = [v.name.split(
        '_') + [solucion.get_value(v)] for v in model.iter_variables()]

    cantLin = 30

    # Holgura
    n_cons = model.number_of_constraints
    const = [model.get_constraint_by_index(i) for i in range(n_cons)]
    lhs_model = [model.get_constraint_by_index(i).lhs for i in range(n_cons)]
    h = model.slack_values(const)
    # La variable no negativa s1 es la holgura (o cantidad no utilizada) del recurso M1
    # La cantidad de S1 representa el exceso de toneladas de la mezcla sobre el mínimo requerido
    print('-'*cantLin+'Holguras'+'-'*cantLin)

    result_holguras = {}
    for n in range(n_cons):
        result_holguras[const[n].lp_name] = h[n]
    # print(result_holguras)

    # Precios duales o sombra
    # El nombre valor unitario de un recurso es una descripción adecuada de la
    # tasa de cambio de la función objetivo por unidad de cambio de un recurso.
    # función objetivo por unidad de cambio de un recurso. No obstante, los primeros
    # desarrollos de LP acuñaron el nombre abstracto de precio dual (o sombra)
    print('-'*cantLin+'Precios Duales'+'-'*cantLin)
    precios_duales = model.dual_values(const)
    result_duales = {}
    for n in range(n_cons):
        result_duales[const[n].lp_name] = precios_duales[n]

    # Analisis de sensibilidad
    # El análisis de sensibilidad, que trata de determinar las condiciones que mantendrán inalterada la solución actual.
    # Rangos en que el modelo es factible
    cpx = model.get_engine().get_cplex()
    of = cpx.solution.sensitivity.objective()
    b = cpx.solution.sensitivity.rhs()

    # Sensibilidad de la solución óptima a los cambios en la disponibilidad de los recursos
    # (lado derecho de las restricciones)
    print('-'*cantLin+'Costo reducido'+'-'*cantLin)
    var_list = [model.get_var_by_index(i) for i in range(len(x))]
    result_costos_reducidos = {}
    for n in range(len(var_list)):
        result_costos_reducidos[str(var_list[n])] = var_list[n].reduced_cost

    # Sensibilidad de la solución óptima a las variaciones del beneficio unitario o del coste unitario
    # (coeficientes de la función objetivo)
    print('-'*cantLin+'SENSIBILIDAD FO'+'-'*cantLin)
    result_sensibilidad_FO = {}
    for n in range(len(var_list)):
        result_sensibilidad_FO[var_list[n]] = of[n]

    print('-'*cantLin+'SENSIBILIDAD LADO DERECHO'+'-'*cantLin)
    result_rango_duales = {}
    for n in range(n_cons):
        result_rango_duales[const[n].lp_name] = {
            str(precios_duales[n]): str(b[n])}
    return result

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
