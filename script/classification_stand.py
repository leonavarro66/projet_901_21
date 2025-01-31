# -*- coding: utf-8 -*-
"""
@author: navarro leo, biou romain, sala mathieu
"""

import sys
sys.path.append('/home/onyxia/work/projet_901_21/script')
sys.path.append('/home/onyxia/work/libsigma')

import os
import geopandas as gpd
from rasterstats import zonal_stats
from sklearn.metrics import confusion_matrix

# Personnal libraries
from my_function import classify_polygon
import plots

MY_FOLDER_RESULT = '/home/onyxia/work/projet_901_21/results/data'

# Charger les fichiers d'entrées
raster_path = os.path.join(MY_FOLDER_RESULT, 'classif', 'carte_essences_echelle_pixel.tif')
bd_foret_path = os.path.join(MY_FOLDER_RESULT, 'sample', 'Sample_BD_foret_T31TCJ.shp')

# Charger le shapefile
bd_foret = gpd.read_file(bd_foret_path)

# Extraire les noms associés aux codes dynamiquement depuis la bd_foret
if "Code" in bd_foret.columns and "Nom" in bd_foret.columns:
    code_to_name = dict(zip(bd_foret["Code"], bd_foret["Nom"]))

# Calculer la surface de chaque polygone en hectares
bd_foret["surface_ha"] = bd_foret.geometry.area / 10000  # Conversion m² -> ha

# Calculer les statistiques zonales
stats = zonal_stats(bd_foret_path, raster_path, categorical=True, nodata=0)

# Assigner les classes de peuplement
bd_foret["codepredit"] = [classify_polygon(s, a) for s, a in zip(stats, bd_foret["surface_ha"])]

# On drop la colonne de la surface car on ne doit pas l'avoir dans le fichier final
bd_foret = bd_foret.drop(columns=["surface_ha"])

# On réecrit le fichier de polygones d'échantillons avec la nouvelle colonne 'codepredit'
bd_foret.to_file(bd_foret_path)

# Calculer la matrice de confusion
bd_foret_valid = bd_foret[bd_foret["codepredit"] != -1]  # Exclure les No Data

y_true = bd_foret_valid["Code"]
y_pred = bd_foret_valid["codepredit"]

cm = confusion_matrix(y_true, y_pred)
print("Matrice de confusion :")
print(cm)

unique_labels = sorted(set(y_true) | set(y_pred))
plots.plot_cm(
    cm,
    labels=[str(label) for label in unique_labels],
    out_filename="/home/onyxia/work/data/project/ma_cm.png"
    )
