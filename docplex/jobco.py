#! /usr/bin/python3
from docplex.mp.model import Model

m = Model(name='JOBCO')
x1 = m.continuous_var(name="x1", lb=0)
x2 = m.continuous_var(name="x2", lb=0)

c1 = m.add_constraint(2*x1 + x2 <= 8, ctname="const1")
c2 = m.add_constraint(x1 + 3*x2 <= 8, ctname="const2")
m.set_objective("Max", 30*x1 + 20*x2)
m.print_information()
m.solve()
m.print_solution()
cantLin = 20
n_cons = m.number_of_constraints
const = [m.get_constraint_by_index(i) for i in range(n_cons)]
h = m.slack_values(const)
print('-'*cantLin+'HOLGURAS'+'-'*cantLin)
for n in range(n_cons):
    print('las variables de holguras son. '+str(const[n])+' es  '+str(h[n]))
print('-'*cantLin+'Precios duales'+'-'*cantLin)
precios_duales = m.dual_values(const)
for n in range(n_cons):
    print('los precios duales de las restrccion es. ' +
          str(const[n])+' es  '+str(precios_duales[n]))


cpx = m.get_engine().get_cplex()


of = cpx.solution.sensitivity.objective()
b = cpx.solution.sensitivity.rhs()

var_list = [m.get_var_by_name('x1'), m.get_var_by_name(
    'x2')]

print('-'*cantLin+'COSTOS REDUCIDOS'+'-'*cantLin)
for n in range(len(var_list)):
    print('los costos reducidos son. ' +
          str(var_list[n])+' '+str(var_list[n].reduced_cost))

print('-'*cantLin+'SENSIBILIDAD FO'+'-'*cantLin)
for n in range(len(var_list)):
    print('la varaible >' + str(var_list[n])+' '+str(of[n]))

print('-'*cantLin+'SENSIBILIDAD LADO DERECHO'+'-'*cantLin)
print('Restricciones de sensibilidad')
# La conclusión es que el precio dual de 14,00 $/h sigue siendo válido sólo en el rango
for n in range(n_cons):
    print(
        'La conclusión es que el precio dual de {} $/h sigue siendo válido sólo en el rango'.format(precios_duales[n]))
    print('la varaible ' + str(const[n])+' '+str(b[n]))
    print('---')

print('-----Matriz Soluction Optima-----------')
cp = m.get_cplex()

for fila in cp.solution.advanced.binvarow():
    print(fila)
print('-'*8)
for fila in cp.solution.advanced.binvrow():
    print(fila)
