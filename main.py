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

#PARAMETROS
model.RbnPf = Param(model.i, initialize = {1: 350,2: 600 ,3: 400}, doc = 'Limite de Research Blending Number producto final j')
model.Rbn = Param(model.i, initialize = {1: 55.48230, 2: 52.52652 ,3: 52.52652}, doc = 'Research Blending number producto i ')

model.IpvrF = Param(model.i, initialize = {1: 350,2: 600 ,3: 400}, doc = 'Limite de indice RVP producto final j')
model.Ipvr = Param(model.i, initialize = {1: 0.61140, 2: 0.03713 ,3: 0.02998}, doc = 'IPVR del producto i ')

model.PAzufreF = Param(model.i, initialize = {1: 350,2: 600 ,3: 400}, doc = 'Limite del azufre  producto final j')
model.PAzufre = Param(model.i, initialize = {1: 64.72995, 2: 345.32027 ,3: 0.78492}, doc = 'azufre que es calculador por el P = d*v del producto i ')

model.Destil = Param(initialize = 7849, doc = 'Destilacion atmosfereica')
model.rendimiento = Param( model.i, initialize = {1: 0.014, 2:0.15, 3:0.82}, doc = 'Rendimientos Nvl, Nvp, Ar')

model.densidad = Param( model.i, initialize = {1: 0.66, 2:0.749, 3:0.787}, doc = 'Densidad Nvl, Nvp, Ar')
model.preciog = Param( model.i, initialize = {1: 3000, 2:4000, 3:4400}, doc = 'Precio Gaso83, Gaso90, Gaso94')



#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1045), doc = 'Alimentacion al reformador')
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
model.x = Var( model.i, model.j, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
model.gx = Var( model.j, bounds = (0, None), doc = 'gasolina j ')
#RESTRICCINES
#demanda

#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)
model.NvlMB = Constraint(expr = model.x[1,1] + model.x[1,2] <= model.rendimiento[1]*model.Destil, doc = 'Balance de Materiales para la Nafta Virgen ligera')

model.NvpMB = Constraint(expr = model.x[2,1] + model.x[2,2] + model.Ar <= model.rendimiento[2]*model.Destil, doc = 'Balance de Materiales para la Nafta Virgen Pesada')

model.Ref = Constraint(expr = model.x[3,1] + model.x[3,2] + model.x[3,3] <= model.rendimiento[3]*model.Ar, doc = 'Balance de Materiales para el Refromado')
#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  model.Wg[j] == sum(model.densidad[i]*model.x[i,j] for i in model.i) 
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
def rbn_rule(model, j):
  return  model.RbnPf[j] <= sum(model.Rbn[i]*model.x[i,j] for i in model.i) 
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

def ipvr_rule(model, j):
  return model.IpvrF[j] <= sum(model.Ipvr[i]*model.x[i,j] for i in model.i) 
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

def pazufre_rule(model, j):
  return  model.PAzufreF[j] <= sum(model.PAzufre[i]*model.x[i,j] for i in model.i) 
model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')

#FUNCION OBJETIVO
def obj_rule(model):
  return sum( model.preciog[j]*model.gx[j] for j in model.j )
model.obj = Objective(expr = obj_rule, sense = maximize,doc = 'funcion objetivo')
#gasolina j
model.g83 = Constraint(expr = model.x[1,1] + model.x[2,1] + model.x[3,1] == model.gx[1], doc = 'Gasolina 83')
model.g90 = Constraint(expr = model.x[1,2] + model.x[2,2] + model.x[3,2] == model.gx[2], doc = 'Gasolina 90')
model.g94 = Constraint(expr = model.x[3,2] == model.gx[3], doc = 'Gasolina 94')

print(model.obj.pprint())