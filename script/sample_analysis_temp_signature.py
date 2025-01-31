# -*- coding: utf-8 -*-
"""
@author: navarro leo, biou romain, sala mathieu
"""

import sys
import logging
sys.path.append('/home/onyxia/work/projet_901_21/script')
from my_function import analyze_phenology_gdal_alternative

logging.basicConfig(level=logging.INFO)

# Initialisation des paramètres
NDVI_RASTER = "/home/onyxia/work/projet_901_21/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif"
SAMPLE_SHAPEFILE = "/home/onyxia/work/projet_901_21/results/data/sample/Sample_BD_foret_T31TCJ.shp"
OUTPUT_FOLDER = "/home/onyxia/work/projet_901_21/results/figure"
dates = ["2022-04-17", "2022-05-17", "2022-08-28", "2022-11-13", "2022-11-16", "2023-02-14"]

# Appel de la fonction
analyze_phenology_gdal_alternative(NDVI_RASTER, SAMPLE_SHAPEFILE, OUTPUT_FOLDER, dates)
