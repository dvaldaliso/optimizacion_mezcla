import pandas as pd
# Para el caso que se vaya a ejcutar el ficher
#import util as u
from . import util as u
data = pd.read_excel(
    '/home/desarrollo/Documents/Proyectos/Tesis/Algoritmopython/data_modelo/assay_data/assayData.csv')


def datos(fc2, destil, crudos_precio):
    # Crudos
    tablaCrudo = u.getTablaCrudo(fc2, destil, crudos_precio, data)
    # Mezcla Crudos
    mezclaCrudo = u.getDataMezcla(data.values, tablaCrudo)
    # Productos Intermedios
    tablaPIntermedios = u.getDataPI(mezclaCrudo, destil)
    return tablaPIntermedios


if (__name__ == '__main__'):
    fc2 = 0.200
    destil = 8744
    crudos_precio = {'Ural': 2352.059*6.2898, 'Leona': 2303.83*6.2898}
    datos(fc2, destil, crudos_precio)
