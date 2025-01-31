# -*- coding: utf-8 -*-
"""
@author: navarro leo, biou romain, sala mathieu
"""

import os
import sys
import geopandas as gpd
sys.path.append('/home/onyxia/work/projet_901_21/script')
from my_function import clip_raster, apply_mask, concat_bands, calculate_ndvi, custom_sort_key

# Initialisation des chemins nécessaires
RASTER_FOLDER = "/home/onyxia/work/data/images"
EMPRISE_FILE = "/home/onyxia/work/data/project/emprise_etude.shp"
MASQUE_FILE = "/home/onyxia/work/projet_901_21/results/data/img_pretraitees/masque_foret.tif"
OUTPUT_RESULT = "/home/onyxia/work/projet_901_21/results/data/img_pretraitees"
OUTPUT_DECOUPE_FOLDER = "/home/onyxia/work/data/project/pretraitement_decoupe"
OUTPUT_MASQUE_FOLDER = "/home/onyxia/work/data/project/pretraitement_masque"
OUTPUT_MASQUE_NDVI_FOLDER = "/home/onyxia/work/data/project/pretraitement_masque_ndvi"
OUTPUT_NDVI_FOLDER = "/home/onyxia/work/data/project/pretraitement_ndvi"

# Initialisation des variables nécessaires
SPATIAL_RES = 10  # Résolution spatiale de 10 m
DATA_TYPE = 'UInt16'  # Type de données de sortie
DRIVER = 'GTiff'  # Format GeoTIFF
NO_DATA = 0
EXPRESSION = 'A*(B==1)'  # Expression utilisé pour appliquer le masque forêt

emprise = gpd.read_file(EMPRISE_FILE)

# Créer le dossier de sortie s'il n'existe pas
if not os.path.exists(OUTPUT_DECOUPE_FOLDER):
    os.makedirs(OUTPUT_DECOUPE_FOLDER)

# Créer le dossier de sortie s'il n'existe pas
if not os.path.exists(OUTPUT_MASQUE_FOLDER):
    os.makedirs(OUTPUT_MASQUE_FOLDER)

# Créer le dossier de sortie s'il n'existe pas
if not os.path.exists(OUTPUT_MASQUE_NDVI_FOLDER):
    os.makedirs(OUTPUT_MASQUE_NDVI_FOLDER)

# Traitements pour générer le fichier multibandes concaténés
# Liste de tous les fichiers .tif dans le dossier de rasters
raster_files = [f for f in os.listdir(RASTER_FOLDER) if f.endswith('.tif')]

for raster_file in raster_files:
    # Charger l'image raster
    raster_path = os.path.join(RASTER_FOLDER, raster_file)

    # Séparer le nom de fichier et l'extension
    file_name, file_extension = os.path.splitext(raster_file)

    # Créer le nouveau nom de fichier
    new_file_name = f"{file_name}_decoupee{file_extension}"

    # Création du chemin de sortie
    output_path = os.path.join(OUTPUT_DECOUPE_FOLDER, new_file_name)

    # Appel de la fonction pour découper chaque raster en fonction de l'emprise
    clip_raster(raster_path, EMPRISE_FILE, emprise, output_path, SPATIAL_RES, DATA_TYPE, DRIVER)

# Liste de tous les fichiers raster découpés
raster_files_decoupee = [f for f in os.listdir(OUTPUT_DECOUPE_FOLDER) if f.endswith('.tif')]

# On boucle pour traiter chaque raster 1 par 1
for raster_file_decoupee in raster_files_decoupee:
    # Charger l'image raster
    raster_decoupee_path = os.path.join(OUTPUT_DECOUPE_FOLDER, raster_file_decoupee)

    # Séparer le nom du fichier de son extension
    file_name, file_extension = os.path.splitext(raster_file_decoupee)

    # Créer le nouveau nom de fichier
    new_file_name = f"{file_name}_masque{file_extension}"

    # Création du chemin de sortie
    output_path = os.path.join(OUTPUT_MASQUE_FOLDER, new_file_name)

    # Appel de la fonction pour mettre en place le masque forêt
    apply_mask(raster_decoupee_path, MASQUE_FILE, output_path, DATA_TYPE, DRIVER, EXPRESSION)

# Ordre des bandes chromatiques
band_order = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]

raster_files_masque = sorted(
    [os.path.join(OUTPUT_MASQUE_FOLDER, f) for f in os.listdir(OUTPUT_MASQUE_FOLDER) if f.endswith('.tif')],
    key=lambda x: custom_sort_key(os.path.basename(x), band_order)
    )
out_result = os.path.join(OUTPUT_RESULT, "Serie_temp_S2_allbands.tif")

concat_bands(raster_files_masque, out_result, DATA_TYPE, NO_DATA)

DATA_TYPE_NDVI = "Float32"
NO_DATA_NDVI = -9999
EXPRESSION_NDVI = '(A - B) / (A + B)'
# Traitements pour générer le NDVI
# Liste de tous les fichiers raster découpés
raster_files_decoupee = [f for f in os.listdir(OUTPUT_DECOUPE_FOLDER) if f.endswith('.tif')]

# On boucle pour traiter chaque raster 1 par 1
for raster_file_decoupee in raster_files_decoupee:
    # Charger l'image raster
    raster_decoupee_path = os.path.join(OUTPUT_DECOUPE_FOLDER, raster_file_decoupee)

    # Séparer le nom du fichier de son extension
    file_name, file_extension = os.path.splitext(raster_file_decoupee)

    # Créer le nouveau nom de fichier
    new_file_name = f"{file_name}_masque{file_extension}"

    # Création du chemin de sortie
    output_path = os.path.join(OUTPUT_MASQUE_NDVI_FOLDER, new_file_name)

    # Appel de la fonction pour mettre en place le masque forêt
    apply_mask(
        raster_decoupee_path,
        MASQUE_FILE,
        output_path,
        DATA_TYPE_NDVI,
        DRIVER,
        EXPRESSION_NDVI,
        NO_DATA_NDVI
        )

# Création des rasters NDVI
calculate_ndvi(OUTPUT_MASQUE_NDVI_FOLDER, OUTPUT_NDVI_FOLDER, EXPRESSION)

raster_files_ndvi = sorted(
    [os.path.join(OUTPUT_NDVI_FOLDER, f) for f in os.listdir(OUTPUT_NDVI_FOLDER) if f.endswith('.tif')]
    )

out_result = os.path.join(OUTPUT_RESULT, "Serie_temp_S2_ndvi.tif")

# Concaténation des 6 rasters préalablement créés
concat_bands(raster_files_ndvi, out_result, DATA_TYPE_NDVI, NO_DATA_NDVI)
