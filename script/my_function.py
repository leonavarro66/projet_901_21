# -*- coding: utf-8 -*-
"""
@author: navarro leo, biou romain, sala mathieu
"""

import os
import geopandas as gpd
import subprocess
import logging
from osgeo import gdal

def rasterize(
    in_vector,
    ref_image,
    out_image,
    spatial_res,
    data_type,
    driver,
    field_name
):
    """
    Fonction permettant de rasteriser un shapefile en fonction d'une couche de référence.

    Paramètres :
    - in_vector (str): Chemin vers le shapefile à rasteriser.
    - ref_image (GeoDataFrame): GeoDataFrame représentant l'image de référence (utilisé pour l'emprise).
    - out_image (str): Chemin où l'image rasterisée sera sauvegardée.
    - spatial_res (float): Résolution spatiale à utiliser pour le raster.
    - data_type (str): Type de données pour le raster (par exemple, 'Byte', 'UInt16', etc.).
    - driver (str): Driver de format à utiliser pour la sortie (par exemple, 'GTiff' pour GeoTIFF).
    - field_name (str): Nom du champ à utiliser pour la rasterisation.

    Exceptions :
        ValueError: Si un paramètre est invalide ou si la commande échoue.
    """
    # Vérification des paramètres
    if not os.path.exists(in_vector):
        raise ValueError(f"Le fichier d'entrée '{in_vector}' n'existe pas.")
    if not isinstance(ref_image, gpd.GeoDataFrame):
        raise ValueError("Le paramètre 'ref_image' doit être un GeoDataFrame.")
    if not isinstance(spatial_res, (int, float)) or spatial_res <= 0:
        raise ValueError("La résolution spatiale doit être un nombre positif.")
    if not isinstance(field_name, str) or field_name.strip() == "":
        raise ValueError("Le nom du champ ('field_name') ne peut pas être vide.")

    # Extraction des coordonnées de l'emprise de l'image de référence
    try:
        xmin, ymin, xmax, ymax = ref_image.total_bounds
    except Exception as e:
        raise ValueError(f"Erreur lors de l'extraction des limites de l'emprise : {e}")
    
    # Définir la commande à exécuter avec les paramètres appropriés
    cmd_pattern = (
        "gdal_rasterize -a {field_name} "
        "-tr {spatial_res} {spatial_res} "
        "-te {xmin} {ymin} {xmax} {ymax} -ot {data_type} -of {driver} "
        "{in_vector} {out_image}"
    )

    # Remplir la commande avec les paramètres
    cmd = cmd_pattern.format(
        in_vector=in_vector, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax,
        spatial_res=spatial_res, out_image=out_image, field_name=field_name,
        data_type=data_type, driver=driver
    )

    # Affichage de la commande pour vérification
    logging.info(f"Commande de rasterisation : {cmd}")

    # Exécution de la commande
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())  # Afficher la sortie standard
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else "Erreur inconnue."
        raise ValueError(f"Erreur lors de l'exécution de la commande gdal_rasterize : {error_msg}")

    # Confirmer que l'image a été créée
    if not os.path.exists(out_image):
        raise ValueError(f"L'image de sortie '{out_image}' n'a pas été créée.")
    
    logging.info(f"Rasterisation terminée, fichier sauvegardé à : {out_image}")


def classify_geodataframe(
    gdf,
    mapping_column,
    code_mapping,
    name_mapping,
    code_column="Code",
    name_column="Nom",
):
    """
    Automatise le traitement des données pour mapper des valeurs et filtrer un GeoDataFrame.

    Paramètres :
    - gdf (GeoDataFrame) : Le GeoDataFrame à traiter.
    - mapping_column (str) : Le nom de la colonne utilisée pour effectuer le mapping.
    - code_mapping (dict) : Dictionnaire de correspondance pour les codes.
    - name_mapping (dict) : Dictionnaire de correspondance pour les noms.
    - code_column (str) : Nom de la colonne de sortie pour les codes (par défaut 'Code').
    - name_column (str) : Nom de la colonne de sortie pour les noms (par défaut 'Nom').

    Retour :
    - GeoDataFrame : Le GeoDataFrame nettoyé et enrichi.

    Exceptions :
    - ValueError : Si la colonne de mapping n'existe pas ou si le GeoDataFrame est vide.
    """
    try:
        # Vérifier si le GeoDataFrame est valide
        if gdf is None or gdf.empty:
            raise ValueError("Le GeoDataFrame fourni est vide ou invalide.")

        # Vérifier si la colonne utilisée pour le mapping existe
        if mapping_column not in gdf.columns:
            raise ValueError(f"La colonne '{mapping_column}' n'existe pas dans le GeoDataFrame.")

        # Ajouter les colonnes de mapping en utilisant .loc pour éviter l'erreur
        gdf.loc[:, code_column] = gdf[mapping_column].map(code_mapping)
        gdf.loc[:, name_column] = gdf[mapping_column].map(name_mapping)

        # Supprimer les lignes sans code associé (valeurs NaN dans la colonne de code)
        gdf = gdf.dropna(subset=[code_column])

        # Convertir la colonne des codes en entier (integer)
        gdf[code_column] = gdf[code_column].astype(int)

        # Retourner le GeoDataFrame modifié
        return gdf

    except ValueError as e:
        print(f"Erreur : {e}")
        return None
    except Exception as e:
        print(f"Une erreur inattendue s'est produite : {e}")
        return None


