# -*- coding: utf-8 -*-
"""
@author: navarro leo, biou romain, sala mathieu
"""

import os
import geopandas as gpd
import subprocess
import logging


def rasterize(in_vector, ref_image, out_image, spatial_res, data_type, driver, field_name):
    """
    Fonction permettant de rasteriser un shapefile en fonction d'une couche de référence.

    Args:
        in_vector (str): Chemin vers le shapefile à rasteriser.
        ref_image (GeoDataFrame): GeoDataFrame représentant l'image de référence (utilisé pour l'emprise).
        out_image (str): Chemin où l'image rasterisée sera sauvegardée.
        spatial_res (float): Résolution spatiale à utiliser pour le raster.
        data_type (str): Type de données pour le raster (par exemple, 'Byte', 'UInt16', etc.).
        driver (str): Driver de format à utiliser pour la sortie (par exemple, 'GTiff' pour GeoTIFF).
        field_name (str): Nom du champ à utiliser pour la rasterisation.

    Raises:
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
