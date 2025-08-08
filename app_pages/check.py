import polars as pl
import streamlit as st

# Disable unsecure warning
import urllib3
from streamlit_agraph import Config, Edge, Node, agraph

from functions import (
    get_companies,
    get_company_info,
    get_pcl_record,
    remove_accents,
    to_upper_no_accents,
)
from models.models import Dirigeant, FranceCompany

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def page_content():
    st.set_page_config(
        page_title="France Checks",
        page_icon=":mag:",
    )
    
    nodes = []
    edges = []
    
    st.title(":mag: France Checks")
    
    st.text(
        "This app checks the existence of a company in France based on the provided first and last name."
    )
    st.warning(
        "This app does not perform exact matching on the First Name and Last Name, results given need to be carefully reviewed. The source used is BODACC.",
        icon="⚠️",
    )
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        first_name = st.text_input("First Name")
    with col2:
        last_name = st.text_input("Last Name")
    with col3:
        birthdate = st.text_input("Birthdate")
    with col4:
        nationality = st.text_input("Nationality")
    # filtering results
    col5, col6, col7 = st.columns(3)
    with col5:
        name_filter = st.segmented_control(
            "Filter on Name",
            ["Perfect match", "Strong Match", "All"],
            default="Perfect match",
        )
    with col6:
        date_filter = st.segmented_control(
            "Filter on Date", ["Perfect match", "Strong Match", "All"], default="All"
        )
    with col7:
        nationality_filter = st.segmented_control(
            "Filter on Nationality", ["Perfect match", "Strong Match", "All"], default="All"
        )
    # max hits
    max_number_hits = st.number_input("Max Nbr of Bodacc Publications to find", value=100)
    # max hits
    if st.button("Check"):
        reference_entity = Dirigeant(
            **{
                "prenoms": first_name,
                "nom": last_name,
                "date_de_naissance": birthdate,
                "nationalite": nationality,
            }
        )
        df = get_companies(first_name, last_name, max_number_hits)
    
        nbr_hits = df.height
    
        companies = pl.DataFrame(schema=FranceCompany())
        companies = companies.cast(
            {
                "Siren": pl.String,
                "CompanyName": pl.String,
                "Sector": pl.String,
                "Address": pl.String,
                "CreationDate": pl.String,
                "Dirigeants": pl.String,
                "NamesScoresMax": pl.Int64,
                "BirthDateScoresMax": pl.Int64,
                "NationalityScoresMax": pl.Int64,
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
        processing_text = f"Found {nbr_hits} possible matches."
        processing_bar = st.progress(
            0, text=processing_text + " Currently processing nbr 1"
        )
        process_complete = 0
        df = df.unique()
        for row in df.iter_rows(named=True):
            process_complete += 1
            processing_bar.progress(
                int(process_complete / nbr_hits * 100),
                text=processing_text + f" Currently processing {process_complete}",
            )
            try:
                print(f'Fetching company info for {row["Siren"]}')
                company_info = get_company_info(row["Siren"], reference_entity)
    
                if name_filter != "All":
                    if name_filter == "Perfect match":
                        if company_info.NamesScoresMax != 100:
                            continue
                    else:
                        if company_info.NamesScoresMax <= 80:
                            continue
    
                if date_filter != "All":
                    if date_filter == "Perfect match":
                        if company_info.BirthDateScoresMax != 200:
                            continue
                    else:
                        if company_info.BirthDateScoresMax <= 150:
                            continue
                if nationality_filter != "All":
                    if nationality_filter == "Perfect match":
                        if company_info.NationalityScoresMax != 100:
                            continue
                    else:
                        if company_info.NationalityScoresMax <= 80:
                            continue
                if company_info.CompanyName is not None:
                    companies = companies.vstack(pl.DataFrame([company_info.model_dump()]))
    
                try:
                    print(f"Fetching PCL For: {row['Siren']}")
                    if row["Siren"] is not None:
                        pcl_record = get_pcl_record(row["Siren"])
                        if not pcl_record.is_empty():
                            pcl = pcl.vstack(pcl_record)
                except Exception as e:
                    print(f"Failed to get PCL record for {row['Siren']}: {e}")
            except Exception as e:
                print(f"Failed to get company info for {row['Siren']}: {e}")
    
        result = df.join(companies.drop("CompanyName"), on="Siren")
        result = result.unique()
        processing_bar.empty()
    
        if df.is_empty():
            st.warning("No company found.")
        else:
            st.success("Companies found from bodacc publications:")
    
            st.dataframe(
                result.select(
                    [
                        "Siren",
                        "CompanyName",
                        "Sector",
                        "Address",
                        "CreationDate",
                        "Dirigeants",
                    ]
                )
            )
    
            if not pcl.is_empty():
                st.subheader("Procedures Collectives Records:")
                st.dataframe(
                    pcl.select(
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
                st.info("No Procedures Collectives records found for the companies.")
    
        name = f"{first_name} {last_name}"
        normalized_name = to_upper_no_accents(name)
        graph_companies = result.filter(
            pl.col("Dirigeants").str.contains(f"{normalized_name}", literal=True)
        )
    
        st.markdown(
            "###### Graph Representation (only showing companies with matching director):"
        )
        nodes.append(
            Node(
                id="Person",
                label=f"{first_name} {last_name}",
                size=25,
                font={"color": "white"},
                image="https://raw.githubusercontent.com/material-icons/material-icons-png/refs/heads/master/png/white/person/baseline-2x.png",
                shape="circularImage",
            )
        )
        already_exists = []
        for row in graph_companies.iter_rows(named=True):
            if f"{row['Siren']}" in already_exists:
                continue
            nodes.append(
                Node(
                    id=f"{row['Siren']}",
                    label=row["CompanyName"],
                    color="green",
                    font={"color": "white"},
                    size=25,
                    link=f"https://www.pappers.fr/entreprise/{row['Siren']}",
                    image="https://raw.githubusercontent.com/material-icons/material-icons-png/refs/heads/master/png/white/business/baseline-2x.png",
                    shape="circularImage",
                )
            )
            already_exists.append(f"{row['Siren']}")
            edges.append(
                Edge(
                    source="Person",
                    target=f"{row['Siren']}",
                )
            )
    
        config = Config(
            width=700,
            height=500,
            directed=True,
            physics=True,
            hierarchical=False,
            highlightColor="#F0F0F0",
            nodeHighlightBehavior=True,
        )
    
        return_value = agraph(nodes=nodes, edges=edges, config=config)

if __name__ == '__main__':
    page_content()
