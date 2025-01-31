# -*- coding: utf-8 -*-
"""
@author: navarro leo, biou romain, sala mathieu
"""

import os
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import LogNorm
from my_function import count_polygons_by_class, count_pixels_by_class, prepare_violin_plot_data

import numpy as np

# Définition des chemins des fichiers
INPUT_FILE = "/home/onyxia/work/projet_901_21/results/data/sample/Sample_BD_foret_T31TCJ.shp"
OUTPUT_DIR = "/home/onyxia/work/projet_901_21/results/figure"
diag_poly_file = os.path.join(OUTPUT_DIR, "diag_baton_nb_poly_by_class.png")
diag_pix_file = os.path.join(OUTPUT_DIR, "diag_baton_nb_pix_by_class.png")
violin_plot_file = os.path.join(OUTPUT_DIR, "violin_plot_nb_pix_by_poly_by_class.png")

# Charger les données du fichier Shapefile
gdf = gpd.read_file(INPUT_FILE)

# Liste des classes à analyser
selected_classes = [11, 12, 13, 14, 21, 22, 23, 24, 25]

# Comptage du nombre de polygones par classe
class_counts = count_polygons_by_class(gdf, "Code", selected_classes)

# Associer les codes des classes à leurs noms
filtered_gdf = gdf[gdf["Code"].isin(selected_classes)][["Code", "Nom"]].drop_duplicates()
code_to_name = dict(zip(filtered_gdf["Code"], filtered_gdf["Nom"]))

# Conversion des codes en noms pour le diagramme en bâtons (polygones)
class_names = [code_to_name[code] for code in class_counts.keys()]
counts = list(class_counts.values())

# Générer une palette de couleurs avec une échelle logarithmique
norm = LogNorm(vmin=min(counts), vmax=max(counts))
colors = cm.Greens(norm(counts))

# Création du diagramme en bâtons pour les polygones
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

plt.figure(figsize=(12, 8))
bars = plt.bar(class_names, counts, color=colors, edgecolor='black')
plt.xlabel("Classes", fontsize=16)
plt.ylabel("Nombre de polygones", fontsize=16)
plt.title("Nombre de polygones par classe", fontsize=18)
plt.xticks(rotation=45, ha="right", fontsize=12)
plt.tight_layout()

# Ajouter des étiquettes sur chaque barre
for bar, count in zip(bars, counts):
    plt.text(bar.get_x() + bar.get_width() / 2,  # Position horizontale centrée sur la barre
             bar.get_height() + 1,              # Position verticale au-dessus de la barre
             str(count),                        # Texte affiché (nombre de polygones)
             ha='center', va='bottom', fontsize=10)

# Sauvegarder la figure
plt.savefig(diag_poly_file)
plt.close()

print(f"diag_baton_nb_poly_by_class sauvegardé dans {diag_poly_file}")

# Comptage du nombre de pixels par classe
class_pixel_counts = count_pixels_by_class(gdf, "Code", selected_classes)

# Conversion des codes en noms pour le diagramme en bâtons (pixels)
class_names_pix = [code_to_name[code] for code in class_pixel_counts.keys()]
counts_pix = list(class_pixel_counts.values())

# Création du diagramme en bâtons pour les pixels
plt.figure(figsize=(12, 8))
# Générer une palette de couleurs avec une échelle logarithmique
norm = LogNorm(vmin=min(counts_pix), vmax=max(counts_pix))
colors = cm.Blues(norm(counts_pix))

bars = plt.bar(class_names_pix, counts_pix, color=colors, edgecolor='black')
plt.xlabel("Classes", fontsize=16)
plt.ylabel("Nombre de pixels", fontsize=16)
plt.title("Nombre de pixels par classe", fontsize=18)
plt.xticks(rotation=45, ha="right", fontsize=12)
plt.tight_layout()

# Ajouter des étiquettes sur chaque barre
for bar, count in zip(bars, counts_pix):
    plt.text(bar.get_x() + bar.get_width() / 2,  # Position horizontale centrée sur la barre
             bar.get_height() + 1,              # Position verticale au-dessus de la barre
             str(count),                        # Texte affiché (nombre de pixels)
             ha='center', va='bottom', fontsize=10)

# Sauvegarder la figure
plt.savefig(diag_pix_file)
plt.close()

print(f"diag_baton_nb_pix_by_class sauvegardé dans {diag_pix_file}")

# Calculer la surface de chaque polygone en pixels (adapté à la résolution du raster)
RESOLUTION = 10  # Résolution spatiale utilisée pour le raster
gdf["Nombre_de_pixels"] = (gdf.geometry.area / (RESOLUTION**2)).astype(int)

# Préparer les données pour le "violin plot"
violin_data = prepare_violin_plot_data(gdf, "Code", "Nombre_de_pixels")

# Filtrer les données pour les classes sélectionnées
violin_data = violin_data[violin_data["Classe"].isin(selected_classes)]

# Mapper les noms des classes pour les classes sélectionnées
classes = [code_to_name[classe] for classe in selected_classes]

# Préparer les données pour Matplotlib
data = [violin_data[violin_data["Classe"] == classe]["Pixels"].values for classe in selected_classes]

# Création du "violin plot" avec Matplotlib
plt.figure(figsize=(12, 8))
violin_parts = plt.violinplot(data, showmeans=False, showextrema=True, showmedians=True)

# Personnaliser les couleurs des violons
for pc in violin_parts['bodies']:
    pc.set_facecolor('skyblue')
    pc.set_edgecolor('black')
    pc.set_alpha(0.7)

# Ajouter des étiquettes et configurer l'échelle des axes
plt.xticks(
    ticks=np.arange(1, len(classes) + 1),
    labels=classes,
    rotation=45,
    ha="right",
    fontsize=12
    )
plt.xlabel("Classes", fontsize=16)
plt.ylabel("Nombre de pixels par polygone", fontsize=16)
plt.title("Distribution du nombre de pixels par polygone, par classe", fontsize=18)
plt.yscale('log')  # Utiliser une échelle logarithmique pour l'axe Y
plt.yticks([1, 10, 100, 1000, 10000, 100000], ["0", "10", "100", "1k", "10k", "100k"])
plt.gca().yaxis.set_minor_formatter(plt.FuncFormatter(lambda x, _: ""))  # Supprimer les ticks
plt.tight_layout()

# Sauvegarder la figure
plt.savefig(violin_plot_file)
plt.close()

print(f"violin_plot_nb_pix_by_poly_by_class sauvegardé dans {violin_plot_file}")
