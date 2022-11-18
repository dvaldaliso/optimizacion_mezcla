#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory


model  =  pyo.ConcreteModel()
#SET O RANGOS
#model.i  =  RangeSet(N)   #producto intermedio
#model.j  =  RangeSet(M)   #producto final

model.i = Set(initialize=['Nvl','Np','Ref','Nim','NCraq'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94','Nex'], doc='Productos Finales')


#PARAMETROS
model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13049, 'Nim':52.59990, 'NCraq': 63.32281}, doc = 'Research Blending number producto i ')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998, 'Nim':0.78031, 'NCraq': 0.61750}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492, 'Nim':600.00000, 'NCraq': 1232.00000}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66, 'Np':0.749, 'Ref':0.787, 'Nim':0.75000, 'NCraq': 0.77000}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.89125002, 'G90': 62.360227, 'G94': 65.13049292,'Nex':0 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617 ,'G90': 0.617 ,'G94': 0.617,'Nex':0 }, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000, 'Nex':0}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.72, 'G90':0.72, 'G94':0.72, 'Nex':0}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746, 'Nex':1400}, doc = 'Precio Gaso83, Gaso90, Gaso94')

model.demandag = Param( model.j, initialize = {'G83': 300, 'G90':400, 'G94':440, 'Nex':0}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')

model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455, 'Nim':0, 'NCraq': 0}, doc = 'Rendimientos Nvl, Nvp, Ar')


#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, bounds = (0, None),  doc = 'gasolina j')
gx = model.gx

#RESTRICCIONES
#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)

def balance_materiales_rule(model, i):
  if i == 'Nvl' or i == 'Np' or i =='Ref':
    alimientacioRef = 0
    limite = model.rendimiento['Ref']*Ar
    if i=='Nvl':
      limite = model.rendimiento['Nvl']*model.Destil
    elif i=='Np':
      alimientacioRef = Ar
      limite = model.rendimiento['Np']*model.Destil 
    return  sum(x[i,j] for j in model.j) + alimientacioRef  == limite 

  
model.balance_materiales = Constraint(model.i, rule = balance_materiales_rule, doc = 'Balance de materiales')

model.balance_materiales.pprint()
#gasolina mbj
def gasolinabm_rule(model, j):
  return  sum(x[i,j] for i in model.i) == gx[j]
model.gmb = Constraint(model.j, rule = gasolinabm_rule, doc = 'Balance de materiales para la gasolina j')

#La suma de todas las partes debe mayor que 0
def wgaso_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) >= 0 
model.wgaso = Constraint(model.j, rule = wgaso_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor a 0')

#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  == Wg[j]
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
#RON
def rbn_rule(model, j):
  limite = model.RbnPf[j] * gx[j]
  return sum(model.Rbn[i]* x[i,j] for i in model.i)  >=  limite
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

#RVP
def ipvr_rule(model, j):
  limite = model.IpvrF[j] * gx[j]
  return sum(model.Ipvr[i]*x[i,j] for i in model.i)  >=  limite
  
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

#Azufre
def pazufre_rule(model, j):
  limite = model.PAzufreF[j] * gx[j]
  return  sum(model.PAzufre[i]*x[i,j] for i in model.i)  >= limite

model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')
#densidad
def desnidad_rule(model, j):
  limite = model.PdensidadF[j] * gx[j]
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  >= limite

model.den = Constraint(model.j, rule = desnidad_rule, doc = 'Restriccion Densidad de calidad producto final j')

#model.den.deactivate()
#model.rbn.deactivate()
#model.ipvr.deactivate()
#model.azufre.deactivate()

#model.rbn.pprint()
#model.ipvr.pprint()
#model.azufre.pprint()
#model.den.pprint()


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



#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory


model  =  pyo.ConcreteModel()
#SET O RANGOS
#model.i  =  RangeSet(N)   #producto intermedio
#model.j  =  RangeSet(M)   #producto final

model.i = Set(initialize=['Nvl','Np','Ref','Nim','NCraq'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94','Nex'], doc='Productos Finales')


#PARAMETROS
model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13049, 'Nim':52.59990, 'NCraq': 63.32281}, doc = 'Research Blending number producto i ')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998, 'Nim':0.78031, 'NCraq': 0.61750}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492, 'Nim':600.00000, 'NCraq': 1232.00000}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66, 'Np':0.749, 'Ref':0.787, 'Nim':0.75000, 'NCraq': 0.77000}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.89125002, 'G90': 62.360227, 'G94': 65.13049292,'Nex':0 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617 ,'G90': 0.617 ,'G94': 0.617,'Nex':0 }, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000, 'Nex':0}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.72, 'G90':0.72, 'G94':0.72, 'Nex':0}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746, 'Nex':1400}, doc = 'Precio Gaso83, Gaso90, Gaso94')

model.demandag = Param( model.j, initialize = {'G83': 300, 'G90':400, 'G94':440, 'Nex':0}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')

model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455, 'Nim':0, 'NCraq': 0}, doc = 'Rendimientos Nvl, Nvp, Ar')


#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, bounds = (0, None),  doc = 'gasolina j')
gx = model.gx

#RESTRICCIONES
#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)

