import os
import numpy as np
import geopandas as gpd
import subprocess
import logging

def decouper_raster(raster_path, shapefile_path, output_path):
    """
    Fonction pour découper un raster en fonction d'une emprise (shapefile).
    
    :param raster_path: Chemin vers le fichier raster (.tif)
    :param shapefile_path: Chemin vers le fichier shapefile (emprise)
    :param output_path: Chemin de sortie pour le fichier raster découpé
    """
    # Vérification que le fichier raster existe
    if not os.path.exists(raster_path):
        raise FileNotFoundError(f"Le fichier raster '{raster_path}' est introuvable.")
    
    # Vérification que le shapefile existe
    if not os.path.exists(shapefile_path):
        raise FileNotFoundError(f"Le shapefile '{shapefile_path}' est introuvable.")
    
    # Vérification que le dossier de sortie existe
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Commande pour découper le raster avec otbcli_ExtractROI
    cmd = (
        f"otbcli_ExtractROI -in {raster_path} "
        f"-mode fit "
        f"-mode.fit.vect {shapefile_path} "
        f"-out {output_path} uint16"
    )

    # Affichage de la commande pour vérification
    logging.info(f"Commande de découpe : {cmd}")

    try:
        # Exécution de la commande
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())  # Afficher la sortie standard

    except subprocess.CalledProcessError as e:
        # Gestion des erreurs
        error_msg = e.stderr.decode() if e.stderr else "Erreur inconnue."
        raise ValueError(f"Erreur lors de l'exécution de la commande otbcli_ExtractROI : {error_msg}")
    
    # Vérifier si le fichier de sortie a été créé
    if not os.path.exists(output_path):
        raise ValueError(f"L'image de sortie '{output_path}' n'a pas été créée.")
    
    logging.info(f"Découpage terminé, fichier sauvegardé à : {output_path}")
    
def reproject_raster(raster_path, output_path, reproj="EPSG:2154", no_data=0, data_type="UInt16"):
    """
    Fonction pour reprojeter, modifier le type de données et la valeur des nodatas d'un raster 
    en entrée.
    
    :param raster_path: Chemin vers le fichier raster (.tif)
    :param output_path: Chemin de sortie pour le fichier raster reprojeté
    :param reproj: Système de projection souhaité par défaut 2154
    :param no_data: Valeur de nodata pour l'image en sortie par défaut 0
    :param data_type: Type de données par défaut UInt16 
    """
    # Vérification que le fichier raster existe
    if not os.path.exists(raster_path):
        raise FileNotFoundError(f"Le fichier raster '{raster_path}' est introuvable.")
    
    # Vérification que le dossier de sortie existe
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Commande pour découper le raster avec otbcli_ExtractROI
    cmd = (
        f"gdalwarp -t_srs {reproj} "
        f"-ot {data_type} "
        f"-dstnodata {no_data} "
        f"{raster_path} "
        f"{output_path}"
    )

    # Affichage de la commande pour vérification
    logging.info(f"Commande de découpe : {cmd}")

    try:
        # Exécution de la commande
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())  # Afficher la sortie standard

    except subprocess.CalledProcessError as e:
        # Gestion des erreurs
        error_msg = e.stderr.decode() if e.stderr else "Erreur inconnue."
        raise ValueError(f"Erreur lors de l'exécution de la commande gdalwarp : {error_msg}")
    
    # Vérifier si le fichier de sortie a été créé
    if not os.path.exists(output_path):
        raise ValueError(f"L'image de sortie '{output_path}' n'a pas été créée.")
    
    logging.info(f"Découpage terminé, fichier sauvegardé à : {output_path}")

# Initialisation des chemins nécessaires
raster_folder = "/home/onyxia/work/data/images"
shapefile_path = "/home/onyxia/work/data/project/emprise_etude.shp"
output_decoupe_folder = "/home/onyxia/work/data/project/pretraitement_decoupe"
output_reproj_folder = "/home/onyxia/work/data/project/pretraitement_reproj"

shapefile = gpd.read_file(shapefile_path)

# Créer le dossier de sortie s'il n'existe pas
if not os.path.exists(output_decoupe_folder):
    os.makedirs(output_decoupe_folder)
    
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
    
    #decouper_raster(raster_path, shapefile_path, output_path)

# Liste de tous les fichiers .tif dans le dossier de rasters
raster_files_decoupee = [f for f in os.listdir(output_decoupe_folder) if f.endswith('.tif')]

for raster_file_decoupee in raster_files_decoupee:
    # Charger l'image raster découpee
    raster_decoupee_path = os.path.join(output_decoupe_folder, raster_file_decoupee)
    
    # Séparer le nom de fichier et l'extension
    file_name, file_extension = os.path.splitext(raster_file_decoupee)
    
    # Créer le nouveau nom de fichier
    new_file_name = f"{file_name}_reproject{file_extension}"
    
    # Création du chemin de sortie
    output_path = os.path.join(output_reproj_folder, new_file_name)
    
    # Appel de la fonction de reprojection
    #reproject_raster(raster_decoupee_path, output_path)