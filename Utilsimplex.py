#! /usr/bin/python3
import numpy as np


def buscar_fila_pivote(columnaPivote, bIb):

    columnaPivote = list(list(columnaPivote.A)[0])
    bIb = list(list(bIb))
    dlist = []
    i = 0
    for c in bIb:
        b = columnaPivote[i]
        dlist.append(c/b)
        i = i+1

    return dlist.index(min(dlist))


def buscar_fila_pivote2(columnaPivote, bIb):

    columnaPivote = list(list(columnaPivote.A)[0])
    bIb = list(list(bIb))

    # Si la columna pivote tiene valores negativos o igual a 0 no se tiene en cuenta
    verifica = np.all(np.asarray(columnaPivote) <= 0)
    if not verifica:
        indexdel = np.where(np.asarray(columnaPivote) <= 0)[0][0]
        del columnaPivote[indexdel]
        del bIb[indexdel]

    dlist = []
    i = 0
    for c in bIb:
        b = columnaPivote[i]
        dlist.append(c/b)
        i = i+1

    return dlist.index(min(dlist))


def getIndex(A, vbase, baseorig):
    orden = []
    for i in vbase:
        orden.append(np.where(baseorig == i)[0][0])
    return orden


def getmatriz(A, orden):
    newM = []
    i = 0
    for o in orden:
        if i == 0:
            newM = A[:, [o]]
        else:
            newM = np.concatenate([newM, A[:, [o]]], axis=1)
        i = i+1
    return newM


def seleccionarColPivote(A, CbBIAMenosC, X):
    print(CbBIAMenosC)
    print(type(CbBIAMenosC))
    CbBIAMenosC = list(list(CbBIAMenosC)[0])

    mini = min(CbBIAMenosC)
    return CbBIAMenosC.index(mini)


def seleccionarColPivote3(A, CbBIAMenosC, X):
    CbBIAMenosC = list(list(CbBIAMenosC.A)[0])
    mini = min(CbBIAMenosC)
    return CbBIAMenosC.index(mini)