def filter_and_clip_geodata(
    to_clip_gdf,
    emprise_gdf_path,
    output_path
):
    """
    Filtre les polygones pour qu'ils soient entièrement inclus dans l'emprise 
    et réalise une découpe.

    Paramètres :
    - to_clip_gdf_path (GeoDataFrame) : GeoDataFrame du shapefile à découper.
    - emprise_gdf_path (str) : Chemin du fichier shapefile d'emprise.
    - output_path (str) : Chemin du fichier de sortie.

    Retour :
    - GeoDataFrame : Le GeoDataFrame découpé.
    """
    try:
        # Charger les fichiers
        emprise_gdf = gpd.read_file(emprise_gdf_path)

        # Vérifier les CRS
        if to_clip_gdf.crs != emprise_gdf.crs:
            print("Les CRS diffèrent. Reprojection de l'emprise pour correspondre...")
            emprise_gdf = emprise_gdf.to_crs(to_clip_gdf.crs)
        
        # Découpe du GeoDataFrame
        clipped_gdf = gpd.clip(to_clip_gdf, emprise_gdf)

        # Sauvegarde du fichier filtré
        clipped_gdf.to_file(output_path)
        print(f"Filtrage et découpe réalisés avec succès ! Résultat sauvegardé dans : {output_path}")

        return clipped_gdf

    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        return None

def count_polygons_by_class(gdf, class_column, selected_classes):
    """
    Compte le nombre de polygones par classe pour les classes sélectionnées.

    :param gdf: GeoDataFrame contenant les données des polygones.
    :param class_column: Nom de la colonne contenant les classes.
    :param selected_classes: Liste des classes à analyser.
    :return: Dictionnaire avec les classes comme clés et le nombre de polygones comme valeurs.
    """
    class_counts = {}

    for cls in selected_classes:
        count = gdf[gdf[class_column] == cls].shape[0]
        class_counts[cls] = count

    return class_counts

def stack_bands(bands_files, output_path):
    """
    Concatène plusieurs fichiers .tif (bandes) en une seule image multi-bandes.

    :param bands_files: Liste des chemins vers les fichiers .tif des bandes.
    :param output_path: Chemin du fichier de sortie (fichier .tif multi-bandes).
    """
    # Chargement de la première bande pour obtenir les paramètres de géoréférencement
    ref_ds = gdal.Open(bands_files[0])
    driver = gdal.GetDriverByName("GTiff")
    
    # Création d'une image de sortie avec autant de bandes que le nombre d'entrées
    out_ds = driver.Create(
        output_path,
        ref_ds.RasterXSize,
        ref_ds.RasterYSize,
        len(bands_files),
        ref_ds.GetRasterBand(1).DataType,
    )
    
    # Copie des métadonnées de géoréférencement
    out_ds.SetGeoTransform(ref_ds.GetGeoTransform())
    out_ds.SetProjection(ref_ds.GetProjection())
    
    # Ajout de chaque bande au fichier de sortie
    for i, band_path in enumerate(bands_files):
        band_ds = gdal.Open(band_path)
        band_data = band_ds.GetRasterBand(1).ReadAsArray()
        out_ds.GetRasterBand(i + 1).WriteArray(band_data)
        band_ds = None  # Fermer le fichier après utilisation
    
    # Fermer le fichier de sortie
    out_ds = None
    print(f"Image multi-bandes créée : {output_path}")