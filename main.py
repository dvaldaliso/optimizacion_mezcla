#! /usr/bin/python3
import pandas as pd
import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory

#PARAMETROS

productosIntermedios = {
    'Nvl': {'Rendimiento': 0.04776, 'RBN': 55.48230, 'RVP': 0.61140, 'PAzufre': 64.72995, 'Densidad': 0.66703},
    'Np':  {'Rendimiento': 0.151957, 'RBN': 52.52652, 'RVP': 0.03713, 'PAzufre': 345.32027, 'Densidad': 0.74964},
    'Ref': {'Rendimiento': 0.82455, 'RBN': 65.13, 'RVP': 0.02998, 'PAzufre': 0.78492, 'Densidad': 0.78712}
}
productosFinales = {
    'G83' : {'price': 3300, 'RBNmin': 58.89, 'RVPmax': 0.617498832595756, 'Azufemax':1000, 'Densidadmin': 0.7200},
    'G90' : {'price': 3500, 'RBNmin': 62.36, 'RVPmax': 0.617498832595756, 'Azufemax':1000, 'Densidadmin': 0.7200},
    'G94' : {'price': 3746, 'RBNmin': 65.13, 'RVPmax': 0.617498832595756, 'Azufemax':1000, 'Densidadmin': 0.7200}
}

demandaPF = {
  'G83': { 'Min':0 , 'Max':'M'},
    'G90': {'Min':750, 'Max':'M'},
    'G94': {'Min':300, 'Max':'M'}
}

#model.a = Set(initialize=['Nim','NCraq'], doc='Productos Intermedios Importados')
model  =  pyo.ConcreteModel(name="(Mezclado de gasolina)")
model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT_EXPORT)
#Se puede hacer una union con model.i para tenerlos juntos y trabjarlos por separados en los casos que sea necesario
model.i = Set(initialize=['Nvl','Np','Ref'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94'], doc='Productos Finales')

#print(pd.DataFrame.from_dict(productosFinales).T)
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')

#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, doc = 'gasolina j')
gx = model.gx
x.display()
#RESTRICCIONES
#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)
model.NvlMB = Constraint(expr = x['Nvl','G83'] + x['Nvl','G90'] + x['Nvl','G94'] <= productosIntermedios['Nvl']['Rendimiento']*model.Destil, doc = 'Balance de Materiales para la Nafta Virgen ligera')

model.NvpMB = Constraint(expr = x['Np','G83'] + x['Np','G90'] + x['Np','G94'] + Ar <= productosIntermedios['Np']['Rendimiento']*model.Destil, doc = 'Balance de Materiales para la Nafta Virgen Pesada')

model.Ref = Constraint(expr = x['Ref','G83'] + x['Ref','G90'] + x['Ref','G94'] <= productosIntermedios['Ref']['Rendimiento']*Ar, doc = 'Balance de Materiales para el Refromado')

#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(productosIntermedios[i]['Densidad']*x[i,j] for i in model.i) == Wg[j]   
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#gasolina j
def gasolinaj_rule(model, j):
  return  sum(x[i,j] for i in model.i) == gx[j]   
model.gasolinaj = Constraint(model.j, rule = gasolinaj_rule, doc = 'Cambio de variable')


#calidad
model.calidad = ConstraintList()
for j in model.j:
    model.calidad.add(sum(x[i,j]*productosIntermedios[i]['RBN'] for i in model.i) -  productosFinales[j]['RBNmin']*gx[j] >= 0)
    model.calidad.add(sum(x[i,j]* productosIntermedios[i]['Densidad']  for i in model.i) -  productosFinales[j]['Densidadmin']*gx[j] >= 0)
    model.calidad.add(sum(x[i,j]*productosIntermedios[i]['RVP'] for i in model.i) - productosFinales[j]['RVPmax']*gx[j] <= 0)
    model.calidad.add(sum(x[i,j]*productosIntermedios[i]['PAzufre']   for i in model.i) -  productosFinales[j]['Azufemax']*gx[j]  <= 0)

#demanda
model.demanda = ConstraintList()
for j in model.j:
  if isinstance(demandaPF[j]['Min'], (int, float)):
    model.demanda.add(model.gx[j] >= demandaPF[j]['Min'])
  if isinstance(demandaPF[j]['Max'], (int, float)):
    model.demanda.add(model.gx[j] <= demandaPF[j]['Max'])  

#FUNCION OBJETIVO
def obj_rule(model):
  return sum( productosFinales[j]['price']*gx[j] for j in model.j )
model.obj = Objective(expr = obj_rule, sense = maximize,doc = 'funcion objetivo')

# resolvemos el problema e imprimimos resultados
def pyomo_postprocess(options=None, instance=None, results=None):
    Ar.display()
    gx.display()
    x.display()

# utilizamos solver glpk
opt = SolverFactory("glpk")

resultados = opt.solve(model)

#resultados.write()

# imprimimos resultados
print("\nSolución óptima encontrada\n" + '-'*80)
pyomo_postprocess(None, None, resultados)
if (resultados.solver.status == SolverStatus.ok) and (resultados.solver.termination_condition == TerminationCondition.optimal):
  print(' Do something when the solution in optimal and feasible')
  # display results
  vol = sum(x[i,j]() for i in model.i for j in model.j)
  #print("Total Profit =", round(model.obj(), 1), "dollars.")
  #print("Total Volume =", round(vol, 1), "m3/d.")
  #print("Profit =", round(100*model.obj()/vol,1), "cents por m3/d.")
  stream_results = pd.DataFrame()

  for i in model.i:
    for j in model.j:
        stream_results.loc[i,j] = round(x[i,j](), 1)
    stream_results.loc[i,'Total'] = round(sum(x[i,j]() for j in model.j), 1)
    if i=='Ref':
      stream_results.loc[i,'Available'] = round(productosIntermedios[i]['Rendimiento']*value(Ar), 1)
    elif i=='Np':
      np=productosIntermedios[i]['Rendimiento']*value(model.Destil)
      stream_results.loc[i,'Available'] = round(np-value(Ar), 1)
    else:
       stream_results.loc[i,'Available'] = round(productosIntermedios[i]['Rendimiento']*value(model.Destil), 1)

  stream_results['Unused (Slack)'] = stream_results['Available'] - stream_results['Total']
  print(stream_results)

elif (resultados.solver.termination_condition == TerminationCondition.infeasible):
  print('Do something when model in infeasible')
else:
  # Something else is wrong
  print ('Solver Status: ',  resultados.solver.status)

#dual
#Restricciones
# display all duals
print ("Duals costo reducido")
for c in model.component_objects(pyo.Constraint, active=True):
    print ("   Constraint",c)
    for index in c:
        print ("      ", index, model.dual[c[index]])




