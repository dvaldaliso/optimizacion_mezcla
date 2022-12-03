
from docplex.mp.model import Model

# Datos y Estructuras
pInt = {'Nvl', 'Np', 'Ref'}
pFin = {'G83', 'G90', 'G94'}
# productos Intermedios caracterisiticas
pIntC = {
    'Nvl': {'Rendimiento': 0.04776, 'RBN': 55.48230, 'RVP': 0.61140, 'PAzufre': 64.72995, 'Densidad': 0.66703},
    'Np':  {'Rendimiento': 0.151957, 'RBN': 52.52652, 'RVP': 0.03713, 'PAzufre': 345.32027, 'Densidad': 0.74964},
    'Ref': {'Rendimiento': 0.82455, 'RBN': 65.13, 'RVP': 0.02998, 'PAzufre': 0.78492, 'Densidad': 0.78712}
}
# productos Finales caracterisiticas
pFinC = {
    'G83': {'price': 3300, 'RBNmin': 58.89, 'RVPmax': 0.617498832595756, 'Azufemax': 1000, 'Densidadmin': 0.7200},
    'G90': {'price': 3500, 'RBNmin': 62.36, 'RVPmax': 0.617498832595756, 'Azufemax': 1000, 'Densidadmin': 0.7200},
    'G94': {'price': 3746, 'RBNmin': 65.13, 'RVPmax': 0.617498832595756, 'Azufemax': 1000, 'Densidadmin': 0.7200}
}

demandaPF = {
    'G83': {'Min': 0, 'Max': 'M'},
    'G90': {'Min': 750, 'Max': 'M'},
    'G94': {'Min': 300, 'Max': 'M'}
}
Destil = 8744
model = Model(name='Mezcla de Gasolina')
transferencias = [(i, j) for i in pInt for j in pFin]

x = model.continuous_var_dict(transferencias, name='x', lb=0)
ar = model.continuous_var(name='Alimentacion al reformador', lb=0, ub=1526)
gx = model.continuous_var_dict(pFin, name='gasolina final', lb=0)

# Balance de materiales (Lo que se extrae de los productos intermedios no sobrepasara la existencia)
model.add_constraint(x[('Nvl', 'G83')] + x[('Nvl', 'G90')] + x[('Nvl', 'G94')]
                     <= pIntC['Nvl']['Rendimiento'] * Destil, ctname='Nafta Virgen Ligera')
model.add_constraint(x[('Np', 'G83')] + x[('Np', 'G90')] + x[('Np', 'G94')] +
                     ar <= pIntC['Np']['Rendimiento'] * Destil, ctname='Nafta Virgen Pesada')
model.add_constraint(x[('Ref', 'G83')] + x[('Ref', 'G90')] + x[('Ref', 'G94')]
                     <= pIntC['Ref']['Rendimiento'] * ar, ctname='Reformador')

# gasolinaj
for j in pFin:
    model.add_constraint(model.sum(x[(i, j)] for i in pInt) == gx[j])

# Calidad
for j in pFin:
    model.add_constraint(model.sum(x[(i, j)]*pIntC[i]['RBN']
                         for i in pInt) - pFinC[j]['RBNmin']*gx[j] >= 0)
    model.add_constraint(model.sum(x[(i, j)]*pIntC[i]['Densidad']
                                   for i in pInt) - pFinC[j]['Densidadmin']*gx[j] >= 0)
    model.add_constraint(model.sum(x[(i, j)]*pIntC[i]['RVP']
                                   for i in pInt) - pFinC[j]['RVPmax']*gx[j] <= 0)
    model.add_constraint(model.sum(x[(i, j)]*pIntC[i]['PAzufre']
                                   for i in pInt) - pFinC[j]['Azufemax']*gx[j] <= 0)

# Demanda
for j in pFin:
    if isinstance(demandaPF[j]['Min'], (int, float)):
        model.add_constraint(model.sum(x[(i, j)]
                             for i in pInt) >= demandaPF[j]['Min'])
    if isinstance(demandaPF[j]['Max'], (int, float)):
        model.add_constraint(model.sum(x[(i, j)]
                             for i in pInt) <= demandaPF[j]['Max'])

# Funcion Objetivo
model.set_objective("Max", model.sum(pFinC[j]['price']*gx[j] for j in pFin))
print(model.export_to_string())
model.print_information()
model.solve()
print(model.solve_details)

model.print_solution()
