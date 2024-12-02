# Projet de Télédétection Master 2 SIGMA

## Groupe

Le groupe de travail est constitué de Romain BIOU, Mathieu SALA et Léo NAVARRO

## Installation de l'espace de travail

Lorsque vous arrivez sur votre session Onyxia, vous clonez le dépôt Git avec la commande suivante :


```bash
git clone "https://github.com/leonavarro66/projet_901_21.git"
```

Normalement, vous aurez une arborescence du type

```
WORK
└───data
│   │
│   └───project
│       │   ...
│   
└───libsigma
│   │   ...
│
└───projet_901_21 (dépôt git)
│   │
│   └───rapport
│       │   ...
│   └───...
│       │   ...
```

Maintenant, il faut récupérer les données des images satellites qui sont sur le serveur de fichier Onyxia, pour ce faire, il faut exécuter la commande suivante :

Vous allez les récupérer depuis mon serveur de fichiers Onyxia d'où mon pseudo dans le lien de la commande.

```bash
mc cp -r s3/leonavarrosig66/diffusion/images home/onyxia/work/data
```

Après cette commande, dans le dossier data, en plus du sous-dossier 'project', vous aurez un sous-dossier 'images' avec les données satellites.

Normalement, j'ai rien oublié et on devrait tout avoir pour travailler.

## Contexte

"La BD Forêt® version 2.0 est une base de données de référence pour l’espace forestier et les milieux semi-naturels. Elle constitue le référentiel géographique de description des essences forestières. Elle décrit les formations végétales forestières et naturelles par une approche de la couverture du sol traduisant une description de la densité de couvert du peuplement, de sa composition et de l’essence dominante, pour les éléments de plus de 5 000 m2 (soit 0,5 hectare). Elle est élaborée par photo-interprétation d’images en infrarouge couleurs de la BD ORTHO®. [...]
La BD Forêt® version 2.0 constitue un outil de référence pour les acteurs de la filière forêt-bois, de l’environnement, de l’aménagement du territoire et du développement durable (gestion, incendie, ressource, approvisionnement, certification…) et intervient en appui de divers projets (aménagement du territoire, évaluation de la ressource et de la qualité de l’environnement, prévention des risques, connaissance de la biodiversité et continuités écologiques, description des paysages comme des milieux naturels…)."

Si cette base de données est très précieuse, elle n'est pas mise à jour régulièrement et elle ne permet pas de cartographier les essences forestières à une échelle intra-peuplement. C'est là où vous entrez en scène, munis de nouvelles compétences en télédétection !

## Objectif

L'objectif de ce projet est d'étudier si la BD Forêt® version 2.0 peut être utilisée comme source d'échantillons de référence pour réaliser une classification supervisée de séries temporelles d'images Sentinel 2.

Vous réaliserez une classification supervisée à l'échelle du pixel puis l'information sera aggrégée à l'échelle des peuplements de la BD Forêt. Vous évaluerez la qualité des cartes produites à ces deux échelles. Vous devrez d'abord télécharger des images satellite puis les pré-traiter et enfin préparer les échantillons à partir de la BD Forêt.
