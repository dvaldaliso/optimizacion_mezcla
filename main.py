#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory

N  =  3 # i
M  =  3 # j

model  =  pyo.ConcreteModel()
#SET O RANGOS
#model.i  =  RangeSet(N)   #producto intermedio 'Nvl','Np','Ref'
#model.j  =  RangeSet(M)   #producto final 'G83', 'G90', 'G94

model.i = Set(initialize=['Nvl','Np','Ref'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94'], doc='Productos Finales')


#PARAMETROS

model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13049}, doc = 'Research Blending number producto i ')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66, 'Np':0.749, 'Ref':0.787}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.89125002, 'G90': 62.360227, 'G94': 65.13049292 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617 ,'G90': 0.617 ,'G94': 0.617}, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.72, 'G90':0.72, 'G94':0.72}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746}, doc = 'Precio Gaso83, Gaso90, Gaso94')


model.demandag = Param( model.j, initialize = {'G83': 300, 'G90':300, 'G94':0}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')
model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455}, doc = 'Rendimientos Nvl, Nvp, Ar')

#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1045), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, doc = 'gasolina j')
gx = model.gx
#RESTRICCINES

#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)
model.NvlMB = Constraint(expr = x['Nvl','G83'] + x['Nvl','G90'] <= model.rendimiento['Nvl']*model.Destil, doc = 'Balance de Materiales para la Nafta Virgen ligera')

model.NvpMB = Constraint(expr = x['Np','G83'] + x['Np','G90'] + model.Ar <= model.rendimiento['Np']*model.Destil, doc = 'Balance de Materiales para la Nafta Virgen Pesada')

model.Ref = Constraint(expr = x['Ref','G83'] + x['Ref','G90'] + x['Ref','G94'] <= model.rendimiento['Ref']*Ar, doc = 'Balance de Materiales para el Refromado')
#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  if j != 'G94':
    return  sum(model.densidad[i]*x[i,j] for i in model.i) == Wg[j] 
  return model.densidad['Ref']*x['Ref','G94'] == Wg[j] 
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
def rbn_rule(model, j):
  if j != 'G94':
    return sum(model.Rbn[i]*x[i,j] for i in model.i) >= model.RbnPf[j]*gx[j] 
  return model.Rbn['Ref']*x['Ref','G94'] >= model.RbnPf[j]*gx[j]
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

def ipvr_rule(model, j):
  if j != 'G94':
    return sum(model.Ipvr[i]*x[i,j] for i in model.i) >= model.IpvrF[j]*gx[j] 
  return model.Ipvr['Ref']*x['Ref','G94'] >= model.IpvrF[j]*gx[j] 
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

def pazufre_rule(model, j):
  if j != 'G94':
    return   sum(model.PAzufre[i]*x[i,j] for i in model.i) >= model.PAzufreF[j]*gx[j]  
  return model.PAzufre['Ref']*x['Ref','G94'] >= model.PAzufreF[j]*gx[j] 
model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')

model.rbn.pprint()
#gasolina j
model.g83 = Constraint(expr = x['Nvl','G83'] + x['Np','G83'] + x['Ref','G83'] == gx['G83'], doc = 'Gasolina 83')
model.g90 = Constraint(expr = x['Nvl','G90'] + x['Np','G90'] + x['Ref','G90'] == gx['G90'], doc = 'Gasolina 90')
model.g94 = Constraint(expr = x['Ref','G94'] == gx['G94'], doc = 'Gasolina 94')

#demanda
def demanda_rule (model, j) :
  return  model.gx[j] >= model.demandag[j]
model.demanda = Constraint(model.j,  rule = demanda_rule, doc = 'Restriccion para las demandas')

#FUNCION OBJETIVO
def obj_rule(model):
  return sum( model.preciog[j]*gx[j] for j in model.j )
model.obj = Objective(expr = obj_rule, sense = maximize,doc = 'funcion objetivo')

# resolvemos el problema e imprimimos resultados
def pyomo_postprocess(options=None, instance=None, results=None):
    x.display()

# utilizamos solver glpk
opt = SolverFactory("glpk")
resultados = opt.solve(model)

# imprimimos resultados
print("\nSolución óptima encontrada\n" + '-'*80)
pyomo_postprocess(None, None, resultados)

