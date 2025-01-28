import sys
import logging
sys.path.append('/home/onyxia/work/projet_901_21/script')
from my_function import analyze_phenology_gdal_alternative

logging.basicConfig(level=logging.INFO)


# Initialisation des paramètres
ndvi_raster = "/home/onyxia/work/projet_901_21/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif"  # Raster NDVI multibandes
shapefile = "/home/onyxia/work/projet_901_21/results/data/sample/Sample_BD_foret_T31TCJ.shp"  # Shapefile de la BD forêt
output_folder = "/home/onyxia/work/projet_901_21/results/figure"  # Dossier de sortie
dates = ["2022-04-17", "2022-05-17", "2022-08-28", "2022-11-13", "2022-11-16", "2023-02-14"]  # Dates associées aux bandes

# Appel de la fonction
analyze_phenology_gdal_alternative(ndvi_raster, shapefile, output_folder, dates)
