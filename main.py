#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory

N = 3 # i
M = 3 # j
Pf = 3

d = {(1, 1): 1.7, (1, 2): 7.2, (1, 3): 9.0, (1, 4): 8.3,
(2, 1): 2.9, (2, 2): 6.3, (2, 3): 9.8, (2, 4): 0.7,
(3, 1): 4.5, (3, 2): 4.8, (3, 3): 4.2, (3, 4): 9.3}

model = pyo.ConcreteModel()
model.i = RangeSet(N)   #producto intermedio
model.j = RangeSet(M)   #producto final


model.RbnPf = Param(model.i, initialize={1: 350,2: 600 ,3: 400}, doc='Limite de Research Blending Number producto final j')
model.Rbn = Param(model.i, initialize={1: 350,2: 600 ,3: 400}, doc='Research Blending number producto i ')


model.x = Var( model.i, model.j, bounds=(0,None))

def rbn_rule(model, j):
  return sum(model.Rbn[i]*model.x[i,j] for i in model.i) <= model.RbnPf[j]

model.rbn = Constraint(model.j, rule=rbn_rule, doc='Restriccion de calidad producto final j')

print(model.pprint())