import streamlit as st
import polars as pl

from functions import get_companies, get_company_info, get_pcl_record

st.title("France Checks")

st.text("This app checks the existence of a company in France based on the provided first and last names.")

col1, col2 = st.columns(2)

with col1:
    first_name = st.text_input("First Name")
with col2:
    last_name = st.text_input("Last Name")

if st.button("Check"):
    df = get_companies(first_name, last_name)
    if df.is_empty():
        st.warning("No company found.")
    else:
        st.success("Company found:")
        st.dataframe(df)