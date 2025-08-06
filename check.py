import streamlit as st
import polars as pl

from functions import get_companies, get_company_info, get_pcl_record
from models import FranceCompany

st.set_page_config(
    page_title="France Checks",
    page_icon=":mag:",
)

st.title("France Checks")

st.text("This app checks the existence of a company in France based on the provided first and last name.")
st.warning(
    "This app does not perform exact matching on the First Name and Last Name, results given need to be carefully reviewed. The source used is BODACC.", 
    icon="⚠️"
)

col1, col2 = st.columns(2)

with col1:
    first_name = st.text_input("First Name")
with col2:
    last_name = st.text_input("Last Name")

if st.button("Check"):
    df = get_companies(first_name, last_name)

    companies = pl.DataFrame(schema=FranceCompany())
    companies = companies.cast(
        {
            "Siren": pl.String,
            "CompanyName": pl.String,
            "Sector": pl.String,
            "Address": pl.String,
            "CreationDate": pl.String,
            "Dirigeants": pl.String,
        }
    )

    pcl = pl.DataFrame(
        {
            "Siren": [],
            "CompanyName": [],
            "PublicationDate": [],
            "Nature": [],
            "Url": [],
            "Jugement_Type": [],
            "Jugement_Famille": [],
            "Jugement_Nature": [],
            "Jugement_Date": [],
            "Jugement_Complement": [],
        }
    )

    pcl = pcl.cast(
        {
            "Siren": pl.String,
            "CompanyName": pl.String,
            "PublicationDate": pl.String,
            "Nature": pl.String,
            "Url": pl.String,
            "Jugement_Type": pl.String,
            "Jugement_Famille": pl.String,
            "Jugement_Nature": pl.String,
            "Jugement_Date": pl.String,
            "Jugement_Complement": pl.String,
        }
    )

    for row in df.iter_rows(named=True):
        try:
            company_info = get_company_info(row['Siren'])

            if company_info.CompanyName is not None:
                companies = companies.vstack(pl.DataFrame([company_info.dict()]))

            try:
               print(f"Processing company: {row['Siren']}")
               if row['Siren'] is not None:
                   pcl_record = get_pcl_record(row['Siren'])
                   if not pcl_record.is_empty():
                       pcl = pcl.vstack(pcl_record)
            except Exception as e:
               print(f"Failed to get PCL record for {row['Siren']}: {e}")
        except Exception as e:
            print(f"Failed to get company info for {row['Siren']}: {e}")

    result = df.join(companies.drop("CompanyName"), on="Siren", how="left")

    if df.is_empty():
        st.warning("No company found.")
    else:
        st.success("Companies found:")
        st.dataframe(result)

        if not pcl.is_empty():
            st.subheader("Procedures Collectives Records:")
            st.dataframe(
                pcl
                .select(
                    [
                        pl.col("Siren"),
                        pl.col("CompanyName"),
                        pl.col("PublicationDate"),
                        pl.col("Jugement_Nature"),
                        pl.col("Jugement_Date"),
                        pl.col("Jugement_Complement"),
                        pl.col("Url"),
                    ]
                )
            )
        else:
            st.info("No Procedures Collectives records found for the company.")