#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory

N  =  3 # i
M  =  3 # j

model  =  pyo.ConcreteModel()
#SET O RANGOS
model.i  =  RangeSet(N)   #producto intermedio
model.j  =  RangeSet(M)   #producto final

#model.i = Set(initialize=['Nvl','Np','Ref'], doc='Productos Intermedios')
#model.j = Set(initialize=['G83', 'G90', 'G94'], doc='Productos Finales')


#PARAMETROS
model.RbnPf = Param(model.j, initialize = {1: 58.89125002, 2: 62.360227, 3: 65.13049292}, doc = 'Limite de Research Blending Number producto final j')
model.Rbn = Param(model.i, initialize = {1: 55.48230,2: 52.52652, 3: 65.13049}, doc = 'Research Blending number producto i ')

model.IpvrF = Param(model.j, initialize = {1: 0.617 ,2: 0.617 ,3: 0.617}, doc = 'Limite de indice RVP producto final j')
model.Ipvr = Param(model.i, initialize = {1: 0.61140, 2: 0.03713 ,3: 0.02998}, doc = 'IPVR del producto i ')

model.PAzufreF = Param(model.j, initialize = {1: 1000, 2: 1000 ,3: 1000}, doc = 'Limite del azufre  producto final j')
model.PAzufre = Param(model.i, initialize = {1: 64.72995, 2: 345.32027 ,3: 0.78492}, doc = 'azufre que es calculador por el P = d*v del producto i ')

model.Destil = Param(initialize = 7849, doc = 'Destilacion atmosfereica')
model.rendimiento = Param( model.i, initialize = {1: 0.014, 2:0.15, 3:0.82}, doc = 'Rendimientos Nvl, Nvp, Ar')

model.densidad = Param( model.i, initialize = {1: 0.66, 2:0.749, 3:0.787}, doc = 'Densidad Nvl, Nvp, Ar')
model.preciog = Param( model.j, initialize = {1: 3000, 2:4000, 3:4400}, doc = 'Precio Gaso83, Gaso90, Gaso94')
model.demandag = Param( model.j, initialize = {1: 300, 2:400, 3:440}, doc = 'Demanda Gaso83, Gaso90, Gaso94')



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
model.NvlMB = Constraint(expr = x[1,1] + x[1,2] <= model.rendimiento[1]*model.Destil, doc = 'Balance de Materiales para la Nafta Virgen ligera')

model.NvpMB = Constraint(expr = x[2,1] + x[2,2] + model.Ar <= model.rendimiento[2]*model.Destil, doc = 'Balance de Materiales para la Nafta Virgen Pesada')

model.Ref = Constraint(expr = x[3,1] + x[3,2] + x[3,3] <= model.rendimiento[3]*Ar, doc = 'Balance de Materiales para el Refromado')
#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) == Wg[j] 
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
def rbn_rule(model, j):
  return sum(model.Rbn[i]*x[i,j] for i in model.i) >= model.RbnPf[j]*gx[j] 
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

def ipvr_rule(model, j):
  return sum(model.Ipvr[i]*x[i,j] for i in model.i) >= model.IpvrF[j]*gx[j] 
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

def pazufre_rule(model, j):
  return   sum(model.PAzufre[i]*x[i,j] for i in model.i) >= model.PAzufreF[j]*gx[j]  
model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')

#gasolina j
model.g83 = Constraint(expr = x[1,1] + x[2,1] + x[3,1] == gx[1], doc = 'Gasolina 83')
model.g90 = Constraint(expr = x[1,2] + x[2,2] + x[3,2] == gx[2], doc = 'Gasolina 90')
model.g94 = Constraint(expr = x[3,2] == gx[3], doc = 'Gasolina 94')

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
#pyomo_postprocess(None, None, resultados)


model.display()