# -*- coding: utf-8 -*-
"""
@author: navarro leo, biou romain, sala mathieu
"""

# Import des bibliothèques nécessaire

import sys
import os
import geopandas as gpd
sys.path.append('/home/onyxia/work/libsigma')
sys.path.append('/home/onyxia/work/projet_901_21/script')
from my_function import rasterize

# Fichier de données nécessaire pour le masque
MY_DATA_FOLDER = '/home/onyxia/work/data'
MY_RESULT_FOLDER_OUT = '/home/onyxia/work/projet_901_21/results/data'
vector_filename = os.path.join(MY_DATA_FOLDER, 'project', 'FORMATION_VEGETALE.shp')
emprise_filename = os.path.join(MY_DATA_FOLDER, 'project', 'emprise_etude.shp')

# Lecture du jeu de données de la bd_foret et de l'emprise d'etude
bd_foret = gpd.read_file(vector_filename)
emprise = gpd.read_file(emprise_filename)

# Création d'un tableau où l'on retrouve les codes des types à exclure
types_a_exclure = ['LA4', 'LA6', 'FO0', 'FO1', 'FO2', 'FO3', 'FF0']

# Création de la nouvelle colonne en fonction de la condition
bd_foret['bin'] = bd_foret['CODE_TFV'].apply(lambda x: 1 if x not in types_a_exclure else 0)

# Sauvegarde du shape modifié pour ensuite rasteriser
bd_foret_filtree_filename = os.path.join(MY_DATA_FOLDER, 'project', 'bd_foret_filtree.shp')
bd_foret.to_file(bd_foret_filtree_filename)

# Paramètres de rasterisation
out_image = os.path.join(MY_RESULT_FOLDER_OUT,
                        'img_pretraitees',
                        'masque_foret.tif')  # Chemin vers l'image de sortie
FIELD_NAME = 'bin'  # Champ contenant les valeurs de rasterisation
SPATIAL_RES = 10  # Résolution spatiale de 10 m
DATA_TYPE = 'Byte'  # Type de données de sortie
DRIVER = 'GTiff'  # Format GeoTIFF

rasterize(bd_foret_filtree_filename, emprise, out_image, SPATIAL_RES, DATA_TYPE, DRIVER, FIELD_NAME)
