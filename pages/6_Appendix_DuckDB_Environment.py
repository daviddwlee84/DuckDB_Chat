from typing import Optional
import streamlit as st
import duckdb
from streamlit_searchbox import st_searchbox
import pandas as pd
from fast_autocomplete import AutoComplete

# streamlit.errors.StreamlitAPIException: `set_page_config()` can only be called once per app page, and must be called as the first Streamlit command in your script.
st.set_page_config(page_title="Appendix: DuckDB Environment")
st.title("Appendix: DuckDB Environment")

"""
- [DuckDB Environment - DuckDB](https://duckdb.org/docs/guides/meta/duckdb_environment)
- [DuckDB_% Metadata Functions - DuckDB](https://duckdb.org/docs/sql/duckdb_table_functions.html)
"""

commands = {}

duckdb_connect: Optional[duckdb.DuckDBPyConnection] = (
    st.session_state.duckdb_connect.cursor()
    if "duckdb_connect" in st.session_state
    else None
)


def duckdb_autocomplete(
    query: str,  # , duckdb_connect: Optional[duckdb.DuckDBPyConnection]
) -> pd.Series:
    """
    https://duckdb.org/docs/extensions/autocomplete.html

    TODO:
    https://stackoverflow.com/questions/8760430/does-a-b-tree-work-well-for-auto-suggest-auto-complete-web-forms
    https://stackoverflow.com/questions/61468269/autcomplete-words-that-were-previously-on-a-list

    https://github.com/duckdb/duckdb/issues/2891
    https://github.com/duckdb/duckdb/pull/2895
    https://github.com/duckdb/duckdb/tree/ff7f24fd8e3128d94371827523dae85ebaf58713/third_party/libpg_query/grammar/keywords

    TODO: https://duckdb.org/docs/extensions/full_text_search
    """
    global duckdb_connect
    # Table Function with name sql_auto_complete does not exist!
    template = "FROM sql_auto_complete('{query}');"
    if duckdb_connect is None:
        duckdb.install_extension("autocomplete")
        duckdb.load_extension("autocomplete")
        return duckdb.execute(template.format(query=query)).df()["suggestion"]
    else:
        duckdb_connect.install_extension("autocomplete")
        duckdb_connect.load_extension("autocomplete")
        return duckdb_connect.execute(template.format(query=query)).df()["suggestion"]


if duckdb_connect is not None:
    st.caption("Found DuckDB connection")
    commands["Tables"] = "SHOW ALL TABLES;"

st.subheader("Test Auto-Complete")
# https://github.com/m-wrzr/streamlit-searchbox
st.write(command := st_searchbox(duckdb_autocomplete, key="duckdb_autocomplete"))
if command:
    if duckdb_connect:
        st.dataframe(
            duckdb_connect.execute(
                f"SELECT * FROM duckdb_functions() WHERE function_name = '{command.strip().lower()}';"
            ).df()
        )
    else:
        st.dataframe(
            duckdb.execute(
                f"SELECT * FROM duckdb_functions() WHERE function_name = lower('{command.strip()}';"
            ).df()
        )

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


def duckdb_func_autocomplete(query: str) -> pd.Series:
    """
    https://github.com/seperman/fast-autocomplete
    """
    words = {
        func: {}
        for func in duckdb.execute(
            "SELECT DISTINCT(function_name) AS function_name FROM duckdb_functions();"
        ).df()["function_name"]
    }
    ac = AutoComplete(words=words)
    print(ac.search(query))
    return [res[0] for res in ac.search(query)]


st.divider()
st.subheader("Function Description")
st.dataframe(
    duckdb.execute(
        "SELECT function_name, FIRST(description) AS description FROM duckdb_functions() WHERE description IS NOT NULL GROUP BY function_name",
        connection=duckdb_connect,
    ).df()
)

# BUG: somehow this is unstable: crash without error
st.write(func := st_searchbox(duckdb_func_autocomplete, key="duckdb_func_autocomplete"))
result = duckdb.execute(
    f"SELECT function_name, FIRST(description) AS description FROM duckdb_functions() WHERE function_name = '{func}' GROUP BY function_name",
    connection=duckdb_connect,
).df()
if not result.empty:
    st.write(result["description"][0])
