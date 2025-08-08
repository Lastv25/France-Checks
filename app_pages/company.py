import polars as pl
import streamlit as st


from helpers.api_calls import get_company_info_from_recherche_entreprise

def page_content():

    siren = st.text_input("Siren")

    if siren != '' and siren is not None:
        print('Siren:', siren)
        company_info = get_company_info_from_recherche_entreprise(siren, 100)
        print(company_info)
        print('T'*100)


if __name__ == "__main__":
    page_content()
