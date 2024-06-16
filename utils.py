import os.path
import pickle
import urllib
import zipfile
from os import path, makedirs
from os.path import basename
from shutil import move
from tempfile import TemporaryDirectory
from urllib.request import urlretrieve

import geopandas as gp
import pandas as pd
import unicodedata
import py7zr
import requests

from geopandas import GeoDataFrame
import urllib

CRS = "EPSG:2154" # Lambert 93

BUREAUX="data/in/bureau-de-vote-insee-reu-openstreetmap.gpkg"
IRIS_FOLDER="data/in/iris/"
IRIS=f"{IRIS_FOLDER}/CONTOURS-IRIS.shp"
ELECTIONS="data/in/resultats-europeennes-2024-bureau-vote.xlsx"
DEMOGRAPHIE="data/in/base-ic-evol-struct-pop-2020.CSV"

IRIS_URL = "https://data.geopf.fr/telechargement/download/CONTOURS-IRIS/CONTOURS-IRIS_3-0__SHP__FRA_2023-01-01/CONTOURS-IRIS_3-0__SHP__FRA_2023-01-01.7z"
IRIS_7Z_FOLDER= "CONTOURS-IRIS_3-0__SHP__FRA_2023-01-01/CONTOURS-IRIS/1_DONNEES_LIVRAISON_2024-02-00238/CONTOURS-IRIS_3-0_SHP_LAMB93_FXX-ED2023-01-01/"

URLS = {
    BUREAUX : "https://www.data.gouv.fr/fr/datasets/r/d2392385-c12f-4b1b-8940-37da09be6333",
    ELECTIONS : "https://www.data.gouv.fr/fr/datasets/r/1996b2bc-e95a-4481-904f-28d16987fe61",
    IRIS_FOLDER : f"{IRIS_URL}!{IRIS_7Z_FOLDER}",
    DEMOGRAPHIE : "https://www.insee.fr/fr/statistiques/fichier/7704076/base-ic-evol-struct-pop-2020_csv.zip!base-ic-evol-struct-pop-2020.CSV"
}

OUT_JOINED="data/out/joined.shp"

CACHE_FOLDER="data/cache"

PARTIS_CODES = {
    "RN": "La FRANCE REVIENT",
    "LREM" : "BESOIN D'EUROPE",
    "LFI" : "LFI - UP",
    "PCF" : "GAUCHE UNIE",
    "LR" : "LA DROITE POUR FAIRE ENTENDRE LA VOIX DE LA FRANCE EN EUROPE",
    "EELV" : "EUROPE ÉCOLOGIE",
    "PS" : "REVEIL EUR",
    "AR" : "AR",
    "RECONQUETE" : "LA FRANCE FIERE, MENEE PAR MARION MARECHAL ET SOUTENUE PAR ÉRIC ZEMMOUR"
}

CSP_MAPPING = {
    "csp_agriculteur" : "C20_POP15P_CS1",
    "csp_independant" : "C20_POP15P_CS2",
    "csp_plus" : "C20_POP15P_CS3",
    "csp_intermediaire" : "C20_POP15P_CS4",
    "csp_employe" : "C20_POP15P_CS5",
    "csp_ouvrier" : "C20_POP15P_CS6",
    "csp_retraite" : "C20_POP15P_CS7",
    "csp_sans_emploi" : "C20_POP15P_CS8"
}

AGE_MAP = {
    "P20_POP0002" : 1,
    "P20_POP0305" : 4,
    "P20_POP0610" : 8,
    "P20_POP1117" : 14,
    "P20_POP1824" : 21,
    "P20_POP2539" : 32 ,
    "P20_POP4054" : 47,
    "P20_POP5564" : 59,
    "P20_POP6579" : 72,
    "P20_POP80P"  : 90 }


def mk_dirs():
    makedirs("data/in", exist_ok=True)
    makedirs(CACHE_FOLDER, exist_ok=True)
    makedirs("data/out", exist_ok=True)


def cached(func) :

    cache_filename = f"{CACHE_FOLDER}/{func.__name__}.pkl"
    def wrapper() :

        if os.path.exists(cache_filename) :
            with open(cache_filename, "rb") as f:
                res = pickle.load(f)
        else:
            print(f"Loading ... {func.__name__}")
            res = func()
            with open(cache_filename, "wb") as f:
                pickle.dump(res, f)
        print(f"Number items of {func.__name__}: {len(res)}")
        return res

    return wrapper

@cached
def load_elections():
    df =  pd.read_excel(ELECTIONS)
    return transform_elections(df)

def transform_elections(df):

    first_row = df.iloc[0]

    dic_partis = dict()

    for col in first_row.index :
        if col.startswith("Libellé abrégé de liste"):
            val = first_row[col]
            num = int(col.replace("Libellé abrégé de liste ", ""))
            dic_partis[val] = num

    # Bureau key made of insee commune code + _ + bureau
    keys = df.apply(lambda row : row["Code commune"] + "_" + row["Code BV"], axis=1)

    inscrits = df["Inscrits"]
    votants = df["Votants"]

    data = dict(
        nb_inscrit = inscrits.values,
        nb_votant = votants.values,
        nb_abstention = df["Abstentions"].values,
        nb_blanc = df["Blancs"].values,
        nb_nul = df["Nuls"].values)

    for code_parti, nom_parti in PARTIS_CODES.items():
        num_parti = dic_partis[nom_parti]
        data[f"nb_{code_parti}"] = df[f"Voix {num_parti}"].values

    return pd.DataFrame(
        data=data,
        index=keys)

@cached
def load_bureaux():
    bureaux = gp.read_file(BUREAUX)
    bureaux = bureaux.to_crs(CRS)
    return transform_bureaux(bureaux)

