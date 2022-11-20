#! /usr/bin/python3
import pandas as pd
import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory


model  =  pyo.ConcreteModel()

model.i = Set(initialize=['Nvl','Np','Ref'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94'], doc='Productos Finales')
#REsultado Winqsb de pinon comprobando
#G83
tranmezclag83=55.48230*159.4096 + 52.52652*26.4804+ 65.13049*114.11
mezcla83result = 300* 58.8912500199999
print(round(tranmezclag83,2))
print(round(mezcla83result,2))
#G90
tranmezclag90=55.48230*225.412 + 65.13049*559.6451
mezcla90result = 785.0571 * 62.3602269999997
print(round(tranmezclag90,1))
print(round(mezcla90result,1))
#rvp
#G83
tranmezclag83=0.61140*159.4096 + 0.03713*26.4804+ 0.02998*114.11
mezcla83result = 300* 0.617498832595756
print(round(tranmezclag83,2))
print(round(mezcla83result,2))

#azufre
#G83
tranmezclag83=0.61140*159.4096 + 0.03713*26.4804+ 0.02998*114.11
mezcla83result = 300* 0.617498832595756
print(round(tranmezclag83,2))
print(round(mezcla83result,2))
#---------------------------

#PARAMETROS

productosIntermedios = {
    'Nvl': {'Rendimiento': 0.04776, 'RBN': 55.48230, 'RVP': 0.61140, 'PAzufre': 64.72995, 'Densidad': 0.66703},
    'Np':  {'Rendimiento': 0.151957, 'RBN': 52.52652, 'RVP': 0.03713, 'PAzufre': 345.32027, 'Densidad': 0.74964},
    'Ref': {'Rendimiento': 0.82455, 'RBN': 65.13, 'RVP': 0.02998, 'PAzufre': 64.72995, 'Densidad': 0.78712}
}
productosFinales = {
    'G83' : {'RBNmin': 58.8912500199999, 'RVPmax': 0.617498832595756, 'Azufemax':1000, 'Densidadmin': 0.7200},
    'G90' : {'RBNmin': 61.3602269999997, 'RVPmax': 0.617498832595756, 'Azufemax':1000, 'Densidadmin': 0.7200},
    'G94' : {'RBNmin': 65.1304929200004, 'RVPmax': 0.617498832595756, 'Azufemax':1000, 'Densidadmin': 0.7200}
}
precioPF = {
  'G83': { 'price': 3300},
    'G90': {'price': 3500},
    'G94': {'price': 3746}
}
demandaPF = {
  'G83': { 'Min':0 , 'Max':'M'},
    'G90': {'Min':750, 'Max':'M'},
    'G94': {'Min':400, 'Max':'M'}
}
# display feed information
print(pd.DataFrame.from_dict(productosFinales).T)

model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13}, doc = 'Research Blending number producto i')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66703, 'Np':0.74964, 'Ref':0.78712}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.8912500199999, 'G90': 61.3602269999997, 'G94': 65.1304929200004 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617498832595756 ,'G90': 0.617498832595756 ,'G94': 0.617498832595756}, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.7200, 'G90':0.7200, 'G94':0.7200}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746}, doc = 'Precio Gaso83, Gaso90, Gaso94')


model.demandag = Param( model.j, initialize = {'G83': 0, 'G90':750, 'G94':400}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')
model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455}, doc = 'Rendimientos Nvl, Nvp, Ar')

#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, doc = 'gasolina j')
gx = model.gx
#RESTRICCINES

#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)
model.NvlMB = Constraint(expr = x['Nvl','G83'] + x['Nvl','G90'] + x['Nvl','G94'] <= model.rendimiento['Nvl']*model.Destil, doc = 'Balance de Materiales para la Nafta Virgen ligera')

model.NvpMB = Constraint(expr = x['Np','G83'] + x['Np','G90'] + x['Np','G94'] + model.Ar <= model.rendimiento['Np']*model.Destil, doc = 'Balance de Materiales para la Nafta Virgen Pesada')

model.Ref = Constraint(expr = x['Ref','G83'] + x['Ref','G90'] + x['Ref','G94'] <= model.rendimiento['Ref']*Ar, doc = 'Balance de Materiales para el Refromado')
#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) == Wg[j] 
  
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad


def rbn_rule(model, j):
  return sum(model.Rbn[i]*x[i,j] for i in model.i) >= model.RbnPf[j] * gx[j]
  
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

def ipvr_rule(model, j):
  return sum(model.Ipvr[i]*x[i,j] for i in model.i) >= model.IpvrF[j] * gx[j]
  
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')
#
def pazufre_rule(model, j):
  return   sum(model.PAzufre[i]*x[i,j] for i in model.i) >= model.PAzufreF[j] * gx[j]
model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')


#gasolina j
model.g83 = Constraint(expr = x['Nvl','G83'] + x['Np','G83'] + x['Ref','G83'] == gx['G83'], doc = 'Gasolina 83')
model.g90 = Constraint(expr = x['Nvl','G90'] + x['Np','G90'] + x['Ref','G90'] == gx['G90'], doc = 'Gasolina 90')
model.g94 = Constraint(expr = x['Nvl','G94'] + x['Np','G90'] + x['Ref','G94'] == gx['G94'], doc = 'Gasolina 94')

#demanda
def demanda_rule (model, j) :
  return  model.gx[j] >= model.demandag[j]
model.demanda = Constraint(model.j,  rule = demanda_rule, doc = 'Restriccion para las demandas')
model.demanda.pprint()
#FUNCION OBJETIVO
def obj_rule(model):
  return sum( model.preciog[j]*gx[j] for j in model.j )
model.obj = Objective(expr = obj_rule, sense = maximize,doc = 'funcion objetivo')

# resolvemos el problema e imprimimos resultados
def pyomo_postprocess(options=None, instance=None, results=None):
    gx.display()

# utilizamos solver glpk
opt = SolverFactory("glpk")
resultados = opt.solve(model)

# imprimimos resultados
print("\nSolución óptima encontrada\n" + '-'*80)
pyomo_postprocess(None, None, resultados)
#instance.load(resultados) # Loading solution into results object
if (resultados.solver.status == SolverStatus.ok) and (resultados.solver.termination_condition == TerminationCondition.optimal):
  print(' Do something when the solution in optimal and feasible')
elif (resultados.solver.termination_condition == TerminationCondition.infeasible):
  print('Do something when model in infeasible')
else:
  # Something else is wrong
  print ('Solver Status: ',  resultados.solver.status)

