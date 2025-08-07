import json
import unicodedata

import polars as pl
import requests

from helpers.api_calls import (
    get_company_info_from_recherche_entreprise,
    get_pcl_record_from_bodacc,
    get_publications_from_bodacc,
)
from helpers.entity_matching import (
    compute_date_similarity_score,
    compute_name_similarity_score,
    compute_nationality_similarity_score,
)
from models.models import Dirigeant, FranceCompany, Jugement


def get_companies(
    FirstName: str, LastName: str, MaxNumberHits: int = 100
) -> pl.DataFrame:
    data = get_publications_from_bodacc(FirstName, LastName, MaxNumberHits)

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


def get_company_info(Siren: str, ReferenceEntity: Dirigeant) -> FranceCompany:
    data = get_company_info_from_recherche_entreprise(Siren)

    # since we searched by siren only one result can be found by the
    # api call
    record = data["results"][0]

    # Parse dirigeants data
    dirigeants = []
    name_score_matches = [0]
    date_score_matches = [0]
    nationality_score_matches = [0]
    if "dirigeants" in record and record["dirigeants"]:
        for dirigeant_data in record["dirigeants"]:
            current_director = Dirigeant(**dirigeant_data)
            name_score_matches.append(
                compute_name_similarity_score(ReferenceEntity, current_director)
            )
            date_score_matches.append(
                compute_date_similarity_score(ReferenceEntity, current_director)
            )
            nationality_score_matches.append(
                compute_nationality_similarity_score(ReferenceEntity, current_director)
            )
            dirigeants.append(Dirigeant(**dirigeant_data))
    dirigeants_txt = "\n".join([d.display_info for d in dirigeants])

    company = FranceCompany(
        Siren=record["siren"],
        CompanyName=record["nom_complet"],
        Sector=record["activite_principale"],
        Address=record["siege"]["adresse"],
        CreationDate=record["date_creation"],
        Dirigeants=dirigeants_txt,
        NamesScoresMax=max(name_score_matches),
        BirthDateScoresMax=max(date_score_matches),
        NationalityScoresMax=max(nationality_score_matches),
    )
    return company


def get_pcl_record(Siren: str) -> pl.DataFrame:
    data = get_pcl_record_from_bodacc(Siren)

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
            pl.lit(None).alias("Jugement_Complement"),
        )

    jugement_data = []
    for row in df.iter_rows(named=True):
        jugement_str = row.get("Jugement", "")
        if jugement_str:
            jugement_obj = Jugement.from_json_string(jugement_str)
            jugement_data.append(
                {
                    "Jugement_Type": jugement_obj.type,
                    "Jugement_Famille": jugement_obj.famille,
                    "Jugement_Nature": jugement_obj.nature,
                    "Jugement_Date": jugement_obj.date,
                    "Jugement_Complement": jugement_obj.complementJugement,
                }
            )
        else:
            jugement_data.append(
                {
                    "Jugement_Type": None,
                    "Jugement_Famille": None,
                    "Jugement_Nature": None,
                    "Jugement_Date": None,
                    "Jugement_Complement": None,
                }
            )

    # Create a DataFrame with the parsed Jugement data
    jugement_df = pl.DataFrame(jugement_data)

    # Join with the original DataFrame (excluding the original Jugement column)
    result_df = df.select(
        [
            pl.col("Siren"),
            pl.col("CompanyName"),
            pl.col("PublicationDate"),
            pl.col("Nature"),
            pl.col("Url"),
        ]
    ).hstack(jugement_df)

    return result_df


def parse_jugement_string(jugement_str: str) -> Jugement:
    """
    Parse a single Jugement JSON string into a Jugement object
    """
    return Jugement.from_json_string(jugement_str)


def remove_accents(input_str):
    # Normalize string (NFD decomposes combined characters)
    nfkd_form = unicodedata.normalize("NFD", input_str)
    # Remove accent characters
    only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return only_ascii


def to_upper_no_accents(name):
    no_accents = remove_accents(name)
    return no_accents.upper()