def balance_materiales_rule(model, i):
  if i == 'Nvl' or i == 'Np' or i =='Ref':
    alimientacioRef = 0
    limite = model.rendimiento['Ref']*Ar
    if i=='Nvl':
      limite = model.rendimiento['Nvl']*model.Destil
    elif i=='Np':
      alimientacioRef = Ar
      limite = model.rendimiento['Np']*model.Destil 
    return  sum(x[i,j] for j in model.j) + alimientacioRef  == limite 

  
model.balance_materiales = Constraint(model.i, rule = balance_materiales_rule, doc = 'Balance de materiales')

model.balance_materiales.pprint()
#gasolina mbj
def gasolinabm_rule(model, j):
  return  sum(x[i,j] for i in model.i) == gx[j]
model.gmb = Constraint(model.j, rule = gasolinabm_rule, doc = 'Balance de materiales para la gasolina j')

#La suma de todas las partes debe mayor que 0
def wgaso_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) >= 0 
model.wgaso = Constraint(model.j, rule = wgaso_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor a 0')

#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  == Wg[j]
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
#RON
def rbn_rule(model, j):
  limite = model.RbnPf[j] * gx[j]
  return sum(model.Rbn[i]* x[i,j] for i in model.i)  >=  limite
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

#RVP
def ipvr_rule(model, j):
  limite = model.IpvrF[j] * gx[j]
  return sum(model.Ipvr[i]*x[i,j] for i in model.i)  >=  limite
  
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

#Azufre
def pazufre_rule(model, j):
  limite = model.PAzufreF[j] * gx[j]
  return  sum(model.PAzufre[i]*x[i,j] for i in model.i)  >= limite

model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')
#densidad
def desnidad_rule(model, j):
  limite = model.PdensidadF[j] * gx[j]
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  >= limite

model.den = Constraint(model.j, rule = desnidad_rule, doc = 'Restriccion Densidad de calidad producto final j')

#model.den.deactivate()
#model.rbn.deactivate()
#model.ipvr.deactivate()
#model.azufre.deactivate()

#model.rbn.pprint()
#model.ipvr.pprint()
#model.azufre.pprint()
#model.den.pprint()


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



#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory


model  =  pyo.ConcreteModel()
#SET O RANGOS
#model.i  =  RangeSet(N)   #producto intermedio
#model.j  =  RangeSet(M)   #producto final

model.i = Set(initialize=['Nvl','Np','Ref','Nim','NCraq'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94','Nex'], doc='Productos Finales')


#PARAMETROS
model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13049, 'Nim':52.59990, 'NCraq': 63.32281}, doc = 'Research Blending number producto i ')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998, 'Nim':0.78031, 'NCraq': 0.61750}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492, 'Nim':600.00000, 'NCraq': 1232.00000}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66, 'Np':0.749, 'Ref':0.787, 'Nim':0.75000, 'NCraq': 0.77000}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.89125002, 'G90': 62.360227, 'G94': 65.13049292,'Nex':0 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617 ,'G90': 0.617 ,'G94': 0.617,'Nex':0 }, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000, 'Nex':0}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.72, 'G90':0.72, 'G94':0.72, 'Nex':0}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746, 'Nex':1400}, doc = 'Precio Gaso83, Gaso90, Gaso94')

model.demandag = Param( model.j, initialize = {'G83': 300, 'G90':400, 'G94':440, 'Nex':0}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')

model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455, 'Nim':0, 'NCraq': 0}, doc = 'Rendimientos Nvl, Nvp, Ar')


#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, bounds = (0, None),  doc = 'gasolina j')
gx = model.gx

#RESTRICCIONES
#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)

def balance_materiales_rule(model, i):
  if i == 'Nvl' or i == 'Np' or i =='Ref':
    alimientacioRef = 0
    limite = model.rendimiento['Ref']*Ar
    if i=='Nvl':
      limite = model.rendimiento['Nvl']*model.Destil
    elif i=='Np':
      alimientacioRef = Ar
      limite = model.rendimiento['Np']*model.Destil 
    return  sum(x[i,j] for j in model.j) + alimientacioRef  == limite 

  
model.balance_materiales = Constraint(model.i, rule = balance_materiales_rule, doc = 'Balance de materiales')

model.balance_materiales.pprint()
#gasolina mbj
def gasolinabm_rule(model, j):
  return  sum(x[i,j] for i in model.i) == gx[j]
model.gmb = Constraint(model.j, rule = gasolinabm_rule, doc = 'Balance de materiales para la gasolina j')

