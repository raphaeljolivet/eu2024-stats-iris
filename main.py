from utils import *

def main() :

    # Create folders
    mk_dirs()

    # Download source files
    download_all()

    # Load files
    iris = load_iris()
    bureaux = load_bureaux()
    elections = load_elections()
    demographie = load_demographie()

    # Add geometry to bureaux
    bureaux_elections = bureaux.join(elections, how="inner")

    # Group by iris
    iris_elections = group_sum_by_iris(iris, bureaux_elections)
    iris_elections = votants_to_score(iris_elections)

    # Join demography
    iris_all = iris_elections.join(demographie, how="inner")

    # Add iris geometry
    iris_all = iris.join(iris_all, how="inner")

    # Save output
    iris_all.to_file("data/out/iris-stats.geojson")
    iris_all.to_file("data/out/iris-stats.gpkg")


if __name__ == '__main__':
    main()