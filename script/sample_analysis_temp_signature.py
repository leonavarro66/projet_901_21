import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.INFO)

def analyze_phenology_gdal_alternative(ndvi_raster, shapefile, output_folder):
    """
    Analyse la phénologie des classes de la BD forêt classifié en calculant la moyenne et l'écart type du NDVI.

    :param ndvi_raster: Chemin du raster multibandes NDVI
    :param shapefile: Chemin du shapefile de la BD forêt classifié
    :param output_folder: Dossier pour sauvegarder les résultats
    """
    # Classes pertinentes
    selected_classes = [12, 13, 14, 23, 24, 25]
    os.makedirs(output_folder, exist_ok=True)

    # Initialisation des résultats
    stats = {cls: {"mean": [], "std": []} for cls in selected_classes}
    bands_count = 6  # Supposons que le raster NDVI contient 6 bandes temporelles

    for i in range(1, bands_count + 1):
        logging.info(f"Traitement de la bande {i}...")
        temp_band_raster = f"/home/onyxia/work/data/project/temp/temp_band_{i}.tif"

        # Extraire la bande NDVI i
        cmd_extract_band = (
            f"gdal_translate -b {i} {ndvi_raster} {temp_band_raster} "
            f"-of GTiff -q"
        )
        subprocess.run(cmd_extract_band, shell=True, check=True)

        for cls in selected_classes:
            logging.info(f"Traitement de la classe {cls}...")

            # Créer un masque pour la classe
            temp_mask = f"/home/onyxia/work/data/project/temp/temp_mask_{cls}.shp"
            cmd_create_mask = (
                f"ogr2ogr -where \"Code={cls}\" {temp_mask} {shapefile}"
            )
            subprocess.run(cmd_create_mask, shell=True, check=True)

            # Découper le raster par la classe
            temp_cropped_raster = f"/home/onyxia/work/data/project/temp/temp_cropped_band_{i}_class_{cls}.tif"
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
    dates = [f"Bande {i}" for i in range(1, bands_count + 1)]
    plt.figure(figsize=(12, 6))
    for cls in selected_classes:
        mean_values = stats[cls]["mean"]
        std_values = stats[cls]["std"]
        plt.plot(dates, mean_values, label=f"Classe {cls}")
        plt.fill_between(
            dates,
            [m - s if m and s else 0 for m, s in zip(mean_values, std_values)],
            [m + s if m and s else 0 for m, s in zip(mean_values, std_values)],
            alpha=0.2
        )

    # Personnalisation du graphique
    plt.title("Signature temporelle du NDVI par classe")
    plt.xlabel("Dates (bandes temporelles)")
    plt.ylabel("NDVI")
    plt.legend(title="Classes")
    plt.grid(True)

    # Sauvegarder le graphique
    output_path = os.path.join(output_folder, "temp_mean_ndvi.png")
    plt.savefig(output_path)
    plt.close()

    logging.info(f"Graphique sauvegardé : {output_path}")

# Exemple d'utilisation
ndvi_raster = "/home/onyxia/work/projet_901_21/results/data/img_pretraitees/Serie_temp_S2_ndvi.tif"  # Raster NDVI multibandes
shapefile = "/home/onyxia/work/projet_901_21/results/data/sample/Sample_BD_foret_T31TCJ.shp"  # Shapefile de la BD forêt
output_folder = "/home/onyxia/work/data/project/test"  # Dossier de sortie
analyze_phenology_gdal_alternative(ndvi_raster, shapefile, output_folder)