#La suma de todas las partes debe mayor que 0
def wgaso_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) >= 0 
model.wgaso = Constraint(model.j, rule = wgaso_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor a 0')

#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  == Wg[j]
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
#RON
def rbn_rule(model, j):
  limite = model.RbnPf[j] * gx[j]
  return sum(model.Rbn[i]* x[i,j] for i in model.i)  >=  limite
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

#RVP
def ipvr_rule(model, j):
  limite = model.IpvrF[j] * gx[j]
  return sum(model.Ipvr[i]*x[i,j] for i in model.i)  >=  limite
  
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

#Azufre
def pazufre_rule(model, j):
  limite = model.PAzufreF[j] * gx[j]
  return  sum(model.PAzufre[i]*x[i,j] for i in model.i)  >= limite

model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')
#densidad
def desnidad_rule(model, j):
  limite = model.PdensidadF[j] * gx[j]
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  >= limite

model.den = Constraint(model.j, rule = desnidad_rule, doc = 'Restriccion Densidad de calidad producto final j')

#model.den.deactivate()
#model.rbn.deactivate()
#model.ipvr.deactivate()
#model.azufre.deactivate()

#model.rbn.pprint()
#model.ipvr.pprint()
#model.azufre.pprint()
#model.den.pprint()


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



#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory


model  =  pyo.ConcreteModel()
#SET O RANGOS
#model.i  =  RangeSet(N)   #producto intermedio
#model.j  =  RangeSet(M)   #producto final

model.i = Set(initialize=['Nvl','Np','Ref','Nim','NCraq'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94','Nex'], doc='Productos Finales')


#PARAMETROS
model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13049, 'Nim':52.59990, 'NCraq': 63.32281}, doc = 'Research Blending number producto i ')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998, 'Nim':0.78031, 'NCraq': 0.61750}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492, 'Nim':600.00000, 'NCraq': 1232.00000}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66, 'Np':0.749, 'Ref':0.787, 'Nim':0.75000, 'NCraq': 0.77000}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.89125002, 'G90': 62.360227, 'G94': 65.13049292,'Nex':0 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617 ,'G90': 0.617 ,'G94': 0.617,'Nex':0 }, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000, 'Nex':0}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.72, 'G90':0.72, 'G94':0.72, 'Nex':0}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746, 'Nex':1400}, doc = 'Precio Gaso83, Gaso90, Gaso94')

model.demandag = Param( model.j, initialize = {'G83': 300, 'G90':400, 'G94':440, 'Nex':0}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')

model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455, 'Nim':0, 'NCraq': 0}, doc = 'Rendimientos Nvl, Nvp, Ar')


#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, bounds = (0, None),  doc = 'gasolina j')
gx = model.gx

#RESTRICCIONES
#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)

def balance_materiales_rule(model, i):
  if i == 'Nvl' or i == 'Np' or i =='Ref':
    alimientacioRef = 0
    limite = model.rendimiento['Ref']*Ar
    if i=='Nvl':
      limite = model.rendimiento['Nvl']*model.Destil
    elif i=='Np':
      alimientacioRef = Ar
      limite = model.rendimiento['Np']*model.Destil 
    return  sum(x[i,j] for j in model.j) + alimientacioRef  == limite 

  
model.balance_materiales = Constraint(model.i, rule = balance_materiales_rule, doc = 'Balance de materiales')

model.balance_materiales.pprint()
#gasolina mbj
def gasolinabm_rule(model, j):
  return  sum(x[i,j] for i in model.i) == gx[j]
model.gmb = Constraint(model.j, rule = gasolinabm_rule, doc = 'Balance de materiales para la gasolina j')

#La suma de todas las partes debe mayor que 0
def wgaso_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) >= 0 
model.wgaso = Constraint(model.j, rule = wgaso_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor a 0')

#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  == Wg[j]
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
#RON
def rbn_rule(model, j):
  limite = model.RbnPf[j] * gx[j]
  return sum(model.Rbn[i]* x[i,j] for i in model.i)  >=  limite
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

#RVP
def ipvr_rule(model, j):
  limite = model.IpvrF[j] * gx[j]
  return sum(model.Ipvr[i]*x[i,j] for i in model.i)  >=  limite
  
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

#Azufre
def pazufre_rule(model, j):
  limite = model.PAzufreF[j] * gx[j]
  return  sum(model.PAzufre[i]*x[i,j] for i in model.i)  >= limite

model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')
#densidad
def desnidad_rule(model, j):
  limite = model.PdensidadF[j] * gx[j]
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  >= limite

model.den = Constraint(model.j, rule = desnidad_rule, doc = 'Restriccion Densidad de calidad producto final j')

#model.den.deactivate()
#model.rbn.deactivate()
#model.ipvr.deactivate()
#model.azufre.deactivate()

#model.rbn.pprint()
#model.ipvr.pprint()
#model.azufre.pprint()
#model.den.pprint()


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



#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory


model  =  pyo.ConcreteModel()
#SET O RANGOS
#model.i  =  RangeSet(N)   #producto intermedio
#model.j  =  RangeSet(M)   #producto final

model.i = Set(initialize=['Nvl','Np','Ref','Nim','NCraq'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94','Nex'], doc='Productos Finales')


#PARAMETROS
model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13049, 'Nim':52.59990, 'NCraq': 63.32281}, doc = 'Research Blending number producto i ')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998, 'Nim':0.78031, 'NCraq': 0.61750}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492, 'Nim':600.00000, 'NCraq': 1232.00000}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66, 'Np':0.749, 'Ref':0.787, 'Nim':0.75000, 'NCraq': 0.77000}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.89125002, 'G90': 62.360227, 'G94': 65.13049292,'Nex':0 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617 ,'G90': 0.617 ,'G94': 0.617,'Nex':0 }, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000, 'Nex':0}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.72, 'G90':0.72, 'G94':0.72, 'Nex':0}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746, 'Nex':1400}, doc = 'Precio Gaso83, Gaso90, Gaso94')

model.demandag = Param( model.j, initialize = {'G83': 300, 'G90':400, 'G94':440, 'Nex':0}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')

model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455, 'Nim':0, 'NCraq': 0}, doc = 'Rendimientos Nvl, Nvp, Ar')


#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, bounds = (0, None),  doc = 'gasolina j')
gx = model.gx

#RESTRICCIONES
#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)

