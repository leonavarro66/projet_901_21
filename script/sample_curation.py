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
from my_function import classify_geodataframe, filter_and_clip_geodata

# Fichier de données nécessaire pour le masque
my_data_folder = '/home/onyxia/work/data'
my_result_folder_out = '/home/onyxia/work/projet_901_21/results/data'
vector_filename = os.path.join(my_data_folder, 'project', 'FORMATION_VEGETALE.shp')
emprise_filename = os.path.join(my_data_folder, 'project', 'emprise_etude.shp')
bd_foret_classee_decoupe_filename = os.path.join(my_result_folder_out, 'sample', 'Sample_BD_foret_T31TCJ.shp')

# Lecture du jeu de données de la bd_foret et de l'emprise d'etude
bd_foret = gpd.read_file(vector_filename)

# Création des dictionnaires pour le code et le nom
code_mapping = {
    "FF1-49-49": 11,
    "FF1-10-10": 11,
    "FF1-09-09": 11,
    "FF1G01-01": 12,
    "FF1-14-14": 13,
    "FP": 14,
    "FF1-00-00": 15,
    "FF1-00": 16,
    "FF2-91-91": 21,
    "FF2-63-63": 21,
    "FF2G61-61": 21,
    "FF2-90-90": 21,
    "FF2-52-52": 22,
    "FF2-81-81": 22,
    "FF2-80-80": 22,
    "FF2-64-64": 23,
    "FF2G53-53": 24,
    "FF2-51-51": 25,
    "FF2-00-00": 26,
    "FF2-00": 27,
    "FF32": 28,
    "FF31": 29,
}

name_mapping = {
    "FF1-49-49": "Autres feuillus",
    "FF1-10-10": "Autres feuillus",
    "FF1-09-09": "Autres feuillus",
    "FF1G01-01": "Chêne",
    "FF1-14-14": "Robinier",
    "FP": "Peupleraie",
    "FF1-00-00": "Mélange de feuillus",
    "FF1-00": "Feuillus en îlots",
    "FF2-91-91": "Autres conifères autre que pin",
    "FF2-63-63": "Autres conifères autre que pin",
    "FF2G61-61": "Autres conifères autre que pin",
    "FF2-90-90": "Autres conifères autre que pin",
    "FF2-52-52": "Autres Pin",
    "FF2-81-81": "Autres Pin",
    "FF2-80-80": "Autres Pin",
    "FF2-64-64": "Douglas",
    "FF2G53-53": "Pin laricio ou pin noir",
    "FF2-51-51": "Pin maritime",
    "FF2-00-00": "Mélange conifères",
    "FF2-00": "Conifères en îlots",
    "FF32": "Mélange conifères prépondérants et feuillus",
    "FF31": "Mélange de feuillus prépondérants et conifères",
}

# Traitement du GeoDataFrame
bd_foret_classee = classify_geodataframe(
    bd_foret, mapping_column="CODE_TFV", code_mapping=code_mapping, name_mapping=name_mapping
)

# Si le traitement est réussi, on découpe puis on enregistre.
if bd_foret_classee is not None:
    # Appel de la fonction pour découper la bd foret classée par rapport à l'emprise
    result = filter_and_clip_geodata(bd_foret_classee, emprise_filename, bd_foret_classee_decoupe_filename)
    if result is not None:
        print("Traitement terminé avec succès.")
    else:
        print("Le traitement a échoué.")
else:
    print("Le traitement a échoué.")
