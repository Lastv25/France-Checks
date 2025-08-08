import streamlit as st

# Page Navigation
pages = [
    st.Page("app_pages/introduction.py", title="Introduction"),
    st.Page("app_pages/check.py", title="Natural Person Check"),
]

# Adding pages to the sidebar navigation
pg = st.navigation(pages, position="sidebar", expanded=True)

# Running the app
pg.run()
