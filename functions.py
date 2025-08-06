import requests
import polars as pl

from models import FranceCompany

def get_companies(FirstName: str, LastName: str) -> pl.DataFrame:
    api_url = f"https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records?where=search%28%22{FirstName}%22%29%20and%20search%28%22{LastName}%22%29&limit=100&offset=0&timezone=UTC&include_links=false&include_app_metas=false"

    response = requests.get(api_url, verify=False)
    response.raise_for_status()

    data = response.json()

    records = data["results"]

    df = pl.DataFrame(records)

    df = df.select(
        [
            pl.col("registre")
            .list.eval(pl.element().filter(pl.element().str.contains(r"^\d{9}$")))
            .list.first()
            .alias("Siren"),
            pl.col("commercant").alias("CompanyName"),
        ]
    )

    return df.unique(maintain_order=True)


def get_company_info(Siren: str) -> FranceCompany:
    api_url = f"https://recherche-entreprises.api.gouv.fr/search?q={Siren}&minimal=true&limite_matching_etablissements=1&include=siege%2Cdirigeants%2Cfinances%2Cscore&page=1&per_page=1"

    response = requests.get(api_url, verify=False)
    response.raise_for_status()

    data = response.json()

    record = data["results"][0]

    company = FranceCompany(
        Siren=record["siren"],
        CompanyName=record["nom_complet"],
        Sector=record["activite_principale"],
        Address=record["siege"]["adresse"],
        CreationDate=record["date_creation"],
    )

    return company


def get_pcl_record(Siren: str) -> pl.DataFrame:
    api_url = f"https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records?where=search%28%22Proc%C3%A9dures%20collectives%22%29%20and%20search%28%22{Siren}%22%29&limit=100&offset=0&timezone=UTC&include_links=false&include_app_metas=false"

    response = requests.get(api_url, verify=False)
    response.raise_for_status()

    data = response.json()

    records = data["results"]

    df = pl.DataFrame(records)

    return df.select(
        [
            pl.col("registre")
            .list.eval(pl.element().filter(pl.element().str.contains(r"^\d{9}$")))
            .list.first()
            .alias("Siren"),
            pl.col("commercant").alias("CompanyName"),
            pl.col("dateparution").alias("PublicationDate"),
            pl.col("familleavis_lib").alias("Nature"),
            pl.col("jugement").alias("Jugement"),
            pl.col("url_complete").alias("Url"),
        ]
    )