def balance_materiales_rule(model, i):
  if i == 'Nvl' or i == 'Np' or i =='Ref':
    alimientacioRef = 0
    limite = model.rendimiento['Ref']*Ar
    if i=='Nvl':
      limite = model.rendimiento['Nvl']*model.Destil
    elif i=='Np':
      alimientacioRef = Ar
      limite = model.rendimiento['Np']*model.Destil 
    return  sum(x[i,j] for j in model.j) + alimientacioRef  == limite 

  
model.balance_materiales = Constraint(model.i, rule = balance_materiales_rule, doc = 'Balance de materiales')

model.balance_materiales.pprint()
#gasolina mbj
def gasolinabm_rule(model, j):
  return  sum(x[i,j] for i in model.i) == gx[j]
model.gmb = Constraint(model.j, rule = gasolinabm_rule, doc = 'Balance de materiales para la gasolina j')

#La suma de todas las partes debe mayor que 0
def wgaso_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) >= 0 
model.wgaso = Constraint(model.j, rule = wgaso_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor a 0')

#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  == Wg[j]
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
#RON
def rbn_rule(model, j):
  limite = model.RbnPf[j] * gx[j]
  return sum(model.Rbn[i]* x[i,j] for i in model.i)  >=  limite
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

#RVP
def ipvr_rule(model, j):
  limite = model.IpvrF[j] * gx[j]
  return sum(model.Ipvr[i]*x[i,j] for i in model.i)  >=  limite
  
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

#Azufre
def pazufre_rule(model, j):
  limite = model.PAzufreF[j] * gx[j]
  return  sum(model.PAzufre[i]*x[i,j] for i in model.i)  >= limite

model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')
#densidad
def desnidad_rule(model, j):
  limite = model.PdensidadF[j] * gx[j]
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  >= limite

model.den = Constraint(model.j, rule = desnidad_rule, doc = 'Restriccion Densidad de calidad producto final j')

#model.den.deactivate()
#model.rbn.deactivate()
#model.ipvr.deactivate()
#model.azufre.deactivate()

#model.rbn.pprint()
#model.ipvr.pprint()
#model.azufre.pprint()
#model.den.pprint()


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



#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory


model  =  pyo.ConcreteModel()
#SET O RANGOS
#model.i  =  RangeSet(N)   #producto intermedio
#model.j  =  RangeSet(M)   #producto final

model.i = Set(initialize=['Nvl','Np','Ref','Nim','NCraq'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94','Nex'], doc='Productos Finales')


#PARAMETROS
model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13049, 'Nim':52.59990, 'NCraq': 63.32281}, doc = 'Research Blending number producto i ')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998, 'Nim':0.78031, 'NCraq': 0.61750}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492, 'Nim':600.00000, 'NCraq': 1232.00000}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66, 'Np':0.749, 'Ref':0.787, 'Nim':0.75000, 'NCraq': 0.77000}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.89125002, 'G90': 62.360227, 'G94': 65.13049292,'Nex':0 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617 ,'G90': 0.617 ,'G94': 0.617,'Nex':0 }, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000, 'Nex':0}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.72, 'G90':0.72, 'G94':0.72, 'Nex':0}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746, 'Nex':1400}, doc = 'Precio Gaso83, Gaso90, Gaso94')

model.demandag = Param( model.j, initialize = {'G83': 300, 'G90':400, 'G94':440, 'Nex':0}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')

model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455, 'Nim':0, 'NCraq': 0}, doc = 'Rendimientos Nvl, Nvp, Ar')


#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, bounds = (0, None),  doc = 'gasolina j')
gx = model.gx

#RESTRICCIONES
#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)

def balance_materiales_rule(model, i):
  if i == 'Nvl' or i == 'Np' or i =='Ref':
    alimientacioRef = 0
    limite = model.rendimiento['Ref']*Ar
    if i=='Nvl':
      limite = model.rendimiento['Nvl']*model.Destil
    elif i=='Np':
      alimientacioRef = Ar
      limite = model.rendimiento['Np']*model.Destil 
    return  sum(x[i,j] for j in model.j) + alimientacioRef  == limite 

  
model.balance_materiales = Constraint(model.i, rule = balance_materiales_rule, doc = 'Balance de materiales')

model.balance_materiales.pprint()
#gasolina mbj
def gasolinabm_rule(model, j):
  return  sum(x[i,j] for i in model.i) == gx[j]
model.gmb = Constraint(model.j, rule = gasolinabm_rule, doc = 'Balance de materiales para la gasolina j')

