# -*- coding: utf-8 -*-
"""
@author: navarro leo, biou romain, sala mathieu
"""

import os
import re
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
import logging
import numpy as np
from osgeo import gdal


def rasterize(
    in_vector,
    ref_image,
    out_image,
    spatial_res,
    data_type,
    driver,
    field_name,
    proj="EPSG:2154",
    no_data=0
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
    - proj (str): Projection par défaut EPSG:2154
    - no_data (int): Valeur de no data
    
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
        "-tr {spatial_res} {spatial_res} -a_nodata {no_data} "
        "-te {xmin} {ymin} {xmax} {ymax} -ot {data_type} -of {driver} "
        "-a_srs {proj} -tap "
        "{in_vector} {out_image}"
    )

    # Remplir la commande avec les paramètres
    cmd = cmd_pattern.format(
        in_vector=in_vector, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax,
        spatial_res=spatial_res, out_image=out_image, field_name=field_name,
        data_type=data_type, driver=driver, proj=proj, no_data=no_data
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


def rasteriser_avec_gdal(in_vector, out_image, resolution_spatiale, nom_champ, type_donnee="UInt16"):
    """
    Rasterise un fichier vecteur en un fichier raster en utilisant GDAL.

    Paramètres :
    - in_vector (str) : Chemin vers le fichier vecteur d'entrée (shapefile).
    - out_image (str) : Chemin vers le fichier raster de sortie.
    - resolution_spatiale (float) : Résolution spatiale pour le raster.
    - nom_champ (str) : Nom du champ d'attribut à graver dans le raster.
    - type_donnee (str) : Type de données GDAL pour le raster (par défaut : UInt16).

    Retourne :
    - None
    """
    try:
        # Ouvrir le fichier vecteur
        vector_ds = gdal.OpenEx(in_vector, gdal.OF_VECTOR)
        if vector_ds is None:
            raise RuntimeError(f"Impossible d'ouvrir le fichier vecteur : {in_vector}")

        # Obtenir la couche à partir du dataset vecteur
        couche = vector_ds.GetLayer()

        # Obtenir l'étendue de la couche vecteur
        extent = couche.GetExtent()
        xmin, xmax, ymin, ymax = extent

        # Calculer les dimensions du raster
        cols = int((xmax - xmin) / resolution_spatiale)
        rows = int((ymax - ymin) / resolution_spatiale)

        # Créer le dataset raster
        driver = gdal.GetDriverByName("GTiff")
        raster_ds = driver.Create(
            out_image,
            cols,
            rows,
            1,
            gdal.GetDataTypeByName(type_donnee)
        )

        if raster_ds is None:
            raise RuntimeError(f"Impossible de créer le fichier raster : {out_image}")

        # Définir la géotransformation et la projection
        geotransform = (xmin, resolution_spatiale, 0, ymax, 0, -resolution_spatiale)
        raster_ds.SetGeoTransform(geotransform)
        raster_ds.SetProjection(couche.GetSpatialRef().ExportToWkt())

        # Rasteriser la couche vecteur
        gdal.RasterizeLayer(
            raster_ds,
            [1],
            couche,
            options=[f"ATTRIBUTE={nom_champ}"]
        )

        # Fermer les datasets
        raster_ds = None
        vector_ds = None

        logging.info(f"Rasterisation terminée. Résultat enregistré dans {out_image}")

    except Exception as e:
        logging.error(f"Erreur lors de la rasterisation : {e}")
        raise


def count_pixels_by_class(gdf, colonne_classe, classes_selectionnees):
    """
    Compte le nombre de pixels par classe en rasterisant les polygones.

    Paramètres :
    - gdf (GeoDataFrame) : GeoDataFrame contenant les polygones.
    - colonne_classe (str) : Nom de la colonne contenant les valeurs des classes.
    - classes_selectionnees (list) : Liste des classes à analyser.

    Retourne :
    - dict : Un dictionnaire avec les classes comme clés et le nombre de pixels comme valeurs.
    """
    # Créer des chemins temporaires pour les fichiers vecteur et raster
    vecteur_temp = "/tmp/temp_vector.shp"
    raster_temp = "/tmp/temp_raster.tif"
    resolution_spatiale = 10  # Définir la résolution spatiale

    try:
        # Enregistrer le GeoDataFrame en tant que shapefile temporaire
        gdf.to_file(vecteur_temp)

        # Rasteriser le shapefile
        rasteriser_avec_gdal(
            in_vector=vecteur_temp,
            out_image=raster_temp,
            resolution_spatiale=resolution_spatiale,
            nom_champ=colonne_classe
        )

        # Ouvrir le raster et compter les pixels
        raster_ds = gdal.Open(raster_temp)
        raster_array = raster_ds.GetRasterBand(1).ReadAsArray()

        # Compter les pixels pour chaque classe
        compteur_pixels = {}
        for classe in classes_selectionnees:
            compteur_pixels[classe] = np.sum(raster_array == classe)

        # Supprimer les fichiers temporaires
        os.remove(vecteur_temp)
        os.remove(raster_temp)

        return compteur_pixels

    except Exception as e:
        logging.error(f"Erreur lors du comptage des pixels : {e}")
        return {}

    finally:
        # S'assurer que les fichiers temporaires sont supprimés
        if os.path.exists(vecteur_temp):
            os.remove(vecteur_temp)
        if os.path.exists(raster_temp):
            os.remove(raster_temp)


def prepare_violin_plot_data(gdf, class_column, pixel_column):
    """
    Prépare les données pour un "violin plot" montrant la distribution du nombre de pixels par polygone, par classe.

    :param gdf: GeoDataFrame contenant les données des polygones.
    :param class_column: Nom de la colonne contenant les classes.
    :param pixel_column: Nom de la colonne contenant le nombre de pixels.
    :return: DataFrame avec les colonnes "Classe" et "Pixels".
    """
    # Vérifier que les colonnes nécessaires existent
    if class_column not in gdf.columns or pixel_column not in gdf.columns:
        raise ValueError(f"Les colonnes {class_column} et {pixel_column} doivent exister dans le GeoDataFrame.")

    # Filtrer les lignes ayant des valeurs non nulles dans les colonnes spécifiées
    filtered_gdf = gdf.dropna(subset=[class_column, pixel_column])

    # Construire un DataFrame avec les classes et les pixels
    violin_data = filtered_gdf[[class_column, pixel_column]].rename(
        columns={class_column: "Classe", pixel_column: "Pixels"}
    )

    return violin_data

from osgeo import gdal

def clip_raster(
    in_raster,
    ref_image,
    ref_image_gdf,
    out_image,
    spatial_res,
    data_type,
    driver,
    proj="EPSG:2154",
    no_data=0
):
    """
    Fonction permettant de découper un raster en fonction d'une couche de référence.

    Paramètres :
    - in_raster (str): Chemin vers le raster à découper.
    - ref_image (str): Chemin vers le shape de l'emprise.
    - ref_image_gdf (GeoDataFrame): GeoDataFrame représentant l'image de référence (utilisé pour l'emprise).
    - out_image (str): Chemin où l'image découpée sera sauvegardée.
    - spatial_res (float): Résolution spatiale à utiliser pour le raster.
    - data_type (str): Type de données pour le raster (par exemple, 'Byte', 'UInt16', etc.).
    - driver (str): Driver de format à utiliser pour la sortie (par exemple, 'GTiff' pour GeoTIFF).
    - proj (str): Projection par défaut EPSG:2154
    - no_data (int): Valeur de no data
    
    Exceptions :
        ValueError: Si un paramètre est invalide ou si la commande échoue.
    """
    # Vérification des paramètres
    if not os.path.exists(in_raster):
        raise ValueError(f"Le fichier d'entrée '{in_raster}' n'existe pas.")
    if not os.path.exists(ref_image):
        raise ValueError(f"Le fichier d'entrée '{ref_image}' n'existe pas.")
    if not isinstance(ref_image_gdf, gpd.GeoDataFrame):
        raise ValueError("Le paramètre 'ref_image_gdf' doit être un GeoDataFrame.")
    if not isinstance(spatial_res, (int, float)) or spatial_res <= 0:
        raise ValueError("La résolution spatiale doit être un nombre positif.")

    # Extraction des coordonnées de l'emprise de l'image de référence
    try:
        xmin, ymin, xmax, ymax = ref_image_gdf.total_bounds
    except Exception as e:
        raise ValueError(f"Erreur lors de l'extraction des limites de l'emprise : {e}")
    
    # Définir la commande à exécuter avec les paramètres appropriés
    cmd_pattern = (
        "gdalwarp -cutline {ref_image} "
        "-crop_to_cutline "
        "-tr {spatial_res} {spatial_res} -dstnodata {no_data} "
        "-te {xmin} {ymin} {xmax} {ymax} -ot {data_type} -of {driver} "
        "-t_srs {proj} -tap "
        "{in_raster} {out_image}"
    )

    # Remplir la commande avec les paramètres
    cmd = cmd_pattern.format(
        in_raster=in_raster, xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax,
        spatial_res=spatial_res, out_image=out_image,
        data_type=data_type, driver=driver, proj=proj, no_data=no_data, ref_image=ref_image
    )

    # Affichage de la commande pour vérification
    logging.info(f"Commande de découpage raster : {cmd}")

    # Exécution de la commande
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())  # Afficher la sortie standard
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else "Erreur inconnue."
        raise ValueError(f"Erreur lors de l'exécution de la commande gdalwarp : {error_msg}")

    # Confirmer que l'image a été créée
    if not os.path.exists(out_image):
        raise ValueError(f"L'image de sortie '{out_image}' n'a pas été créée.")

    logging.info(f"Découpage terminée, fichier sauvegardé à : {out_image}")


