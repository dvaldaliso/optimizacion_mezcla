#! /usr/bin/python3
from docplex.mp.model import Model
m = Model(name='mezcla de gasolina')
x = m.continuous_var(name="x", lb=0)
y = m.continuous_var(name="y", lb=0)
c1 = m.add_constraint(2*x + y >= 10, ctname="const1")
c2 = m.add_constraint(x + y >= 8, ctname="const2")
c3 = m.add_constraint(x + 4*y >= 11, ctname="const3")
m.set_objective("min", 5*x + 4*y)
m.print_information()
m.solve()
m.print_solution()