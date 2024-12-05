# -*- coding: utf-8 -*-
"""
@author: navarro leo, biou romain, sala mathieu
"""

# Import des bibliothèques nécessaire

import sys
sys.path.append('/home/onyxia/work/libsigma')
import os
import geopandas as gpd
import read_and_write as rw


# Fichier de données
my_data_folder = '/home/onyxia/work/data'
my_result_folder_out = '/home/onyxia/work/projet_901_21/results/data/img_pretraitees'
vector_filename = os.path.join(my_data_folder, 'project/FORMATION_VEGETALE.shp')

bd_foret = gpd.read_file(vector_filename)

# Transformation des données
types_a_exclure = ['LA4', 'LA6', 'FO0', 'FO1', 'FO2', 'FO3', 'FF0']
bd_foret_filtrée = bd_foret[~bd_foret['CODE_TFV'].isin(types_a_exclure)]


filename = os.path.join(my_data_folder, 'project/FORMATION_VEGETALE.shp')
out_ndvi_filename = os.path.join(my_result_folder_out, 'masque_foret.tif')

# load data
data_set = rw.open_image(filename)
img = rw.load_img_as_array(filename)

print(data_set)
print(img)
