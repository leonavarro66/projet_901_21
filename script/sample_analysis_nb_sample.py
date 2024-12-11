import os
import geopandas as gpd
import matplotlib.pyplot as plt
from my_function import count_polygons_by_class
import matplotlib.cm as cm
from matplotlib.colors import LogNorm


# Définir les chemins des fichiers
input_file = "/home/onyxia/work/projet_901_21/results/data/sample/Sample_BD_foret_T31TCJ.shp"
output_dir = "/home/onyxia/work/projet_901_21/results/figure"
output_file = os.path.join(output_dir, "diag_baton_nb_poly_by_class.png")

# Charger les données du fichier Shapefile
gdf = gpd.read_file(input_file)

# Liste des classes à analyser
selected_classes = [11, 12, 13, 14, 21, 22, 23, 24, 25]

# Comptage des polygones par classe
class_counts = count_polygons_by_class(gdf, "Code", selected_classes)

# Associer les noms aux codes
# Filtrer uniquement les codes sélectionnés et retirer les doublons
filtered_gdf = gdf[gdf["Code"].isin(selected_classes)][["Code", "Nom"]].drop_duplicates()
code_to_name = dict(zip(filtered_gdf["Code"], filtered_gdf["Nom"]))

# Convertir les codes en noms pour le plot
class_names = [code_to_name[code] for code in class_counts.keys()]
counts = list(class_counts.values())

# Générer une palette de couleurs avec une échelle logarithmique
norm = LogNorm(vmin=min(counts), vmax=max(counts))  # Normalisation logarithmique
colors = cm.Greens(norm(counts))  # Génère une palette de verts

# Créer le diagramme en bâtons
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

plt.figure(figsize=(10, 6))
bars = plt.bar(class_names, counts, color=colors, edgecolor='black')  # Ajout de la bordure noire
plt.xlabel("Classes", fontsize=14)
plt.ylabel("Nombre de polygones", fontsize=14)
plt.title("Nombre de polygones par classe", fontsize=16)
plt.xticks(rotation=45, ha="right")  # Rotation des noms pour une meilleure lisibilité
plt.tight_layout()

# Ajouter des étiquettes sur chaque barre
for bar, count in zip(bars, counts):
    plt.text(bar.get_x() + bar.get_width() / 2,  # Position horizontale centrée sur la barre
             bar.get_height() + 1,              # Position verticale légèrement au-dessus de la barre
             str(count),                        # Texte affiché (nombre de polygones)
             ha='center', va='bottom', fontsize=10)

# Sauvegarder la figure
plt.savefig(output_file)
plt.close()

print(f"Diagramme en bâtons sauvegardé dans {output_file}")