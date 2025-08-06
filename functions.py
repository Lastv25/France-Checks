import requests
import polars as pl
import json

from models import FranceCompany, Jugement, Dirigeant

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

    # Parse dirigeants data
    dirigeants = []
    if "dirigeants" in record and record["dirigeants"]:
        for dirigeant_data in record["dirigeants"]:
            dirigeants.append(Dirigeant(**dirigeant_data))
    dirigeants_txt = "\n".join([d.display_info for d in dirigeants])

    company = FranceCompany(
        Siren=record["siren"],
        CompanyName=record["nom_complet"],
        Sector=record["activite_principale"],
        Address=record["siege"]["adresse"],
        CreationDate=record["date_creation"],
        Dirigeants=dirigeants_txt
    )

    return company


def get_pcl_record(Siren: str) -> pl.DataFrame:
    api_url = f"https://bodacc-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/annonces-commerciales/records?where=search%28%22Proc%C3%A9dures%20collectives%22%29%20and%20search%28%22{Siren}%22%29&limit=100&offset=0&timezone=UTC&include_links=false&include_app_metas=false"

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
            pl.col("dateparution").alias("PublicationDate"),
            pl.col("familleavis_lib").alias("Nature"),
            pl.col("jugement").alias("Jugement"),
            pl.col("url_complete").alias("Url"),
        ]
    )
    
    if len(df) == 0:
        return df.drop("Jugement").with_columns(
            pl.lit(None).alias("Jugement_Type"),
            pl.lit(None).alias("Jugement_Famille"),
            pl.lit(None).alias("Jugement_Nature"),
            pl.lit(None).alias("Jugement_Date"),
            pl.lit(None).alias("Jugement_Complement")
        )
    
    jugement_data = []
    for row in df.iter_rows(named=True):
        jugement_str = row.get('Jugement', '')
        if jugement_str:
            jugement_obj = Jugement.from_json_string(jugement_str)
            jugement_data.append({
                'Jugement_Type': jugement_obj.type,
                'Jugement_Famille': jugement_obj.famille,
                'Jugement_Nature': jugement_obj.nature,
                'Jugement_Date': jugement_obj.date,
                'Jugement_Complement': jugement_obj.complementJugement
            })
        else:
            jugement_data.append({
                'Jugement_Type': None,
                'Jugement_Famille': None,
                'Jugement_Nature': None,
                'Jugement_Date': None,
                'Jugement_Complement': None
            })
    
    # Create a DataFrame with the parsed Jugement data
    jugement_df = pl.DataFrame(jugement_data)
    
    # Join with the original DataFrame (excluding the original Jugement column)
    result_df = df.select([
        pl.col("Siren"),
        pl.col("CompanyName"),
        pl.col("PublicationDate"),
        pl.col("Nature"),
        pl.col("Url")
    ]).hstack(jugement_df)

    return result_df


def parse_jugement_string(jugement_str: str) -> Jugement:
    """
    Parse a single Jugement JSON string into a Jugement object
    """
    return Jugement.from_json_string(jugement_str)