#La suma de todas las partes debe mayor que 0
def wgaso_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) >= 0 
model.wgaso = Constraint(model.j, rule = wgaso_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor a 0')

#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  == Wg[j]
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
#RON
def rbn_rule(model, j):
  limite = model.RbnPf[j] * gx[j]
  return sum(model.Rbn[i]* x[i,j] for i in model.i)  >=  limite
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

#RVP
def ipvr_rule(model, j):
  limite = model.IpvrF[j] * gx[j]
  return sum(model.Ipvr[i]*x[i,j] for i in model.i)  >=  limite
  
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

#Azufre
def pazufre_rule(model, j):
  limite = model.PAzufreF[j] * gx[j]
  return  sum(model.PAzufre[i]*x[i,j] for i in model.i)  >= limite

model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')
#densidad
def desnidad_rule(model, j):
  limite = model.PdensidadF[j] * gx[j]
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  >= limite

model.den = Constraint(model.j, rule = desnidad_rule, doc = 'Restriccion Densidad de calidad producto final j')

#model.den.deactivate()
#model.rbn.deactivate()
#model.ipvr.deactivate()
#model.azufre.deactivate()

#model.rbn.pprint()
#model.ipvr.pprint()
#model.azufre.pprint()
#model.den.pprint()


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



#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory


model  =  pyo.ConcreteModel()
#SET O RANGOS
#model.i  =  RangeSet(N)   #producto intermedio
#model.j  =  RangeSet(M)   #producto final

model.i = Set(initialize=['Nvl','Np','Ref','Nim','NCraq'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94','Nex'], doc='Productos Finales')


#PARAMETROS
model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13049, 'Nim':52.59990, 'NCraq': 63.32281}, doc = 'Research Blending number producto i ')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998, 'Nim':0.78031, 'NCraq': 0.61750}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492, 'Nim':600.00000, 'NCraq': 1232.00000}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66, 'Np':0.749, 'Ref':0.787, 'Nim':0.75000, 'NCraq': 0.77000}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.89125002, 'G90': 62.360227, 'G94': 65.13049292,'Nex':0 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617 ,'G90': 0.617 ,'G94': 0.617,'Nex':0 }, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000, 'Nex':0}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.72, 'G90':0.72, 'G94':0.72, 'Nex':0}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746, 'Nex':1400}, doc = 'Precio Gaso83, Gaso90, Gaso94')

model.demandag = Param( model.j, initialize = {'G83': 300, 'G90':400, 'G94':440, 'Nex':0}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')

model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455, 'Nim':0, 'NCraq': 0}, doc = 'Rendimientos Nvl, Nvp, Ar')


#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, bounds = (0, None),  doc = 'gasolina j')
gx = model.gx

#RESTRICCIONES
#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)

def balance_materiales_rule(model, i):
  if i == 'Nvl' or i == 'Np' or i =='Ref':
    alimientacioRef = 0
    limite = model.rendimiento['Ref']*Ar
    if i=='Nvl':
      limite = model.rendimiento['Nvl']*model.Destil
    elif i=='Np':
      alimientacioRef = Ar
      limite = model.rendimiento['Np']*model.Destil 
    return  sum(x[i,j] for j in model.j) + alimientacioRef  == limite 

  
model.balance_materiales = Constraint(model.i, rule = balance_materiales_rule, doc = 'Balance de materiales')

model.balance_materiales.pprint()
#gasolina mbj
def gasolinabm_rule(model, j):
  return  sum(x[i,j] for i in model.i) == gx[j]
model.gmb = Constraint(model.j, rule = gasolinabm_rule, doc = 'Balance de materiales para la gasolina j')

#La suma de todas las partes debe mayor que 0
def wgaso_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) >= 0 
model.wgaso = Constraint(model.j, rule = wgaso_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor a 0')

#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  == Wg[j]
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
#RON
def rbn_rule(model, j):
  limite = model.RbnPf[j] * gx[j]
  return sum(model.Rbn[i]* x[i,j] for i in model.i)  >=  limite
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

#RVP
def ipvr_rule(model, j):
  limite = model.IpvrF[j] * gx[j]
  return sum(model.Ipvr[i]*x[i,j] for i in model.i)  >=  limite
  
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

#Azufre
def pazufre_rule(model, j):
  limite = model.PAzufreF[j] * gx[j]
  return  sum(model.PAzufre[i]*x[i,j] for i in model.i)  >= limite

model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')
#densidad
def desnidad_rule(model, j):
  limite = model.PdensidadF[j] * gx[j]
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  >= limite

model.den = Constraint(model.j, rule = desnidad_rule, doc = 'Restriccion Densidad de calidad producto final j')

#model.den.deactivate()
#model.rbn.deactivate()
#model.ipvr.deactivate()
#model.azufre.deactivate()

#model.rbn.pprint()
#model.ipvr.pprint()
#model.azufre.pprint()
#model.den.pprint()


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



#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory


model  =  pyo.ConcreteModel()
#SET O RANGOS
#model.i  =  RangeSet(N)   #producto intermedio
#model.j  =  RangeSet(M)   #producto final

model.i = Set(initialize=['Nvl','Np','Ref','Nim','NCraq'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94','Nex'], doc='Productos Finales')


#PARAMETROS
model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13049, 'Nim':52.59990, 'NCraq': 63.32281}, doc = 'Research Blending number producto i ')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998, 'Nim':0.78031, 'NCraq': 0.61750}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492, 'Nim':600.00000, 'NCraq': 1232.00000}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66, 'Np':0.749, 'Ref':0.787, 'Nim':0.75000, 'NCraq': 0.77000}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.89125002, 'G90': 62.360227, 'G94': 65.13049292,'Nex':0 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617 ,'G90': 0.617 ,'G94': 0.617,'Nex':0 }, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000, 'Nex':0}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.72, 'G90':0.72, 'G94':0.72, 'Nex':0}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746, 'Nex':1400}, doc = 'Precio Gaso83, Gaso90, Gaso94')

model.demandag = Param( model.j, initialize = {'G83': 300, 'G90':400, 'G94':440, 'Nex':0}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')

model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455, 'Nim':0, 'NCraq': 0}, doc = 'Rendimientos Nvl, Nvp, Ar')


#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, bounds = (0, None),  doc = 'gasolina j')
gx = model.gx

#RESTRICCIONES
#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)

