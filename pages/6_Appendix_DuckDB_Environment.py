import streamlit as st
import duckdb

# streamlit.errors.StreamlitAPIException: `set_page_config()` can only be called once per app page, and must be called as the first Streamlit command in your script.
st.set_page_config(page_title="Appendix: DuckDB Environment")
st.title("Appendix: DuckDB Environment")

"""
[DuckDB Environment - DuckDB](https://duckdb.org/docs/guides/meta/duckdb_environment)
"""

commands = {}

duckdb_connect = (
    st.session_state.duckdb_connect.cursor()
    if "duckdb_connect" in st.session_state
    else None
)
if duckdb_connect is not None:
    st.caption("Found DuckDB connection")
    commands["Tables"] = "SHOW ALL TABLES;"

commands.update(
    {
        "Version Number of DuckDB": "SELECT version();",
        "Detail Version Number of DuckDB": "PRAGMA version;",
        "Columns": "SELECT * FROM duckdb_columns()",
        "Constraints": "SELECT * FROM duckdb_constraints()",
        "Lists the databases that are accessible from within the current DuckDB process": "SELECT * FROM duckdb_databases()",
        "Dependencies between objects": "SELECT * FROM duckdb_dependencies()",
        "Extensions": "SELECT * FROM duckdb_extensions()",
        "Functions": "SELECT * FROM duckdb_functions()",
        "Secondary indexes": "SELECT * FROM duckdb_indexes()",
        "DuckDB's keywords and reversed words": "SELECT * FROM duckdb_keywords()",
        # duckdb.CatalogException: Catalog Error: Table Function with name duckdb_optimizers does not exist!
        # "The available optimization rules in the DuckDB instance": "SELECT * FROM duckdb_optimizers()",
        "Schemas": "SELECT * FROM duckdb_schemas()",
        "Sequences": "SELECT * FROM duckdb_sequences()",
        "Settings": "SELECT * FROM duckdb_settings()",
        "Base tables": "SELECT * FROM duckdb_tables()",
        "Data types": "SELECT * FROM duckdb_types()",
        "Views": "SELECT * FROM duckdb_views()",
        "Temporary files": "SELECT * FROM duckdb_temporary_files()",
    }
)


for describe, command in commands.items():
    st.subheader(describe)
    st.dataframe(duckdb.execute(command, connection=duckdb_connect).df())
