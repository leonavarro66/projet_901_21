import sys
import os
sys.path.append('/home/onyxia/work/projet_901_21/script')
from my_function import stack_bands

# Initialisation des chemins nécessaires
raster_folder = "/home/onyxia/work/data/images"

# Liste de tous les fichiers .tif dans le dossier de rasters
raster_files = [os.path.join(raster_folder, f) for f in os.listdir(raster_folder) if f.endswith('.tif')]

stack_bands(raster_files, '/home/onyxia/work/data/project/aaaa.tif')

gdalwarp -overwrite -t_srs EPSG:2154 -te 501127.9697 6240658.2591 609759.1078 6314464.0236 -te_srs EPSG:2154 -ot UInt16 -of GTiff -tr 10.0 10.0 -tap -cutline "C:/Users/LéoNavarro/OneDrive - Veremes/Documents/DOSSIER PERSO LEO/Master sigma/projet_lang/emprise_etude.shp" -cl emprise_etude -crop_to_cutline -dstnodata 0.0 -tap "C:/Users/LéoNavarro/OneDrive - Veremes/Documents/DOSSIER PERSO LEO/Master sigma/projet_lang/SENTINEL2A_20220417-104906-443_L2A_T31TCJ_C_V3-0_FRE_B2.tif" C:/Users/LéoNavarro/AppData/Local/Temp/processing_VwtNmT/27c33c631c0a494e807317479df3b033/OUTPUT.tif