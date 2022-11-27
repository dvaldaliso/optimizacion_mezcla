#! /usr/bin/python3
import numpy as np
import sympy as sp
from sympy.matrices import Matrix, eye, zeros, ones, diag, GramSchmidt
import Utilsimplex as util

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
artifi = [-10000 for m in range(1, Rmayorigual+1)]

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
# itreacion1
# Paso1 Seleccionar las varaibles basicas
VbasicaI1 = [X[2], X[3], X[5]]

# Paso2 Obtener B Inversa
orden = util.getIndex(A, VbasicaI1, X)
A = np.matrix(A)
B1 = util.getmatriz(A, orden)
B1I = np.linalg.inv(np.array(B1, dtype=int))

# Paso 2 Obtener BInversa*A y BInversa*bprima
# BInversa*A
B1IA = B1I @ A
B1IA = B1IA.astype(int)
# BInversa*bprima
B1Ib = B1I @ b
B1Ib = B1Ib.astype(int)

# Renglon de la funcion Objetivo
# C sub b

cbasica1 = [C[2], C[3], C[5]]
Cb1 = np.asarray(cbasica1)

CbB1IA = Cb1 @ B1IA

# Z o Funcion Objetivo
CbB1Ib = Cb1 @ B1Ib
CbB1IAmenosC = CbB1IA - C

# Si en este Vector todos los valores son >0 terminamos
is_all_mzero = np.all(np.asarray(CbB1IAmenosC) >= 0)
if is_all_mzero:
    print('is over')
# Seleccionar nueva base
# Buscar la columna pivote varaible que entra
colPiv1IN = util.seleccionarColPivote3(A, CbB1IAmenosC, X)
print(X[colPiv1IN], 'Nueva varaible que entra a la base')
# Buscar fila pivote
# Buscamos la columna de la varaible que entra en la matriz A original
indexbaseout = util.buscar_fila_pivote(np.transpose(A[:, [colPiv1IN]]), B1Ib)
print(VbasicaI1[indexbaseout], 'varaible que sale')
print('-------------------------------')

# iteracion 2
# Vector base
VbasicaI2 = VbasicaI1
VbasicaI2[indexbaseout] = X[colPiv1IN]

orden2 = util.getIndex(A, VbasicaI2, X)

matrizbase = util.getmatriz(A, orden2)
B2I = np.linalg.inv(np.array(matrizbase, dtype=int))

# BInversa*A
B2IA = B2I @ A
# BInversa*bprima
B2Ib = B2I @ b
cbasica2 = cbasica1  # actualizar Cbase
cbasica2[indexbaseout] = C[colPiv1IN]

# Funcion Objetivo
CbB2IA = cbasica2 @ B2IA
CbB2IA = np.array(CbB2IA, dtype=int)
CbB2Ib = cbasica2 @ B2Ib

CbB2IAMenosC = CbB2IA - C
# Si en este Vector todos los valores son >0 terminamos
is_all_mzero = np.all(np.asarray(CbB2IAMenosC) >= 0)
if is_all_mzero:
    print('is over')
colPiv2IN = util.seleccionarColPivote(A, CbB2IAMenosC, X)
filaPiv2Out = util.buscar_fila_pivote(np.transpose(B2IA[:, [colPiv2IN]]), B2Ib)

print(x[colPiv2IN], 'Nueva que entra')
print(VbasicaI2[filaPiv2Out], 'La que sale')

# iteracion 3
# Actualizar Vector base
VbasicaI3 = VbasicaI2
VbasicaI3[filaPiv2Out] = x[colPiv2IN]

orden3 = util.getIndex(A, VbasicaI3, X)
matrizbase3 = util.getmatriz(A, orden3)
# Inversa de base
B3I = np.linalg.inv(np.array(matrizbase3, dtype=int))

# BInversa*A
B3IA = B3I @ A
# BInversa*bprima
B3Ib = B3I @ b

cbasica3 = cbasica2  # actualizar Cbase
cbasica3[filaPiv2Out] = C[colPiv2IN]

CbB3IA = cbasica3 @ B3IA

CbB3Ib = cbasica3 @ B3Ib

CbB3IAMenosC = CbB3IA - C

# Si en este Vector todos los valores son >0 terminamos
is_all_mzero3 = np.all(np.asarray(CbB3IAMenosC) >= 0)
if is_all_mzero3:
    print('is over')

colPiv3IN = util.seleccionarColPivote3(A, CbB3IAMenosC, X)
filaPiv3Out = util.buscar_fila_pivote2(
    np.transpose(B3IA[:, [colPiv3IN]]), B3Ib)
print('----------------------')
print(X[colPiv3IN], 'Nueva que entra')
print(VbasicaI3[filaPiv3Out], filaPiv3Out, 'La que sale')

# 4 iteracion
# Actualizar Vector base
VbasicaI4 = VbasicaI3
VbasicaI4[filaPiv3Out] = X[colPiv3IN]

orden4 = util.getIndex(A, VbasicaI4, X)
matrizbase4 = util.getmatriz(A, orden4)


# Inversa de base
B4I = np.linalg.inv(np.array(matrizbase4, dtype=int))

# BInversa*A
B4IA = B4I @ A
# BInversa*bprima
B4Ib = B4I @ b

cbasica4 = cbasica3  # actualizar Cbase
cbasica4[filaPiv3Out] = C[colPiv3IN]
# FO
CbB4IA = cbasica4 @ B4IA
CbB4Ib = cbasica4 @ B4Ib
CbB4IAMenosC = CbB4IA - C

# Si en este Vector todos los valores son >0 terminamos
is_all_mzero4 = np.all(np.asarray(CbB4IAMenosC) >= 0)
if is_all_mzero4:
    print('is over')
print(CbB4IAMenosC)
print(CbB4Ib)
print(B4Ib)
