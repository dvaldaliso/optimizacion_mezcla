#! /usr/bin/python3
from docplex.mp.model import Model
m = Model(name='mezcla de gasolina')
x = m.continuous_var(name="x", lb=0)
y = m.continuous_var(name="y", lb=0)
c1 = m.add_constraint(2*x + y <= 20, ctname="const1")
c2 = m.add_constraint(x + y <= 18, ctname="const2")
c3 = m.add_constraint(x + 2*y >= 18, ctname="const3")
m.set_objective("Max", 5*x + 4*y)
m.print_information()
m.solve()
m.print_solution()
