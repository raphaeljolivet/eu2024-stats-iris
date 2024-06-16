
# Croisement des résultats des élections européennes 2024, avec les donnnées démographique INSEE de 2020, au niveau IRIS 

Ce projet croise les [résultats des élections européennes de 2024](https://www.data.gouv.fr/fr/datasets/resultats-des-elections-europeennes-du-9-juin-2024/) avec les données 
démographiques [INSEE au niveau IRIS (2020)](https://www.insee.fr/fr/statistiques/7704076), pour l'ensemble de la France métropolitaine.

Cette jointure est faite de manière géographique, gràce à la reconcustruction de la géométrie des bureaux de vote produite par [cet autre projet](https://www.data.gouv.fr/fr/datasets/reconstruction-automatique-de-la-geometrie-des-bureaux-de-vote-depuis-insee-reu-et-openstreetmap/) 

L'objectif est de permettre des statistiques démographiques fines sur les tendances politiques récentes.


# Données de sortie 

La sortie de cette jointure est disponible ici, au format Goejson et gpkg (geopackage) :
https://github.com/raphaeljolivet/eu2024-stats-iris/releases/tag/1.0

# Utilisation

Pour générer vous même les fichiers de sorties :

1) Créez un nouvel environeme,nt Python 3.10, avec **conda** ou **virtualenv*
2) Importez lees dépendances : `pip install -r requirements.txt```
3) Exécutez le point d'entrée principal : `python main.py`

Les données d'entrée sont téléchargées dans le dossier `data/in` et les sorties sont générées dans `data/out` 

# Source de données

## Shapefile bureaux

* https://www.data.gouv.fr/fr/datasets/reconstruction-automatique-de-la-geometrie-des-bureaux-de-vote-depuis-insee-reu-et-openstreetmap/
* https://www.data.gouv.fr/fr/datasets/r/d2392385-c12f-4b1b-8940-37da09be6333

## Contours IRIS 

https://data.geopf.fr/telechargement/download/CONTOURS-IRIS/CONTOURS-IRIS_3-0__SHP__FRA_2023-01-01/CONTOURS-IRIS_3-0__SHP__FRA_2023-01-01.7z


## Résultats des elections 

https://www.data.gouv.fr/fr/datasets/r/1996b2bc-e95a-4481-904f-28d16987fe61

## Démographie 2020 Insee

https://www.insee.fr/fr/statistiques/7704076
https://www.insee.fr/fr/statistiques/fichier/7704076/base-ic-evol-struct-pop-2020_csv.zip


# LICENSE

La code source et les données de sorties sont fournies selon les termes de la license [Creative Common NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/deed.fr)


