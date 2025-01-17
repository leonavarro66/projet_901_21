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



from osgeo import gdal
import numpy as np
import logging
import os
import geopandas as gpd

gdal.UseExceptions()

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

import pandas as pd
import geopandas as gpd

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