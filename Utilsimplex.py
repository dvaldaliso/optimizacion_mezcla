#! /usr/bin/python3
import numpy as np


def buscar_fila_pivote(BIA, colPivIN, bIb):

    columnaPivote = np.transpose(BIA[:, [colPivIN]])
    columnaPivote = list(list(columnaPivote.A)[0])
    bIb = list(list(bIb))

    # Si la columna pivote tiene valores negativos o igual a 0 no se tiene en cuenta
    verifica = listHavelessCero(columnaPivote)

    if verifica:
        indexdel = np.where(np.asarray(columnaPivote) <= 0)[0][0]
        del columnaPivote[indexdel]
        del bIb[indexdel]

    i = 0
    dlist = []
    for c in bIb:
        b = columnaPivote[i]
        dlist.append(c/b)
        i = i+1
    if verifica:
        print(dlist, 'Herere')
    return dlist.index(min(dlist))


def seleccionarColPivote(CbBIAMenosC):
    CbBIAMenosC = np.asarray(CbBIAMenosC)
    CbBIAMenosC = list(list(CbBIAMenosC)[0])

    mini = min(CbBIAMenosC)
    return CbBIAMenosC.index(mini)


def listHavelessCero(list):
    for x in list:
        if x <= 0:
            return True
    return False


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
