#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *


model = ConcreteModel()
model.IDX = range(10)
model.a = Var()
model.b = Var(model.IDX)
model.c1 = Constraint( expr = sum(model.b[i] for i in model.IDX) <= model.a )
