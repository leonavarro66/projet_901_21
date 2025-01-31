# -*- coding: utf-8 -*-
"""
@author: navarro leo, biou romain, sala mathieu
"""

import os
import sys
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal
import pandas as pd
sys.path.append('/home/onyxia/work/projet_901_21/script')
from my_function import calculate_distance

# Charger les données shapefile
BD_FORET_CLASS = "/home/onyxia/work/projet_901_21/results/data/sample/Sample_BD_foret_T31TCJ.shp"
OUTPUT_PATH = "/home/onyxia/work/projet_901_21/results/figure"
os.makedirs(OUTPUT_PATH, exist_ok=True)
output_1 = os.path.join(OUTPUT_PATH, "diag_baton_dist_centroide_classe.png")
output_2 = os.path.join(OUTPUT_PATH, "violin_plot_dist_centroide_by_poly_by_class.png")

data = gpd.read_file(BD_FORET_CLASS)

# Charger le raster NDVI avec GDAL
NDVI_PATH = "/home/onyxia/work/projet_901_21/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif"
dataset = gdal.Open(NDVI_PATH)

# Lire la première bande du raster NDVI
band = dataset.GetRasterBand(1)
ndvi_array = band.ReadAsArray()
no_data = band.GetNoDataValue()

# Récupérer les dimensions et la géométrie du raster
nrows, ncols = ndvi_array.shape
transform = dataset.GetGeoTransform()

# Définir les classes bleues et rouges avec leur code et nom associé
classes_bleues = {
    15: "Mélange de feuillus",
    26: "Mélange conifères",
    28: "Mélange de conifères prépondérants et feuillus",
    29: "Mélange de feuillus prépondérants et conifères",
}

classes_rouges = {
    11: "Autres feuillus",
    12: "Chêne",
    13: "Robinier",
    14: "Peupleraie",
    23: "Douglas",
    24: "Pin laricio ou pin noir",
    25: "Pin maritime",
}

# Filtrer les données par classe
all_data = data[data["Code"].isin(list(classes_bleues.keys()) + list(classes_rouges.keys()))]

# Question 1 : Distance moyenne au centroïde par classe
mean_distances = {}

for class_code, group in all_data.groupby("Code"):
    centroid = group.geometry.centroid
    centroid_x = centroid.x.mean()
    centroid_y = centroid.y.mean()

    distances = []
    for _, row in group.iterrows():
        min_x, min_y, max_x, max_y = row['geometry'].bounds
        start_col = max(0, int((min_x - transform[0]) / transform[1]))
        end_col = min(ncols - 1, int((max_x - transform[0]) / transform[1]))
        start_row = max(0, int((max_y - transform[3]) / transform[5]))
        end_row = min(nrows - 1, int((min_y - transform[3]) / transform[5]))

        for row_idx in range(start_row, end_row + 1):
            for col_idx in range(start_col, end_col + 1):
                pixel_value = ndvi_array[row_idx, col_idx]
                if pixel_value != no_data:
                    pixel_x = transform[0] + col_idx * transform[1] + transform[1] / 2
                    pixel_y = transform[3] + row_idx * transform[5] + transform[5] / 2
                    distances.append(calculate_distance((centroid_x, centroid_y), pixel_x, pixel_y))

    # Calculer la distance moyenne
    if distances:
        mean_distances[class_code] = np.mean(distances)
    else:
        print(f"Attention : aucune distance calculée pour la classe {class_code}")
        mean_distances[class_code] = np.nan

# Diagramme en bâtons pour la question 1
# Diagramme en bâtons pour la question 1
plt.figure(figsize=(10, 6))

# Récupérer les noms des classes à partir des codes
class_names = [classes_bleues.get(code, classes_rouges.get(code, "Inconnue")) for code in mean_distances.keys()]

# Créer le graphique
bars = plt.bar(
    class_names,
    mean_distances.values(),
    color=["blue" if code in classes_bleues else "red" for code in mean_distances.keys()]
    )
plt.xlabel("Classe")
plt.ylabel("Distance moyenne au centroïde (mètres)")
plt.title("Distance moyenne au centroïde par classe")
plt.xticks(rotation=45, ha="right")

# Ajouter les étiquettes avec les valeurs sur les barres
for bar in bars:
    yval = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        yval + 0.1,
        f'{yval:.2f}',
        ha='center',
        va='bottom',
        fontsize=10
        )

plt.tight_layout()

# Sauvegarder et afficher
plt.savefig(output_1)
plt.show()

# Question 2 : Analyse à l'échelle de chaque polygone
polygon_distances = []

for _, row in all_data.iterrows():
    centroid = row.geometry.centroid
    centroid_x, centroid_y = centroid.x, centroid.y

    min_x, min_y, max_x, max_y = row['geometry'].bounds
    start_col = max(0, int((min_x - transform[0]) / transform[1]))
    end_col = min(ncols - 1, int((max_x - transform[0]) / transform[1]))
    start_row = max(0, int((max_y - transform[3]) / transform[5]))
    end_row = min(nrows - 1, int((min_y - transform[3]) / transform[5]))

    distances = []
    for row_idx in range(start_row, end_row + 1):
        for col_idx in range(start_col, end_col + 1):
            pixel_value = ndvi_array[row_idx, col_idx]
            if pixel_value != no_data:
                pixel_x = transform[0] + col_idx * transform[1] + transform[1] / 2
                pixel_y = transform[3] + row_idx * transform[5] + transform[5] / 2
                distances.append(calculate_distance((centroid_x, centroid_y), pixel_x, pixel_y))

    if distances:
        mean_distance = np.mean(distances)
    else:
        mean_distance = np.nan

    polygon_distances.append({"Classe": row["Nom"], "Distance moyenne": mean_distance})

# Convertir en DataFrame pour le plot
polygon_distances_df = pd.DataFrame(polygon_distances)

# Violin plot pour la question 2
plt.figure(figsize=(12, 8))
for idx, class_name in enumerate(polygon_distances_df["Classe"].unique()):
    class_distances = polygon_distances_df[polygon_distances_df["Classe"] == class_name]["Distance moyenne"].dropna()
    if not class_distances.empty:
        violon = plt.violinplot(
            class_distances,
            positions=[idx],
            showmeans=True,
            showextrema=True,
            widths=0.7
            )
        COLOR = "blue" if class_name in classes_bleues else "red"
        for body in violon['bodies']:
            body.set_facecolor(COLOR)
            body.set_edgecolor("black")

plt.xticks(range(len(polygon_distances_df["Classe"].unique())), polygon_distances_df["Classe"].unique(), rotation=45, ha="right")
plt.xlabel("Classe")
plt.ylabel("Distribution des distances moyennes (mètres)")
plt.title("Distribution des distances moyennes au centroïde par classe")
plt.tight_layout()
plt.savefig(output_2)
plt.show()
