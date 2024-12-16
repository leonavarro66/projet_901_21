import sys
import os
import geopandas as gpd
sys.path.append('/home/onyxia/work/libsigma')
sys.path.append('/home/onyxia/work/projet_901_21/script')
from my_function import stack_bands


my_result_folder_out = '/home/onyxia/work/projet_901_21/results/data'
bands_concat = os.path.join(my_result_folder_out, 'test', 'test_image_concat_01.tif')


# Liste initiale des fichiers
bands_files = [
    "SENTINEL2A_20220417-104906-443_L2A_T31TCJ_C_V3-0_FRE_B2.tif",
    "SENTINEL2A_20220417-104906-443_L2A_T31TCJ_C_V3-0_FRE_B3.tif",
    "SENTINEL2A_20220417-104906-443_L2A_T31TCJ_C_V3-0_FRE_B4.tif",
    "SENTINEL2A_20220417-104906-443_L2A_T31TCJ_C_V3-0_FRE_B5.tif",
    "SENTINEL2A_20220417-104906-443_L2A_T31TCJ_C_V3-0_FRE_B6.tif",
    "SENTINEL2A_20220417-104906-443_L2A_T31TCJ_C_V3-0_FRE_B7.tif",
    "SENTINEL2A_20220417-104906-443_L2A_T31TCJ_C_V3-0_FRE_B8.tif",
    "SENTINEL2A_20220417-104906-443_L2A_T31TCJ_C_V3-0_FRE_B8A.tif",
    "SENTINEL2A_20220417-104906-443_L2A_T31TCJ_C_V3-0_FRE_B11.tif",
    "SENTINEL2A_20220417-104906-443_L2A_T31TCJ_C_V3-0_FRE_B12.tif",
]

# Dossier à ajouter comme préfixe
my_data_folder = '/home/onyxia/work/data/images'

# Ajouter le préfixe à chaque fichier
bands_files_with_prefix = [os.path.join(my_data_folder, file) for file in bands_files]

# Afficher le résultat
print(bands_files_with_prefix)

stack_bands(bands_files_with_prefix, bands_concat)
