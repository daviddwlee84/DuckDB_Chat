import streamlit as st
import duckdb
from langchain.utilities.sql_database import SQLDatabase
import pandas as pd
from sqlalchemy import create_engine
import sqlite3

st.set_page_config(page_title="Database Question Answering")

st.title("Database Question Answering")

table_name = st.text_input(
    "Table Name (better be meaningful and related to the file you uploaded)",
    value="tbl",
)

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.db_engine = create_engine("sqlite:///:memory:")
    # st.session_state.db_engine = create_engine("sqlite:///temp.db")
    st.session_state.data = None

sqlite_connect = sqlite3.connect(":memory:")
# sqlite_connect = sqlite3.connect("temp.db")

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
            st.session_state.data = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".parquet"):
            st.session_state.data = pd.read_parquet(uploaded_file)
        else:
            st.error("Please provide valid file.")
            st.stop()

    # ProgrammingError: SQLite objects created in a thread can only be used in that same thread.
    # st.session_state.data.to_sql("tbl", sqlite_connect)
    st.session_state.data.to_sql(table_name, st.session_state.db_engine)

    db = SQLDatabase(
        st.session_state.db_engine,
        # Include all table (but seems there will be no previous tables)
        # include_tables=[table_name],
        sample_rows_in_table_info=3,
    )

    # st.write(sqlite_connect.execute(f"SELECT * FROM {table_name};").fetchall())
    st.write(db)
    st.write(db.get_table_info())
    st.write(db.get_usable_table_names())
