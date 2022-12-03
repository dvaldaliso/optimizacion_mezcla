#! /usr/bin/python3.9
from docplex.mp.model import Model
# PARAMETROS

pInt = ['Nvl', 'Np', 'Ref']
pFin = ['G83', 'G90', 'G94']
# productos Intermedios caracterisiticas
pIntC = {
    'Nvl': {'Rendimiento': 0.04776, 'RBN': 55.48230, 'RVP': 0.61140, 'PAzufre': 64.72995, 'Densidad': 0.66703},
    'Np':  {'Rendimiento': 0.151957, 'RBN': 52.52652, 'RVP': 0.03713, 'PAzufre': 345.32027, 'Densidad': 0.74964},
    'Ref': {'Rendimiento': 0.82455, 'RBN': 65.13, 'RVP': 0.02998, 'PAzufre': 0.78492, 'Densidad': 0.78712}
}
# productos Finales caracterisiticas
pFinC = {
    'G83': {'price': 3300, 'RBNmin': 58.89, 'RVPmax': 0.617498832595756, 'Azufemax': 1000, 'Densidadmin': 0.7200},
    'G90': {'price': 3500, 'RBNmin': 62.36, 'RVPmax': 0.617498832595756, 'Azufemax': 1000, 'Densidadmin': 0.7200},
    'G94': {'price': 3746, 'RBNmin': 65.13, 'RVPmax': 0.617498832595756, 'Azufemax': 1000, 'Densidadmin': 0.7200}
}

demandaPF = {
    'G83': {'Min': 0, 'Max': 'M'},
    'G90': {'Min': 750, 'Max': 'M'},
    'G94': {'Min': 300, 'Max': 'M'}
}

m = Model(name='Mezcla de Gasolina')