def balance_materiales_rule(model, i):
  if i == 'Nvl' or i == 'Np' or i =='Ref':
    alimientacioRef = 0
    limite = model.rendimiento['Ref']*Ar
    if i=='Nvl':
      limite = model.rendimiento['Nvl']*model.Destil
    elif i=='Np':
      alimientacioRef = Ar
      limite = model.rendimiento['Np']*model.Destil 
    return  sum(x[i,j] for j in model.j) + alimientacioRef  == limite 

  
model.balance_materiales = Constraint(model.i, rule = balance_materiales_rule, doc = 'Balance de materiales')

model.balance_materiales.pprint()
#gasolina mbj
def gasolinabm_rule(model, j):
  return  sum(x[i,j] for i in model.i) == gx[j]
model.gmb = Constraint(model.j, rule = gasolinabm_rule, doc = 'Balance de materiales para la gasolina j')

#La suma de todas las partes debe mayor que 0
def wgaso_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) >= 0 
model.wgaso = Constraint(model.j, rule = wgaso_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor a 0')

#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  == Wg[j]
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
#RON
def rbn_rule(model, j):
  limite = model.RbnPf[j] * gx[j]
  return sum(model.Rbn[i]* x[i,j] for i in model.i)  >=  limite
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

#RVP
def ipvr_rule(model, j):
  limite = model.IpvrF[j] * gx[j]
  return sum(model.Ipvr[i]*x[i,j] for i in model.i)  >=  limite
  
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

#Azufre
def pazufre_rule(model, j):
  limite = model.PAzufreF[j] * gx[j]
  return  sum(model.PAzufre[i]*x[i,j] for i in model.i)  >= limite

model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')
#densidad
def desnidad_rule(model, j):
  limite = model.PdensidadF[j] * gx[j]
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  >= limite

model.den = Constraint(model.j, rule = desnidad_rule, doc = 'Restriccion Densidad de calidad producto final j')

#model.den.deactivate()
#model.rbn.deactivate()
#model.ipvr.deactivate()
#model.azufre.deactivate()

#model.rbn.pprint()
#model.ipvr.pprint()
#model.azufre.pprint()
#model.den.pprint()


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



#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory


model  =  pyo.ConcreteModel()
#SET O RANGOS
#model.i  =  RangeSet(N)   #producto intermedio
#model.j  =  RangeSet(M)   #producto final

model.i = Set(initialize=['Nvl','Np','Ref','Nim','NCraq'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94','Nex'], doc='Productos Finales')


#PARAMETROS
model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13049, 'Nim':52.59990, 'NCraq': 63.32281}, doc = 'Research Blending number producto i ')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998, 'Nim':0.78031, 'NCraq': 0.61750}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492, 'Nim':600.00000, 'NCraq': 1232.00000}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66, 'Np':0.749, 'Ref':0.787, 'Nim':0.75000, 'NCraq': 0.77000}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.89125002, 'G90': 62.360227, 'G94': 65.13049292,'Nex':0 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617 ,'G90': 0.617 ,'G94': 0.617,'Nex':0 }, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000, 'Nex':0}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.72, 'G90':0.72, 'G94':0.72, 'Nex':0}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746, 'Nex':1400}, doc = 'Precio Gaso83, Gaso90, Gaso94')

model.demandag = Param( model.j, initialize = {'G83': 300, 'G90':400, 'G94':440, 'Nex':0}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')

model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455, 'Nim':0, 'NCraq': 0}, doc = 'Rendimientos Nvl, Nvp, Ar')


#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, bounds = (0, None),  doc = 'gasolina j')
gx = model.gx

#RESTRICCIONES
#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)

def balance_materiales_rule(model, i):
  if i == 'Nvl' or i == 'Np' or i =='Ref':
    alimientacioRef = 0
    limite = model.rendimiento['Ref']*Ar
    if i=='Nvl':
      limite = model.rendimiento['Nvl']*model.Destil
    elif i=='Np':
      alimientacioRef = Ar
      limite = model.rendimiento['Np']*model.Destil 
    return  sum(x[i,j] for j in model.j) + alimientacioRef  == limite 

  
model.balance_materiales = Constraint(model.i, rule = balance_materiales_rule, doc = 'Balance de materiales')

model.balance_materiales.pprint()
#gasolina mbj
def gasolinabm_rule(model, j):
  return  sum(x[i,j] for i in model.i) == gx[j]
model.gmb = Constraint(model.j, rule = gasolinabm_rule, doc = 'Balance de materiales para la gasolina j')