def apply_mask(
    in_raster,
    masque_image,
    out_image,
    data_type,
    driver,
    expression,
    no_data=0
):
    """
    Fonction permettant d'appliquer un masque sur un raster.

    Paramètres :
    - in_raster (str): Chemin vers le raster où appliquer le masque.
    - masque_image (str): Chemin vers le masque.
    - out_image (str): Chemin où l'image avec le masque sera sauvegardée.
    - data_type (str): Type de données pour le raster (par exemple, 'Byte', 'UInt16', etc.).
    - driver (str): Driver de format à utiliser pour la sortie (par exemple, 'GTiff' pour GeoTIFF).
    - expression (str): Expression à effectuer pour le masque
    - no_data (int): Valeur de no data
    
    Exceptions :
        ValueError: Si un paramètre est invalide ou si la commande échoue.
    """
    # Vérification des paramètres
    if not os.path.exists(in_raster):
        raise ValueError(f"Le fichier d'entrée '{in_raster}' n'existe pas.")
    # Vérification des paramètres
    if not os.path.exists(masque_image):
        raise ValueError(f"Le fichier d'entrée '{masque_image}' n'existe pas.")
    
    # Définir la commande à exécuter avec les paramètres appropriés
    cmd_pattern = (
        "gdal_calc "
        "--calc '{exp}' "
        "--format {driver} --type {data_type} "
        "--NoDataValue {no_data} "
        "-A {in_raster} "
        "-B {masque} "
        "--outfile {out_image}"
    )

    # Remplir la commande avec les paramètres
    cmd = cmd_pattern.format(
        in_raster=in_raster, masque=masque_image, exp=expression,
        out_image=out_image,
        data_type=data_type, driver=driver, no_data=no_data
    )

    # Affichage de la commande pour vérification
    logging.info(f"Commande de calcul raster : {cmd}")

    # Exécution de la commande
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())  # Afficher la sortie standard
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else "Erreur inconnue."
        raise ValueError(f"Erreur lors de l'exécution de la commande gdal_calc : {error_msg}")

    # Confirmer que l'image a été créée
    if not os.path.exists(out_image):
        raise ValueError(f"L'image de sortie '{out_image}' n'a pas été créée.")
    
    logging.info(f"Calcul terminée, fichier sauvegardé à : {out_image}")


