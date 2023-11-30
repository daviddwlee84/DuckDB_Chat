import streamlit as st
import duckdb
from langchain.utilities.sql_database import SQLDatabase
import pandas as pd

st.set_page_config(page_title="Database Question Answering")

st.title("Database Question Answering")

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.duckdb_connect = duckdb.connect(database=":default:")

duckdb_connect = st.session_state.duckdb_connect.cursor()

with st.expander("Settings"):
    default_table_name = st.text_input("Default Table Name", "tbl")

uploaded_file = st.file_uploader(
    "Data you want to query (support CSV, Parquet, and Json).",
    accept_multiple_files=False,
)

if uploaded_file is None:
    st.session_state.messages = []
else:
    if st.session_state.uploaded_file != uploaded_file:
        st.session_state.messages = []
        st.session_state.uploaded_file = uploaded_file

        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".parquet"):
            df = pd.read_parquet(uploaded_file)
        else:
            st.error("Please provide valid file.")
            st.stop()
        duckdb_connect.register(default_table_name, df)

    db = SQLDatabase.from_uri("duckdb:///:default:")

    # st.write(st.session_state.duckdb_connect.sql(f"DESCRIBE {default_table_name};").df())
    st.write(duckdb_connect.execute(f"DESCRIBE {default_table_name};").df())
    st.write(duckdb_connect.sql(f"SELECT * FROM {default_table_name};").df())
    st.write(db)
    st.write(db.get_table_info())
    st.write(db.get_usable_table_names())