#La suma de todas las partes debe mayor que 0
def wgaso_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) >= 0 
model.wgaso = Constraint(model.j, rule = wgaso_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor a 0')

#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  == Wg[j]
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
#RON
def rbn_rule(model, j):
  limite = model.RbnPf[j] * gx[j]
  return sum(model.Rbn[i]* x[i,j] for i in model.i)  >=  limite
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

#RVP
def ipvr_rule(model, j):
  limite = model.IpvrF[j] * gx[j]
  return sum(model.Ipvr[i]*x[i,j] for i in model.i)  >=  limite
  
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

#Azufre
def pazufre_rule(model, j):
  limite = model.PAzufreF[j] * gx[j]
  return  sum(model.PAzufre[i]*x[i,j] for i in model.i)  >= limite

model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')
#densidad
def desnidad_rule(model, j):
  limite = model.PdensidadF[j] * gx[j]
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  >= limite

model.den = Constraint(model.j, rule = desnidad_rule, doc = 'Restriccion Densidad de calidad producto final j')

#model.den.deactivate()
#model.rbn.deactivate()
#model.ipvr.deactivate()
#model.azufre.deactivate()

#model.rbn.pprint()
#model.ipvr.pprint()
#model.azufre.pprint()
#model.den.pprint()


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



#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory


model  =  pyo.ConcreteModel()
#SET O RANGOS
#model.i  =  RangeSet(N)   #producto intermedio
#model.j  =  RangeSet(M)   #producto final

model.i = Set(initialize=['Nvl','Np','Ref','Nim','NCraq'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94','Nex'], doc='Productos Finales')


#PARAMETROS
model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13049, 'Nim':52.59990, 'NCraq': 63.32281}, doc = 'Research Blending number producto i ')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998, 'Nim':0.78031, 'NCraq': 0.61750}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492, 'Nim':600.00000, 'NCraq': 1232.00000}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66, 'Np':0.749, 'Ref':0.787, 'Nim':0.75000, 'NCraq': 0.77000}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.89125002, 'G90': 62.360227, 'G94': 65.13049292,'Nex':0 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617 ,'G90': 0.617 ,'G94': 0.617,'Nex':0 }, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000, 'Nex':0}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.72, 'G90':0.72, 'G94':0.72, 'Nex':0}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746, 'Nex':1400}, doc = 'Precio Gaso83, Gaso90, Gaso94')

model.demandag = Param( model.j, initialize = {'G83': 300, 'G90':400, 'G94':440, 'Nex':0}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')

model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455, 'Nim':0, 'NCraq': 0}, doc = 'Rendimientos Nvl, Nvp, Ar')


#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, bounds = (0, None),  doc = 'gasolina j')
gx = model.gx

#RESTRICCIONES
#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)

def balance_materiales_rule(model, i):
  if i == 'Nvl' or i == 'Np' or i =='Ref':
    alimientacioRef = 0
    limite = model.rendimiento['Ref']*Ar
    if i=='Nvl':
      limite = model.rendimiento['Nvl']*model.Destil
    elif i=='Np':
      alimientacioRef = Ar
      limite = model.rendimiento['Np']*model.Destil 
    return  sum(x[i,j] for j in model.j) + alimientacioRef  == limite 

  
model.balance_materiales = Constraint(model.i, rule = balance_materiales_rule, doc = 'Balance de materiales')

model.balance_materiales.pprint()
#gasolina mbj
def gasolinabm_rule(model, j):
  return  sum(x[i,j] for i in model.i) == gx[j]
model.gmb = Constraint(model.j, rule = gasolinabm_rule, doc = 'Balance de materiales para la gasolina j')