def concat_bands(input_files, output_file, data_type, no_data, separate=True, output_format="GTiff"):
    """
    Fusionne plusieurs rasters mono-bande en un seul fichier raster.

    Args:
        input_files (list): Liste des fichiers raster à fusionner.
        output_file (str): Chemin du fichier de sortie.
        data_type (str): Type de données.
        no_data (int): Valeur des nodatas
        separate (bool): Si True, chaque raster sera placé dans une bande distincte.
        output_format (str): Format du fichier de sortie (par défaut "GTiff").
        
    """
    # Définir la commande avec les paramètres appropriés
    cmd_pattern = (
        "gdal_merge.py "
        "-o {output_raster} "
        "-n {no_data} -a_nodata {no_data} -ot {data_type} "
        "-of {driver} "
        "{separate_flag} "
        "{input_files}"
    )

    # Construire la commande avec les paramètres
    separate_flag = "-separate" if separate else ""
    input_files = " ".join(input_files)
    cmd = cmd_pattern.format(
        output_raster=output_file,
        driver=output_format,
        no_data=no_data,
        data_type=data_type,
        separate_flag=separate_flag,
        input_files=input_files
    )

    # Affichage de la commande pour vérification
    logging.info(f"Commande de fusion des rasters : {cmd}")

    # Exécution de la commande
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())  # Afficher la sortie standard
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else "Erreur inconnue."
        raise ValueError(f"Erreur lors de l'exécution de la commande gdal_merge.py : {error_msg}")


