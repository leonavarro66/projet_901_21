import os
import re
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.enums import Resampling

# Définir les chemins des fichiers
input_folder = "/home/onyxia/work/data/images"  # Dossier contenant les bandes
emprise_file = "/home/onyxia/work/data/project/emprise_etude.shp"
masque_file = "/home/onyxia/work/projet_901_21/results/data/img_pretraitees/masque_foret.tif"
output_file = "/home/onyxia/work/projet_901_21/results/data/img_pretraitees/Serie_temp_S2_allbands.tif"

# Créer le dossier de sortie s'il n'existe pas
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Charger l'emprise
emprise = gpd.read_file(emprise_file)

# Vérifier la projection de l'emprise
if emprise.crs.to_epsg() != 2154:
    print("Reprojection de l'emprise en EPSG:2154 (Lambert 93)")
    emprise = emprise.to_crs(epsg=2154)

emprise_geom = [feature["geometry"] for feature in emprise.__geo_interface__["features"]]

# Extraire les fichiers d'entrée et organiser par date et bande
files = os.listdir(input_folder)
pattern = r"SENTINEL2A_(\d{8})-.*_B(\w+)\.tif"
data_by_date = {}

for file in files:
    match = re.match(pattern, file)
    if match:
        date, band = match.groups()
        if date not in data_by_date:
            data_by_date[date] = {}
        data_by_date[date][f"B{band}"] = os.path.join(input_folder, file)

# Vérifier si des dates ont été trouvées
if not data_by_date:
    raise ValueError("Aucune date n'a été trouvée dans le dossier. Vérifiez les fichiers dans le dossier d'entrée.")

# Trier les dates
dates = sorted(data_by_date.keys())
required_bands = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]

# Vérifier si toutes les bandes sont présentes pour chaque date
for date, bands in data_by_date.items():
    missing_bands = [band for band in required_bands if band not in bands]
    if missing_bands:
        print(f"Bandes manquantes pour la date {date} : {missing_bands}")

# Découper, reprojeter, et assembler les bandes
processed_bands = []
for date in dates:
    for band in required_bands:
        if band not in data_by_date[date]:
            print(f"Bande manquante : {band} pour la date {date}")
            continue

        raster_path = data_by_date[date][band]
        with rasterio.open(raster_path) as src:
            # Vérifier la projection du raster
            if src.crs.to_epsg() != 2154:
                print(f"Reprojection du raster {raster_path} en EPSG:2154")
                transform, width, height = rasterio.warp.calculate_default_transform(
                    src.crs, 'EPSG:2154', src.width, src.height, *src.bounds
                )
                reprojected_raster = rasterio.MemoryFile().open(
                    driver="GTiff",
                    height=height,
                    width=width,
                    count=src.count,
                    dtype=src.dtypes[0],
                    crs="EPSG:2154",
                    transform=transform
                )
                rasterio.warp.reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(reprojected_raster, 1),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs="EPSG:2154",
                    resampling=Resampling.nearest
                )
                src = reprojected_raster

            # Découper selon l'emprise
            clipped, transform = mask(src, emprise_geom, crop=True, nodata=0)

            # Appliquer le masque
            with rasterio.open(masque_file) as masque_src:
                masque_data = masque_src.read(
                    out_shape=(
                        masque_src.count,
                        clipped.shape[1],
                        clipped.shape[2]
                    ),
                    resampling=Resampling.nearest
                ).astype(bool)

                # Appliquer le masque (mettre à 0 les zones non forêt)
                clipped[~masque_data] = 0

            processed_bands.append((clipped, transform, src.crs))

# Vérifier le nombre total de bandes
print(f"Nombre total de bandes traitées : {len(processed_bands)}")

# Assembler toutes les bandes en une seule image
if processed_bands:
    meta = {
        "driver": "GTiff",
        "count": len(processed_bands),
        "dtype": "uint16",
        "crs": "EPSG:2154",
        "transform": processed_bands[0][1],
        "width": processed_bands[0][0].shape[2],
        "height": processed_bands[0][0].shape[1],
        "nodata": 0
    }

    with rasterio.open(output_file, "w", **meta) as dst:
        for i, (band, _, _) in enumerate(processed_bands, start=1):
            dst.write(band[0], i)

    print(f"Image finale enregistrée sous : {output_file}")

    # Afficher les métadonnées de l'image finale
    with rasterio.open(output_file) as src:
        print("Nombre de bandes :", src.count)
        print("Projection :", src.crs)
        print("Résolution (mètres) :", src.res)
        print("Dimensions (pixels) :", src.width, "x", src.height)
        print("Valeur de nodata :", src.nodata)
else:
    print("Aucune bande n'a été traitée. Vérifiez les fichiers d'entrée.")
