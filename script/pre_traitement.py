import os
import sys
import re
import geopandas as gpd
sys.path.append('/home/onyxia/work/projet_901_21/script')
from my_function import clip_raster, apply_mask, concat_bands

# Initialisation des chemins nécessaires
raster_folder = "/home/onyxia/work/data/images"
emprise_file = "/home/onyxia/work/data/project/emprise_etude.shp"
masque_file = "/home/onyxia/work/projet_901_21/results/data/img_pretraitees/masque_foret.tif"
output_result = "/home/onyxia/work/projet_901_21/results/data/img_pretraitees"
output_decoupe_folder = "/home/onyxia/work/data/project/pretraitement_decoupe"
output_masque_folder = "/home/onyxia/work/data/project/pretraitement_masque"

# Initialisation des variables nécessaires
spatial_res = 10  # Résolution spatiale de 10 m
data_type = 'UInt16'  # Type de données de sortie
driver = 'GTiff'  # Format GeoTIFF
no_data = 0
expression = 'A*(B==1)'  # Expression utilisé pour appliquer le masque forêt

emprise = gpd.read_file(emprise_file)

# Créer le dossier de sortie s'il n'existe pas
if not os.path.exists(output_decoupe_folder):
    os.makedirs(output_decoupe_folder)

# Créer le dossier de sortie s'il n'existe pas
if not os.path.exists(output_masque_folder):
    os.makedirs(output_masque_folder)

# Liste de tous les fichiers .tif dans le dossier de rasters
raster_files = [f for f in os.listdir(raster_folder) if f.endswith('.tif')]

for raster_file in raster_files:
    # Charger l'image raster
    raster_path = os.path.join(raster_folder, raster_file)
    
    # Séparer le nom de fichier et l'extension
    file_name, file_extension = os.path.splitext(raster_file)
    
    # Créer le nouveau nom de fichier
    new_file_name = f"{file_name}_decoupee{file_extension}"
    
    # Création du chemin de sortie
    output_path = os.path.join(output_decoupe_folder, new_file_name)
    
    # Appel de la fonction pour découper chaque raster en fonction de l'emprise
    clip_raster(raster_path, emprise_file, emprise, output_path, spatial_res, data_type, driver)

# Liste de tous les fichiers raster découpés
raster_files_decoupee = [f for f in os.listdir(output_decoupe_folder) if f.endswith('.tif')]

# On boucle pour traiter chaque raster 1 par 1
for raster_file_decoupee in raster_files_decoupee:
    # Charger l'image raster
    raster_decoupee_path = os.path.join(output_decoupe_folder, raster_file_decoupee)
    
    # Séparer le nom du fichier de son extension
    file_name, file_extension = os.path.splitext(raster_file_decoupee)
    
    # Créer le nouveau nom de fichier
    new_file_name = f"{file_name}_masque{file_extension}"
    
    # Création du chemin de sortie
    output_path = os.path.join(output_masque_folder, new_file_name)
    
    # Appel de la fonction pour mettre en place le masque forêt
    apply_mask(raster_decoupee_path, masque_file, output_path, data_type, driver, expression)

# Ordre des bandes chromatiques
band_order = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]

# Fonction de tri personnalisé
def custom_sort_key(filename):
    # Modifier l'expression régulière pour capturer correctement B8A
    match = re.search(r"(\d{8}-\d{6}-\d{3}).*_(B(?:8A|\d{1,2}))_", filename)
    if match:
        date = match.group(1)
        band = match.group(2)
        # Retourner une clé basée sur l'ordre des dates et des bandes
        return (date, band_order.index(band))
    # Clé par défaut pour les fichiers ne correspondant pas au schéma
    return ("", float('inf'))


raster_files_masque = sorted([os.path.join(output_masque_folder, f) for f in os.listdir(output_masque_folder) if f.endswith('.tif')], key=lambda x: custom_sort_key(os.path.basename(x)))
out_result = os.path.join(output_result, "Serie_temp_S2_allbands.tif")

concat_bands(raster_files_masque, out_result, data_type, no_data)