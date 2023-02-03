#! /usr/bin/python3.6
import numpy as np
import sympy as sp
from sympy.matrices import Matrix, eye, zeros, ones, diag, GramSchmidt
import Utilsimplex as util

# El metodo utilizado aqui es el de la M
# Es recomendabe usar el metodo de las 2s fases que en la fase1  elimina las varaibles artificiales minimizando
# la suma de las variables artificiales y el resto del problema igual, luego este
# si es factible pasa a la fase 2 que es resolver el problema con el simplex.

# Max z= 5x1 + 4x2
#       2x1 +  x2 <= 20
#        x1 +  x2 <= 18
#        x1 + 2x2 >= 18
#       x1, x2, x3 >= 0

# Max z= 5x1 + 4x2 + S1 + S2 - S3 + MA3
#       2x1 +  x2  + S1                  = 20
#        x1 +  x2       + S2             = 18
#        x1 + 2x2            - S3 +  A3  = 12
#       x1, x2, x3 >= 0

# Info base

# Coeficientes de la FO
c = np.array([5, 4])

Rmenorigual = 2
Rmayorigual = 1

holguras = [0 for m in range(1, Rmenorigual+1)]
excesos = [0 for m in range(1, Rmayorigual+1)]
# What value of M should we use? The answer depends on the data of the original LP. Recall that the penalty M must be sufficiently large relative to the original objective coefficients to force the artificial variables to be zero (which happens only if a feasible solution exists). At the same time, since computers are the main tool for solving LPs, M should not be unnecessarily too large, as this may lead to serious roundoff error. In the present example, the objective coefficients of x1
# and x2 are 4 and 1, respectively, and it appears reasonable to set M = 100
artifi = [-100 for m in range(1, Rmayorigual+1)]

C = np.concatenate([c, holguras, excesos, artifi])

# Matriz Coeficientes de las Restricciones
# Diemension de la base siempre sera una variable basica por restriccion
A = Matrix([[2, 1], [1, 1], [1, 2]])

# sizes of basic and nonbasic vectors
basicSize = A.shape[0]  # number of constraints, m
nonbasicSize = Rmenorigual + 2*Rmayorigual

# indices de Holgura, exceso y aritificales
I = Matrix(basicSize, nonbasicSize, [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1, 1])

# A aumentada con I
A = A.row_join(I)

# Lado derecho de las restricciones
b = np.array([20, 18, 12])

# global index tracker of variables of basic and nonbasic variables (objective)
# that is, index 1 corresponds with x_1, 2 with x_2 and so on.  So each index corresponds with a variable
x = [sp.Symbol('x'+str(x)) for x in range(1, len(c)+1)]
holguraS = [sp.Symbol('S'+str(s)) for s in range(1, Rmenorigual+1)]
excesosS = [sp.Symbol('S'+str(s))
            for s in range(Rmenorigual+1, Rmenorigual+Rmayorigual+1)]
artifiM = [sp.Symbol('A'+str(m))
           for m in range(Rmenorigual+1, Rmenorigual+Rmayorigual+1)]

X = np.concatenate([x, holguraS, excesosS, artifiM])


# Es optimo el problema?
itereacion = 0
# Paso1 Seleccionar las varaibles basicas
VbasicaI = [X[2], X[3], X[5]]
cbasica = [C[2], C[3], C[5]]
while itereacion < 10:
    # itreacion1

    # Paso2 Obtener B Inversa
    orden = util.getIndex(A, VbasicaI, X)
    A = np.matrix(A)
    B = util.getmatriz(A, orden)
    BI = np.linalg.inv(np.array(B, dtype=int))

    # Paso 2 Obtener BInversa*A y BInversa*bprima
    # BInversa*A
    BIA = BI @ A

    # BInversa*bprima
    BIb = BI @ b

    # Renglon de la funcion Objetivo
    # C sub b
    Cb = np.asarray(cbasica)
    # C base * BInversa*A
    CbBIA = Cb @ BIA

    # Z o Funcion Objetivo
    CbBIb = Cb @ BIb

    # costes reducidos Zj - Cj
    CbBIAmenosC = CbBIA - C

    # Si en este Vector todos los valores son >0 terminamos
    is_all_mzero = np.all(np.asarray(CbBIAmenosC) >= 0)
    if is_all_mzero:
        print('is over')
        print('la base como quedo', cbasica)
        print('zj-cj', CbBIAmenosC)
        print('Z ', CbBIb)
        print(VbasicaI, BIb)
        break
    # Seleccionar nueva base
    # Buscar la columna pivote varaible que entra
    colPivIN = util.seleccionarColPivote(CbBIAmenosC)

    # Buscar fila pivote

    indexbaseout = util.buscar_fila_pivote(BIA, colPivIN, BIb)

    # iteracion 2
    print(X[colPivIN], 'Nueva varaible que entra a la base')
    print(VbasicaI[indexbaseout], 'varaible que sale')
    # Vector base
    VbasicaI[indexbaseout] = X[colPivIN]
    # actualizar Cbase
    cbasica[indexbaseout] = C[colPivIN]
    print(VbasicaI)
    # print(cbasica)
    # print(CbBIAmenosC)
    # print(CbBIb)
    # print(BIb)
    itereacion = itereacion + 1
    print('-------------------------------')

print('termino el ciclo')