def transform_bureaux(df):

    def generate_key(row):

        bureau = row["bureau"]
        insee = row["insee"]

        if bureau is None :
            bureau = "0001"
        else:
            code_postal, bureau = bureau.split("_")

            # Paris
            if insee == "75056":
                arrond = code_postal[3:6]
                bureau = arrond + bureau.zfill(2)

        bureau = bureau.zfill(4)
        return row["insee"] + "_" + bureau

    keys = df.apply(generate_key, axis=1)

    return gp.GeoDataFrame(
        index=keys,
        geometry=df.geometry.values)

@cached
def load_iris():
    iris = gp.read_file(IRIS)
    index = iris.CODE_IRIS.str.zfill(9)

    return gp.GeoDataFrame(
        data=dict(

            nom_commune=iris.NOM_COM.values),
        index=index.values,
        geometry=iris.geometry.values)


def spatial_join_iris(iris_df:GeoDataFrame, other_df:GeoDataFrame) :
    iris_df = iris_df.copy()
    iris_df.reset_index(inplace=True, names="iris_id")

    other_df["sample_point"] = other_df.geometry.sample_points(1)
    other_df.set_geometry("sample_point", inplace=True)

    joined = iris_df.sjoin(other_df, how="inner")
    return joined

def group_sum_by_iris(iris, other) :
    res = spatial_join_iris(iris, other)
    res.drop(columns=["nom_commune", "geometry_left", "geometry_right"], inplace=True)
    res = res.groupby("iris_id").sum()
    res.drop(columns="index_right", inplace=True)
    return res

def votants_to_score(elecs_df) :

    data = dict(
        inscrits = elecs_df.nb_inscrit.values,
        votants = elecs_df.nb_votant.values,
        pct_abstention = (elecs_df.nb_abstention / elecs_df.nb_inscrit * 100).values,
    )

    for col in elecs_df.columns :
        if not col.startswith("nb_"):
            continue
        if col in ["nb_votant", "nb_inscrit", "nb_abstention"]:
            continue
        col_out = "score_" + col.replace("nb_", "")
        data[col_out] = ((elecs_df[col] / elecs_df.nb_votant) * 100).values

    return pd.DataFrame(
        data,
        index=elecs_df.index)



def spatial_join(bureaux:GeoDataFrame, iris:GeoDataFrame):

    bureaux = bureaux.copy()

    # Sample a point in bureau polygon
    bureaux["sample_point"] = bureaux.geometry.sample_points(1)
    bureaux.set_geometry("sample_point", inplace=True)

    # Ensure we have spatial indexes
    iris.sindex
    bureaux.sindex

    joined_df = gp.sjoin(left_df=bureaux, right_df=iris, how="inner")
    joined_df.drop(columns=["sample_point"], inplace=True)
    joined_df.set_geometry("geometry", inplace=True)

    return joined_df

def normalize(input_str):
    res = unicodedata.normalize('NFKD', input_str)
    res = res.encode('ASCII', 'ignore')
    res = res.replace(" ", "_")
    return res


@cached
def load_demographie():
    df = pd.read_csv(DEMOGRAPHIE, sep=";")
    return transform_demo(df)


def transform_demo(df):

    df["IRIS"] = df.IRIS.astype(str).str.zfill(9)
    df.set_index("IRIS", inplace=True)

    pop = df.P20_POP
    pop15ans = df.C20_POP15P

    # Compute mean age
    age_tot = 0
    for col, age in AGE_MAP.items():
        age_tot += age * df[col]
    age_moy = age_tot / pop

    data = dict(
        pop_totale = pop,
        pct_0_19 = df.P20_F0019 / pop * 100,
        pct_20_64 = df.P20_F2064 / pop * 100,
        pct_65_plus = df.P20_F65P / pop * 100,
        pct_etrangers = (df.P20_POP_ETR / pop * 100).values,
        pct_immigres = (df.P20_POP_IMM / pop * 100).values,
        age_moyen = age_moy.values)

    # Compute percentage of CSP categories
    for csp_name, col_name in CSP_MAPPING.items() :
        data["pct_" + csp_name] = df[col_name] / pop15ans * 100

    return pd.DataFrame(
        index=df.index.values,
        data=data)

def download(source_url, dest):
    if os.path.exists(dest):
        print(f"File exists : {dest}. skipping")
        return

    if "!" in source_url:
        source_url, zip_entry = source_url.split("!")
        with TemporaryDirectory() as tmp_dir:
            tmp_filename = path.join(tmp_dir, basename(source_url))
            print(f"Downloading {source_url} to temp zip file")
            safe_url_retrieve(source_url, tmp_filename)
            print(f"Extracting {zip_entry} to {dest}")
            extract_to(tmp_filename, zip_entry, dest)
    else:
        print(f"Downloading {source_url}")
        safe_url_retrieve(source_url, dest)

def download_all() :
    for dest, url in URLS.items() :
        download(url, dest)


def extract_to(filename, source, dest) :

    with TemporaryDirectory() as tmp_dir:

        if filename.endswith(".7z"):
            with py7zr.SevenZipFile(filename, "r") as zip :
                contents = [name for name in zip.getnames() if name.startswith(source)]
                zip.extract(tmp_dir, contents)
        elif filename.endswith(".zip"):
            with zipfile.ZipFile(filename) as z:
                z.extract(source, tmp_dir)
        else:
            raise Exception(f"File type not supported : {filename}")
        move(path.join(tmp_dir, source), dest)


def safe_url_retrieve(url, filename):
    """Fetch a file faking user agent"""
    headers={'user-agent': 'Mozilla/5.0'}
    r= requests.get(url, headers=headers)
    with open(filename, 'wb') as f:
        f.write(r.content)