def calculate_ndvi(input_folder, output_folder, expression, data_type="Float32", driver="GTiff", no_data=-9999):
    """
    Calcule le NDVI pour chaque date à partir des fichiers raster dans le dossier d'entrée,
    et sauvegarde les résultats dans un fichier raster multibandes.

    Args

    - input_folder (str): Dossier contenant les fichiers raster (B4 et B8)
    - output_folder (str): Dossier où les fichiers NDVI seront sauvegardés
    - expression (str): Expression à calculer
    - data_type (str): Type de données pour le raster (par exemple, 'Byte', 'UInt16', etc.).
    - driver (str): Driver de format à utiliser pour la sortie (par exemple, 'GTiff' pour GeoTIFF).
    - no_data (int): Valeur de no data
    """
    # Assurez-vous que le dossier temporaire existe
    os.makedirs(output_folder, exist_ok=True)

    # Expression régulière pour extraire la date et la bande
    date_regex = r"(\d{8}-\d{6}-\d{3})"
    band_regex = r"_(B\d{1,2})_"

    # Liste des fichiers triés
    raster_files = sorted(
        [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith('.tif')],
        key=lambda x: (re.search(date_regex, os.path.basename(x)).group(1), x)
    )

    # Grouper les fichiers par date
    dates = {}
    for raster in raster_files:
        filename = os.path.basename(raster)
        date_match = re.search(date_regex, filename)
        band_match = re.search(band_regex, filename)
        if date_match and band_match:
            date = date_match.group(1)
            band = band_match.group(1)
            if date not in dates:
                dates[date] = {}
            dates[date][band] = raster

    # Calcul du NDVI pour chaque date
    for date, bands in dates.items():
        if "B4" in bands and "B8" in bands:
            b4_path = bands["B4"]
            b8_path = bands["B8"]

            # Chemin de sortie pour le NDVI
            output_path = os.path.join(output_folder, f"NDVI_{date}.tif")

            # Définir la commande
            cmd_pattern = (
                "gdal_calc.py "
                "--calc '{exp}' "
                "--format {driver} --type {data_type} "
                "--NoDataValue {no_data} "
                "-A {in_raster} "
                "-B {masque} "
                "--outfile {out_image}"
            )

            # Remplir la commande avec les paramètres
            cmd = cmd_pattern.format(
                in_raster=b8_path,
                masque=b4_path,
                exp=expression,
                out_image=output_path,
                data_type=data_type,
                driver=driver,
                no_data=no_data
            )

            # Exécution de la commande
            logging.info(f"Commande de calcul raster : {cmd}")
            try:
                result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logging.info(result.stdout.decode())  # Afficher la sortie standard
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode() if e.stderr else "Erreur inconnue."
                raise ValueError(f"Erreur lors de l'exécution de la commande gdal_calc : {error_msg}")
        else:
            logging.warning(f"Bandes nécessaires (B4, B8) manquantes pour la date {date}")


