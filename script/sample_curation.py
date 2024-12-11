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
    "Forêt fermée d’un autre feuillu pur": 11,
    "Forêt fermée de châtaignier pur": 11,
    "Forêt fermée de hêtre pur": 11,
    "Forêt fermée de chênes décidus purs": 12,
    "Forêt fermée de robinier pur": 13,
    "Peupleraie": 14,
    "Forêt fermée à mélange de feuillus": 15,
    "Forêt fermée de feuillus purs en îlots": 16,
    "Forêt fermée d’un autre conifère pur autre que pin": 21,
    "Forêt fermée de mélèze pur": 21,
    "Forêt fermée de sapin ou épicéa": 21,
    "Forêt fermée à mélange d’autres conifères": 21,
    "Forêt fermée de pin sylvestre pur": 22,
    "Forêt fermée d'un autre pin pur": 22,
    "Forêt fermée à mélange de pins purs": 22,
    "Forêt fermée de douglas pur": 23,
    "Forêt fermée de pin laricio ou pin noir pur": 24,
    "Forêt fermée de pin maritime pur": 25,
    "Forêt fermée à mélange de conifères": 26,
    "Forêt fermée de conifères purs en îlots": 27,
    "Forêt fermée à mélange de conifères prépondérants et feuillus": 28,
    "Forêt fermée à mélange de feuillus prépondérants et conifères": 29,
}

name_mapping = {
    "Forêt fermée d’un autre feuillu pur": "Autres feuillus",
    "Forêt fermée de châtaignier pur": "Autres feuillus",
    "Forêt fermée de hêtre pur": "Autres feuillus",
    "Forêt fermée de chênes décidus purs": "Chêne",
    "Forêt fermée de robinier pur": "Robinier",
    "Peupleraie": "Peupleraie",
    "Forêt fermée à mélange de feuillus": "Mélange de feuillus",
    "Forêt fermée de feuillus purs en îlots": "Feuillus en îlots",
    "Forêt fermée d’un autre conifère pur autre que pin": "Autres conifères autre que pin",
    "Forêt fermée de mélèze pur": "Autres conifères autre que pin",
    "Forêt fermée de sapin ou épicéa": "Autres conifères autre que pin",
    "Forêt fermée à mélange d’autres conifères": "Autres conifères autre que pin",
    "Forêt fermée de pin sylvestre pur": "Autres Pin",
    "Forêt fermée d'un autre pin pur": "Autres Pin",
    "Forêt fermée à mélange de pins purs": "Autres Pin",
    "Forêt fermée de douglas pur": "Douglas",
    "Forêt fermée de pin laricio ou pin noir pur": "Pin laricio ou pin noir",
    "Forêt fermée de pin maritime pur": "Pin maritime",
    "Forêt fermée à mélange de conifères": "Mélange conifères",
    "Forêt fermée de conifères purs en îlots": "Conifères en îlots",
    "Forêt fermée à mélange de conifères prépondérants et feuillus": "Mélange conifères prépondérants et feuillus",
    "Forêt fermée à mélange de feuillus prépondérants et conifères": "Mélange de feuillus prépondérants et conifères",
}

# Traitement du GeoDataFrame
bd_foret_classee = classify_geodataframe(
    bd_foret, mapping_column="TFV", code_mapping=code_mapping, name_mapping=name_mapping
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
