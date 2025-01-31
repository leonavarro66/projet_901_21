import sys
sys.path.append('/home/onyxia/work/libsigma')
sys.path.append('/home/onyxia/work/projet_901_21/script')

import os
import numpy as np
from osgeo import gdal
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.ensemble import RandomForestClassifier as RF
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# personal libraries
import classification as cla
import read_and_write as rw
from my_function import rasterize, plot_class_quality
import plots

my_folder = '/home/onyxia/work/data/project/tmp_classif'
my_folder_result = '/home/onyxia/work/projet_901_21/results/data'
sample_shp = os.path.join(my_folder_result, 'sample', 'Sample_BD_foret_T31TCJ.shp')
emprise_shp = '/home/onyxia/work/data/project/emprise_etude.shp'

# Créer le dossier de sortie s'il n'existe pas
if not os.path.exists(os.path.join(my_folder_result, 'classif')):
    os.makedirs(os.path.join(my_folder_result, 'classif'))

# Créer le dossier de sortie s'il n'existe pas
if not os.path.exists(my_folder):
    os.makedirs(my_folder)

# Lecture du jeu de données de la bd_foret et de l'emprise d'etude
bd_foret = gpd.read_file(sample_shp)
emprise = gpd.read_file(emprise_shp)

# Codes à garder pour la classfication supervisée
codes_classif_pixel = [11, 12, 13, 14, 21, 22, 23, 24, 25]

# On garde seulement les lignes qui nous intéresse pour la classification
bd_foret_filtree = bd_foret[bd_foret['Code'].isin(codes_classif_pixel)]

bd_foret_filtree_classif_filename = os.path.join(my_folder, 'bd_foret_filtree_pour_classif.shp')
bd_foret_filtree.to_file(bd_foret_filtree_classif_filename)
# Paramètres de rasterisation
output_file = os.path.join(my_folder, 'sample_raster.tif')  # Chemin vers l'image de sortie
field_name = 'Code'  # Champ contenant les valeurs de rasterisation
spatial_res = 10  # Résolution spatiale de 10 m
data_type = 'Int8'  # Type de données de sortie
driver = 'GTiff'  # Format GeoTIFF

# Appel de la fonction pour rasteriser le jeu d'échantillons
rasterize(bd_foret_filtree_classif_filename, emprise, output_file, spatial_res, data_type, driver, field_name)

# Chaîne de traitements pour la classification supervisée
# 1 --- define parameters
# inputs

sample_filename = os.path.join(my_folder, 'sample_raster.tif')
image_filename = os.path.join(my_folder_result, 'img_pretraitees', 'Serie_temp_S2_allbands.tif')

# outputs
out_classif = os.path.join(my_folder_result, 'classif', 'carte_essences_echelle_pixel.tif')
out_matrix = os.path.join(my_folder, 'matrice_confusion_echelle_pixel.png')
out_qualite = os.path.join(my_folder, 'graphique_qualite_echelle_pixel.png')
# 2 --- extract samples
X, Y, t = cla.get_samples_from_roi(image_filename, sample_filename)

# 3 --- Define StratifiedKFold for 5 folds
skf = StratifiedKFold(n_splits=5)

# Variables to store results
accuracies = []
confusion_matrices = []
classification_reports = []

# 4 --- Loop over the splits
for train_index, test_index in skf.split(X, Y):
    X_train, X_test = X[train_index], X[test_index]
    Y_train, Y_test = Y[train_index], Y[test_index]
    
    # 5 --- Train the classifier
    clf = RF(
        max_depth=50, 
        oob_score=True, 
        max_samples=0.75, 
        class_weight="balanced",
        n_jobs=-1
    )
    clf.fit(X_train, Y_train.ravel())

    # 6 --- Test the classifier
    Y_predict = clf.predict(X_test)

    # 7 --- Compute quality metrics
    cm = confusion_matrix(Y_test, Y_predict)
    report = classification_report(Y_test, Y_predict, labels=np.unique(Y),
                                   output_dict=True, zero_division=1)
    accuracy = accuracy_score(Y_test, Y_predict)

    # Store results
    accuracies.append(accuracy)
    confusion_matrices.append(cm)
    classification_reports.append(report)

# 8 --- Average results over all folds
# Calculer la moyenne des métriques pour chaque classe
average_accuracy = np.mean(accuracies)

# Moyenne de la matrice de confusion (en moyenne sur les plis)
average_cm = np.mean(confusion_matrices, axis=0)

# On suppose que classification_reports contient des dictionnaires, chacun ayant les scores de chaque classe
# On extrait les classes et les clés pour lesquelles on veut calculer la moyenne (par exemple, precision, recall, f1-score)
average_report = {}

# Extraire les clés globales et les classes (les classes sont dans les clés du dictionnaire)
classes = [key for key in classification_reports[0] if isinstance(classification_reports[0][key], dict)]
keys = ['precision', 'recall', 'f1-score']  # Les métriques que nous voulons moyenner

# Calculer la moyenne des scores pour chaque métrique et chaque classe
for key in keys:
    average_report[key] = {}
    for class_label in classes:
        # Moyenne de chaque métrique pour chaque classe sur les plis
        average_report[key][class_label] = np.mean([r[class_label][key] for r in classification_reports])

# 9 --- Display and save results
plots.plot_cm(average_cm, np.unique(Y), out_filename=out_matrix)
plot_class_quality(average_report, average_accuracy, out_filename=out_qualite)

# 5 --- apply on the whole image
# load image
X_img, _, t_img = cla.get_samples_from_roi(image_filename, image_filename)

# predict image
Y_predict = clf.predict(X_img)

# reshape
ds = rw.open_image(image_filename)
nb_row, nb_col, _ = rw.get_image_dimension(ds)

img = np.zeros((nb_row, nb_col, 1), dtype='uint8')
img[t_img[0], t_img[1], 0] = Y_predict

# write image
ds = rw.open_image(image_filename)
rw.write_image(out_classif, img, data_set=ds, gdal_dtype=None,
            transform=None, projection=None, driver_name=None,
            nb_col=None, nb_ligne=None, nb_band=1)