def analyze_phenology_gdal_alternative(ndvi_raster, shapefile, output_folder, dates):
    """
    Analyse la phénologie des classes de la BD forêt classifié et produit un graphique amélioré.

    :param ndvi_raster: Chemin du raster multibandes NDVI
    :param shapefile: Chemin du shapefile de la BD forêt classifié
    :param output_folder: Dossier pour sauvegarder les résultats
    :param dates: Liste des dates associées aux bandes du raster NDVI
    """
    # Classes pertinentes
    selected_classes = [12, 13, 14, 23, 24, 25]
    os.makedirs(output_folder, exist_ok=True)

    # Charger les noms des classes à partir du shapefile
    gdf = gpd.read_file(shapefile)
    class_names = {
        row['Code']: row['Nom']
        for _, row in gdf.iterrows() if row['Code'] in selected_classes
    }

    # Initialisation des résultats
    stats = {cls: {"mean": [], "std": []} for cls in selected_classes}
    bands_count = 6  # Supposons que le raster NDVI contient 6 bandes temporelles

    for i in range(1, bands_count + 1):
        logging.info(f"Traitement de la bande {i}...")
        temp_band_raster = f"/home/onyxia/work/data/project/tmp/temp_band_{i}.tif"

        # Extraire la bande NDVI i
        cmd_extract_band = (
            f"gdal_translate -b {i} {ndvi_raster} {temp_band_raster} "
            f"-of GTiff -q"
        )
        subprocess.run(cmd_extract_band, shell=True, check=True)

        for cls in selected_classes:
            logging.info(f"Traitement de la classe {cls}...")

            # Créer un masque pour la classe
            temp_mask = f"/home/onyxia/work/data/project/tmp/temp_mask_{cls}.shp"
            cmd_create_mask = (
                f"ogr2ogr -where \"Code={cls}\" {temp_mask} {shapefile}"
            )
            subprocess.run(cmd_create_mask, shell=True, check=True)

            # Découper le raster par la classe
            temp_cropped_raster = f"/home/onyxia/work/data/project/tmp/temp_cropped_band_{i}_class_{cls}.tif"
            cmd_crop_raster = (
                f"gdalwarp -cutline {temp_mask} -crop_to_cutline -dstnodata -9999 "
                f"{temp_band_raster} {temp_cropped_raster}"
            )
            subprocess.run(cmd_crop_raster, shell=True, check=True)

            # Obtenir les statistiques avec gdalinfo
            cmd_get_stats = f"gdalinfo -stats {temp_cropped_raster}"
            result = subprocess.run(
                cmd_get_stats, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stats_output = result.stdout.decode()

            # Extraire les statistiques
            mean_value, std_value = None, None
            for line in stats_output.split("\n"):
                if "STATISTICS_MEAN=" in line:
                    mean_value = float(line.split("=")[-1])
                if "STATISTICS_STDDEV=" in line:
                    std_value = float(line.split("=")[-1])

            # Sauvegarder les résultats
            stats[cls]["mean"].append(mean_value)
            stats[cls]["std"].append(std_value)

            # Nettoyer les fichiers temporaires
            os.remove(temp_mask)
            os.remove(temp_cropped_raster)

        # Supprimer le raster temporaire
        os.remove(temp_band_raster)

    # Création du graphique
    logging.info("Création du graphique des signatures temporelles...")
    plt.figure(figsize=(14, 8))
    for cls in selected_classes:
        mean_values = stats[cls]["mean"]
        std_values = stats[cls]["std"]

        # Tracer la moyenne
        plt.plot(
            dates, mean_values, label=f"Classe {cls} - {class_names.get(cls, 'Inconnu')} (Moyenne)", linewidth=2
        )

        # Tracer l'écart type (points et lignes discontinues)
        plt.plot(
            dates, std_values, label=f"Classe {cls} - {class_names.get(cls, 'Inconnu')} (Écart Type)",
            linestyle="--", linewidth=1.5
        )

    # Personnalisation du graphique
    plt.title("Signature temporelle du NDVI par classe", fontsize=16)
    plt.xlabel("Dates", fontsize=12)
    plt.ylabel("NDVI", fontsize=12)
    plt.xticks(rotation=45, fontsize=10)
    plt.yticks(fontsize=10)
    plt.legend(title="Classes et statistiques", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.6)

    # Sauvegarder le graphique
    output_path = os.path.join(output_folder, "temp_mean_ndvi.png")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    logging.info(f"Graphique sauvegardé : {output_path}")


# Fonction pour calculer la distance au centroïde
def calculate_distance(centroid, pixel_x, pixel_y):
    """Fonction qui permet de calculer la distance au centroide

    Args:
        centroid (int): Coordonnées du centroide
        pixel_x (int): Coordonnées du pixel en X 
        pixel_y (int): Coordonnées du pixel en Y

    Returns:
        int: La distance au centroide
    """
    return np.sqrt((centroid[0] - pixel_x) ** 2 + (centroid[1] - pixel_y) ** 2)

def plot_class_quality(report, accuracy, out_filename=None):
    """
    Display a plot bar of quality metrics of each class.

    Parameters
    ----------
    report : dict
        Classification report (output of the `classification_report` function
        of scikit-learn.
    accuracy : float
        Overall accuracy.
    out_filename : str (optional)
        If indicated, the chart is saved at the `out_filename` location
    """
    report_df = pd.DataFrame.from_dict(report)
    # drop columns (axis=1) same as numpy
    try :
        report_df = report_df.drop(['accuracy', 'macro avg', 'weighted avg'],
                                   axis=1, errors="ignore")
    except KeyError:
        report_df = report_df.drop(['micro avg', 'macro avg', 'weighted avg'],
                                   axis=1, errors="ignore")
    # drop rows (axis=0) same as numpy
    report_df = report_df.drop(['support'], axis=0, errors="ignore")
    fig, ax = plt.subplots(figsize=(10, 7))
    ax = report_df.T.plot.bar(ax=ax, zorder=2)

    # custom : information
    ax.text(0.05, 0.95, 'OA : {:.2f}'.format(accuracy), fontsize=14)
    ax.set_title('Class quality estimation')

    # custom : cuteness
    # background color
    ax.set_facecolor('ivory')
    # labels
    x_label = ax.get_xlabel()
    ax.set_xlabel(x_label, fontdict={'fontname': 'Sawasdee'}, fontsize=14)
    y_label = ax.get_ylabel()
    ax.set_ylabel(y_label, fontdict={'fontname': 'Sawasdee'}, fontsize=14)
    # borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis='x', colors='darkslategrey', labelsize=14)
    ax.tick_params(axis='y', colors='darkslategrey', labelsize=14)
    # grid
    ax.minorticks_on()
    ax.yaxis.grid(which='major', color='darkgoldenrod', linestyle='--',
                  linewidth=0.5, zorder=1)
    ax.yaxis.grid(which='minor', color='darkgoldenrod', linestyle='-.',
                  linewidth=0.3, zorder=1)
    if out_filename:
        plt.savefig(out_filename, bbox_inches='tight')


def classify_polygon(stats, area_ha):
    """Applique l'arbre de décision aux statistiques des classes en utilisant les codes.

    Args:
        stats (dict): Dictionnaire regroupant les statistiques zonales
        area_ha (reel): Surface en hectare

    Returns:
        integer: Code prédit
    """
    total = sum(stats.values())
    
    if total == 0:
        return -1  # Code spécial pour indiquer les polygones qui n'ont pas de données (No data présente)

    feuillus = (stats.get(11, 0) + stats.get(12, 0) + stats.get(13, 0) + stats.get(14, 0)) / total * 100  # Pourcentage d'essences propres de feuillus
    coniferes = (stats.get(21, 0) + stats.get(22, 0) + stats.get(23, 0) + stats.get(24, 0) + stats.get(25, 0)) / total * 100  # Pourcentage d'essences propres de conifères
    
    if area_ha < 2:  # Surface < 2 ha
        if feuillus > 75:
            return 16
        elif coniferes > 75:
            return 27
        elif coniferes > feuillus:
            return 28
        else:
            return 29
    else:  # Surface > 2 ha
        classes_C = [11, 12, 13, 14, 21, 22, 23, 24, 25]
        for code in classes_C:
            if stats.get(code, 0) / total * 100 > 75:
                return code  # Retourne le code dominant
        if feuillus > 75:
            return 15
        elif coniferes > 75:
            return 26
        elif coniferes > feuillus:
            return 28
        else:
            return 29
