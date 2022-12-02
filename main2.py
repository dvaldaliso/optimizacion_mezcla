#! /usr/bin/python3
from docplex.mp.model import Model

m = Model(name='mezcla de gasolina')
x1 = m.continuous_var(name="x1", lb=0)
x2 = m.continuous_var(name="x2", lb=0)
x3 = m.continuous_var(name="x3", lb=0)
c1 = m.add_constraint(x1 + 2*x2 + x3 <= 430, ctname="const1")
c2 = m.add_constraint(3*x1 + 2*x3 <= 460, ctname="const2")
c2 = m.add_constraint(x1 + 4*x2 <= 420, ctname="const2")
m.set_objective("Max", 3*x1 + 2*x2 + 5*x3)
m.print_information()
m.solve()
m.print_solution()

n_cons = m.number_of_constraints
const = [m.get_constraint_by_index(i) for i in range(n_cons)]
h = m.slack_values(const)

for n in range(n_cons):
    print('las variables de holguras son. '+str(const[n])+' es  '+str(h[n]))

precios_duales = m.dual_values(const)
for n in range(n_cons):
    print('los precios duales de las restrccion es. ' +
          str(const[n])+' es  '+str(precios_duales[n]))


cpx = m.get_engine().get_cplex()

of = cpx.solution.sensitivity.objective()
b = cpx.solution.sensitivity.rhs()

var_list = [m.get_var_by_name('x1'), m.get_var_by_name(
    'x2'), m.get_var_by_name('x3')]
print('-'*80)
for n in range(len(var_list)):
    print('los costos reducidos son. ' +
          str(var_list[n])+' '+str(var_list[n].reduced_cost))
print('Analisis')
for n in range(len(var_list)):
    print('la varaible >' + str(var_list[n])+' '+str(of[n]))
print('-'*80)
print('Restricciones de sensibilidad')
for n in range(n_cons):
    print('la varaible' + str(const[n])+' '+str(b[n]))