#La suma de todas las partes debe mayor que 0
def wgaso_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) >= 0 
model.wgaso = Constraint(model.j, rule = wgaso_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor a 0')

#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  == Wg[j]
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
#RON
def rbn_rule(model, j):
  limite = model.RbnPf[j] * gx[j]
  return sum(model.Rbn[i]* x[i,j] for i in model.i)  >=  limite
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

#RVP
def ipvr_rule(model, j):
  limite = model.IpvrF[j] * gx[j]
  return sum(model.Ipvr[i]*x[i,j] for i in model.i)  >=  limite
  
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

#Azufre
def pazufre_rule(model, j):
  limite = model.PAzufreF[j] * gx[j]
  return  sum(model.PAzufre[i]*x[i,j] for i in model.i)  >= limite

model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')
#densidad
def desnidad_rule(model, j):
  limite = model.PdensidadF[j] * gx[j]
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  >= limite

model.den = Constraint(model.j, rule = desnidad_rule, doc = 'Restriccion Densidad de calidad producto final j')

#model.den.deactivate()
#model.rbn.deactivate()
#model.ipvr.deactivate()
#model.azufre.deactivate()

#model.rbn.pprint()
#model.ipvr.pprint()
#model.azufre.pprint()
#model.den.pprint()


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



#! /usr/bin/python3

import pyomo.environ as pyo
from pyomo.environ import *
from pyomo.opt import SolverFactory


model  =  pyo.ConcreteModel()
#SET O RANGOS
#model.i  =  RangeSet(N)   #producto intermedio
#model.j  =  RangeSet(M)   #producto final

model.i = Set(initialize=['Nvl','Np','Ref','Nim','NCraq'], doc='Productos Intermedios')
model.j = Set(initialize=['G83', 'G90', 'G94','Nex'], doc='Productos Finales')


#PARAMETROS
model.Rbn = Param(model.i, initialize = {'Nvl': 55.48230,'Np': 52.52652, 'Ref': 65.13049, 'Nim':52.59990, 'NCraq': 63.32281}, doc = 'Research Blending number producto i ')
model.Ipvr = Param(model.i, initialize = {'Nvl': 0.61140, 'Np': 0.03713 ,'Ref': 0.02998, 'Nim':0.78031, 'NCraq': 0.61750}, doc = 'IPVR del producto i ')
model.PAzufre = Param(model.i, initialize = {'Nvl': 64.72995, 'Np': 345.32027 ,'Ref': 0.78492, 'Nim':600.00000, 'NCraq': 1232.00000}, doc = 'azufre que es calculador por el P = d*v del producto i ')
model.densidad = Param( model.i, initialize = {'Nvl': 0.66, 'Np':0.749, 'Ref':0.787, 'Nim':0.75000, 'NCraq': 0.77000}, doc = 'Densidad Nvl, Nvp, Ar')

model.RbnPf = Param(model.j, initialize = {'G83': 58.89125002, 'G90': 62.360227, 'G94': 65.13049292,'Nex':0 }, doc = 'Limite de Research Blending Number producto final j')
model.IpvrF = Param(model.j, initialize = {'G83': 0.617 ,'G90': 0.617 ,'G94': 0.617,'Nex':0 }, doc = 'Limite de indice RVP producto final j')
model.PAzufreF = Param(model.j, initialize = {'G83': 1000, 'G90': 1000 ,'G94': 1000, 'Nex':0}, doc = 'Limite del azufre  producto final j')
model.PdensidadF = Param( model.j, initialize = {'G83': 0.72, 'G90':0.72, 'G94':0.72, 'Nex':0}, doc = 'Densidad producto j')
model.preciog = Param( model.j, initialize = {'G83': 3300, 'G90':3500, 'G94':3746, 'Nex':1400}, doc = 'Precio Gaso83, Gaso90, Gaso94')

model.demandag = Param( model.j, initialize = {'G83': 300, 'G90':400, 'G94':440, 'Nex':0}, doc = 'Demanda Gaso83, Gaso90, Gaso94')
model.Destil = Param(initialize = 8744, doc = 'Destilacion atmosfereica')

model.rendimiento = Param( model.i, initialize = {'Nvl': 0.04776, 'Np':0.151957, 'Ref':0.82455, 'Nim':0, 'NCraq': 0}, doc = 'Rendimientos Nvl, Nvp, Ar')


#VARAIABLES
model.Ar = Var(within = NonNegativeReals, bounds = (0, 1526), doc = 'Alimentacion al reformador')
Ar = model.Ar
model.Wg = Var(model.j ,within = NonNegativeReals, bounds = (0, None), doc = 'gasolina por un peso W(masa)')
Wg = model.Wg
model.x = Var( model.i, model.j,within = NonNegativeReals, bounds = (0, None), doc = 'transferencia m3/d del producto intermedio i en la mezcla del producto final j ')
x = model.x
model.gx = Var(model.j,within = NonNegativeReals, bounds = (0, None),  doc = 'gasolina j')
gx = model.gx

#RESTRICCIONES
#Balance de materiales(Lo que se extrae de los productos intermedios no sobrepasara la existencia)

def balance_materiales_rule(model, i):
  if i == 'Nvl' or i == 'Np' or i =='Ref':
    alimientacioRef = 0
    limite = model.rendimiento['Ref']*Ar
    if i=='Nvl':
      limite = model.rendimiento['Nvl']*model.Destil
    elif i=='Np':
      alimientacioRef = Ar
      limite = model.rendimiento['Np']*model.Destil 
    return  sum(x[i,j] for j in model.j) + alimientacioRef  == limite 

  
model.balance_materiales = Constraint(model.i, rule = balance_materiales_rule, doc = 'Balance de materiales')

model.balance_materiales.pprint()
#gasolina mbj
def gasolinabm_rule(model, j):
  return  sum(x[i,j] for i in model.i) == gx[j]
model.gmb = Constraint(model.j, rule = gasolinabm_rule, doc = 'Balance de materiales para la gasolina j')

#La suma de todas las partes debe mayor que 0
def wgaso_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i) >= 0 
model.wgaso = Constraint(model.j, rule = wgaso_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor a 0')

#La suma de todas las partes debe ser el total de la mezcla a elaborar
def wgasolina_rule(model, j):
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  == Wg[j]
model.wgasolina = Constraint(model.j, rule = wgasolina_rule, doc = 'El peso en masa de todos los productos intermedios tiene que ser mayor o igual que el peso en masa del producto final j')

#calidad
#RON
def rbn_rule(model, j):
  limite = model.RbnPf[j] * gx[j]
  return sum(model.Rbn[i]* x[i,j] for i in model.i)  >=  limite
model.rbn = Constraint(model.j, rule = rbn_rule, doc = 'Restriccion RON de calidad producto final j')

#RVP
def ipvr_rule(model, j):
  limite = model.IpvrF[j] * gx[j]
  return sum(model.Ipvr[i]*x[i,j] for i in model.i)  >=  limite
  
model.ipvr = Constraint(model.j, rule = ipvr_rule, doc = 'Restriccion RVP de calidad producto final j')

#Azufre
def pazufre_rule(model, j):
  limite = model.PAzufreF[j] * gx[j]
  return  sum(model.PAzufre[i]*x[i,j] for i in model.i)  >= limite

model.azufre = Constraint(model.j, rule = pazufre_rule, doc = 'Restriccion Peso Azufre de calidad producto final j')
#densidad
def desnidad_rule(model, j):
  limite = model.PdensidadF[j] * gx[j]
  return  sum(model.densidad[i]*x[i,j] for i in model.i)  >= limite

model.den = Constraint(model.j, rule = desnidad_rule, doc = 'Restriccion Densidad de calidad producto final j')

#model.den.deactivate()
#model.rbn.deactivate()
#model.ipvr.deactivate()
#model.azufre.deactivate()

#model.rbn.pprint()
#model.ipvr.pprint()
#model.azufre.pprint()
#model.den.pprint()


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



