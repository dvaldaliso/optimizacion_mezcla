#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory

N  =  3 # i
M  =  3 # j

d  =  {(1, 1): 1.7, (1, 2): 7.2, (1, 3): 9.0, (1, 4): 8.3,
(2, 1): 2.9, (2, 2): 6.3, (2, 3): 9.8, (2, 4): 0.7,
(3, 1): 4.5, (3, 2): 4.8, (3, 3): 4.2, (3, 4): 9.3}

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



#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1045), doc = 'Alimentacion al reformador')
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'Alimentacion al reformador')

model.x = Var( model.i, model.j, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
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
print(model.pprint())