import streamlit as st
import duckdb
import time
import pandas as pd
import re
from utils import QueryRewriterForDuckDB

# import matplotlib.pyplot as plt


TEMP_TABLE_NAME = "_temp"

# import shutil
# import os

# from streamlit.runtime.uploaded_file_manager import UploadedFileManager
# import tempfile

# from functools import partial
# import pandas as pd
# from streamlit.delta_generator import DeltaGenerator

st.set_page_config(page_title="SQL Query Playground")

st.title("SQL Query Playground")

# uploaded_file_manager = UploadedFileManager()

with st.expander("Settings"):
    default_table_name = st.text_input(
        "Default Table Name (do not use SQL keyword as table name)", "tbl"
    )
    show_information = st.checkbox(
        "Show additional information (e.g. time usage, total rows, columns)", True
    )
    # show_plot_button = st.checkbox("Show plot button", True)
    # use_implicit_from = st.checkbox(
    #     "Able to write statement without FROM latest dataframe (otherwise from file)",
    #     True,
    # )
    st.text("Chat initial settings (take effect when uploading new file):")
    auto_initial_table = st.checkbox("Print table preview when file is uploaded", True)
    auto_initial_table_schema = st.checkbox(
        "Print table schema when file is uploaded", False
    )
    auto_initial_table_status = st.checkbox(
        "Print table statistics (use SUMMARIZE) when file is uploaded", True
    )
    auto_initial_table_status2 = st.checkbox(
        "Print table statistics (use Pandas) when file is uploaded", False
    )
    auto_initial_memory_status = st.checkbox(
        "Show memory consumption of the DataFrame", False
    )
    auto_from_table = st.checkbox(
        "Auto add FROM table clause if not found. (Recommend enable to save lots of typing. Disable this if you want to do some debug like `SELECT md5('123')`). Or you can add `;` at the end to temporary disable this.",
        True,
    )
    show_and_save_actual_prompt = st.checkbox(
        "Show and save actual prompt (automatically modified). Good for debugging.",
        True,
    )
    # try_drop_table_before_creating = st.checkbox(
    #     "Always try drop table if going to create new one.",
    #     True,
    # )
    keep_latest_statement_as_last_table = st.checkbox(
        f"Keep latest statement as last table (called table {TEMP_TABLE_NAME}) (Buggy, better not use)",
        False,
    )
    use_view_over_table = st.checkbox(
        f"Use VIEW over TABLE (Buggy, better not use)",
        False,
    )
    row_limit = st.number_input("Maximum rows to show (`<= 0` means no limit)", value=0)

with st.expander("Hints and Syntax"):
    st.markdown(
        f"""
Use `"column_name"` for column name and `'string'` for string literal.

You can [casting](https://duckdb.org/docs/sql/expressions/cast) Timestamp to Time by `timestamp_column::TIME`

- DuckDB SQL Syntax: [SQL Introduction - DuckDB](https://duckdb.org/docs/sql/introduction)
- DuckDB Data Types: [Data Types - DuckDB](https://duckdb.org/docs/sql/data_types/overview)
- DuckDB Functions: [Functions - DuckDB](https://duckdb.org/docs/sql/functions/overview)
- DuckDB Meta Queries: (**bold** is recommend)
  - [`DESCRIBE {default_table_name};`](https://duckdb.org/docs/guides/meta/describe): Describe Table (show column names and types)
  - [`SHOW TABLES;` **`SHOW ALL TABLES;`**](https://duckdb.org/docs/guides/meta/list_tables): List Tables
  - [`EXPLAIN ...;` **`SET explain_output = 'all'; EXPLAIN ...`**](https://duckdb.org/docs/guides/meta/explain): Inspect Query Plan
  - [**`EXPLAIN ANALYZE ...;`**](https://duckdb.org/docs/guides/meta/explain_analyze): Profile Queries
  - [`SUMMARIZE {default_table_name};` `SUMMARIZE SELECT ...;`](https://duckdb.org/docs/guides/meta/summarize): **Summarize (show value statistics)**
  - [DuckDB Environment](https://duckdb.org/docs/guides/meta/duckdb_environment)
    - `SELECT version();`
    - `PRAGMA version;`
    - `FROM duckdb_columns()`: columns
    - `FROM duckdb_constraints()`: constraints
    - `FROM duckdb_databases()`: lists the databases that are accessible from within the current DuckDB process
    - `FROM duckdb_dependencies()`: dependencies between objects
    - [`FROM duckdb_extensions()`](https://duckdb.org/docs/extensions/overview#listing-extensions): extensions
    - `FROM duckdb_functions()`: functions
    - `FROM duckdb_indexes()`: secondary indexes
    - `FROM duckdb_keywords()`: DuckDB’s keywords and reserved words
    - `FROM duckdb_optimizers()`: the available optimization rules in the DuckDB instance
    - `FROM duckdb_schemas()`: schemas
    - `FROM duckdb_sequences()`: sequences
    - `FROM duckdb_settings()`: settings
    - `FROM duckdb_tables()`: base tables
    - `FROM duckdb_types()`: data types
    - `FROM duckdb_views()`: views
    - `FROM duckdb_temporary_files()`: the temporary files DuckDB has written to disk, to offload data from memory
"""
    )

with st.expander("Usage"):
    st.markdown(
        f"""
        - Table name alias is `{default_table_name}`. Do things like [`SELECT * FROM {default_table_name};`](https://duckdb.org/docs/archive/0.8.1/sql/statements/select).
        - Note that, the `FROM {default_table_name}` can be omitted now. You can `SELECT *` which implies the use of table `{default_table_name}`.
        - Do not use preserve keyword like "table" for the table name.
        - You can just type in table name, this will be equivalent to preview the table (i.e. `SELECT * FROM table;`).
        - Add `;` at the end to disable all autofill stuff like auto add FROM etc.
        - Now support DuckDB statement (meta queries) like `SHOW TABLES;`, `DESCRIBE {default_table_name};`, etc.
        - You can create new table using [`CREATE TABLE new_table_name AS ...`](https://duckdb.org/docs/sql/statements/create_table.html). Also, I created an alias: `new_table_name = ...`
        - Remove table using [`DROP TABLE table_name`](https://duckdb.org/docs/sql/statements/drop.html)
        - Use _create table alias_ will automatically override same name table. This is equivalent to [`CREATE OR REPLACE TABLE...`](https://duckdb.org/docs/archive/0.8.1/sql/statements/create_table.html#create-or-replace)
        - You can create view using [`CREATE OR REPLACE VIEW new_view_name AS ...`](https://duckdb.org/docs/sql/statements/create_view.html). Drop it is similar to table [`DROP VIEW IF EXISTS view_name`](https://duckdb.org/docs/sql/statements/drop.html)
        - Note that, text with single quote means `'string'`. With double quote means `"column_name"`.
        """
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.data = None
    st.session_state.duckdb_connect = duckdb.connect(
        config={"allow_unsigned_extensions": "true"}
    )
    st.session_state.duckdb_connect.install_extension("httpfs")
    st.session_state.duckdb_connect.load_extension("httpfs")
    # st.session_state.duckdb_connect.execute("SET custom_extension_repository='http://welsch.lu/duckdb/prql/latest';")
    # BUG: duckdb.IOException: IO Error: Failed to download extension "prql" at URL "http://welsch.lu/duckdb/prql/latest/v0.8.1/windows_amd64/prql.duckdb_extension.gz Candidate extensions: "parquet", "sqlite", "sqlite3", "sqlite_scanner" (ERROR Read)
    # st.session_state.duckdb_connect.execute("FORCE INSTALL prql;")
    # st.session_state.duckdb_connect.execute("LOAD prql;")
    st.session_state.latest_table = None
    st.session_state.current_active_tables = set()


duckdb_connect = st.session_state.duckdb_connect.cursor()
# duckdb_connect.load_extension("httpfs")
# duckdb_connect.execute("LOAD prql;")

# TODO: Support multiple file
# If upload multiple file, they must have same extension and schema.
# TODO: Add option that if CSV doesn't have header
uploaded_file = st.file_uploader(
    "Data you want to query (support CSV, Parquet, Excel, and Json).",
    accept_multiple_files=False,
)

if uploaded_file is None:
    st.session_state.messages = []
    st.session_state.latest_table = None
    st.session_state.current_active_tables = set()
else:
    if st.session_state.uploaded_file != uploaded_file:
        st.session_state.messages = []
        st.session_state.uploaded_file = uploaded_file
        st.session_state.latest_table = default_table_name
        st.session_state.current_active_tables = {default_table_name}

        if uploaded_file.name.endswith(".csv"):
            # st.session_state.data = duckdb.read_csv(uploaded_file)
            try:
                st.session_state.data = duckdb.read_csv(
                    uploaded_file, connection=duckdb_connect
                )
            except duckdb.InvalidInputException:
                # BUG
                # duckdb.InvalidInputException: Invalid Input Error: Error in file "DUCKDB_INTERNAL_OBJECTSTORE://4b3e93e58df2b90e" at line 1 in column "0": Invalid unicode (byte sequence mismatch) detected in CSV file. Parser options:
                # file=DUCKDB_INTERNAL_OBJECTSTORE://4b3e93e58df2b90e
                # delimiter=',' (auto detected)
                # quote='"' (auto detected)
                # escape='' (auto detected)
                # header=0 (auto detected)
                # sample_size=20480
                # ignore_errors=0
                # all_varchar=0
                st.session_state.data = duckdb.read_csv(
                    uploaded_file, connection=duckdb_connect, encoding="gbk"
                )
            except UnicodeDecodeError:
                st.session_state.data = duckdb.read_csv(
                    uploaded_file, connection=duckdb_connect, encoding="gbk"
                )
        elif uploaded_file.name.endswith(".parquet"):
            # # TODO: making a LRU file manager for this
            # # with open(uploaded_file.name, "wb") as destination_file:
            # #     shutil.copyfileobj(uploaded_file, destination_file)
            # # https://docs.python.org/3/library/tempfile.html#tempfile.NamedTemporaryFile
            # # with tempfile.NamedTemporaryFile(suffix=".parquet") as fp:
            # #     fp.write(uploaded_file.getbuffer())
            # # NOTE: duckdb won't read file directly, so we should remove them later
            # # st.session_state.data = duckdb.read_parquet(uploaded_file.name)
            # st.session_state.data = duckdb.from_df(pd.read_parquet(uploaded_file))
            # # shutil.rmtree(uploaded_file.name)
            # # os.remove(uploaded_file.name)
            st.session_state.data = duckdb.from_df(
                pd.read_parquet(uploaded_file),
                connection=duckdb_connect,
            )
        elif uploaded_file.name.endswith(".json"):
            # TODO: haven't tested yet
            # st.session_state.data = duckdb.read_json(uploaded_file)
            st.session_state.data = duckdb.read_json(
                uploaded_file, connection=duckdb_connect
            )
        elif uploaded_file.name.endswith(".xlsx") or uploaded_file.name.endswith(
            ".xls"
        ):
            # https://duckdb.org/docs/guides/python/relational_api_pandas.html
            st.session_state.data = st.session_state.duckdb_connect.from_df(
                pd.read_excel(uploaded_file)
            )
        else:
            st.error("Invalid file extension.")
            st.stop()
            # st.session_state.data = None

        if auto_initial_table:
            # NOTE: currently force preview top 10 rows
            st.session_state.messages.extend(
                (
                    {
                        "role": "initial",
                        "content": f"Preview top 10 rows of file `{st.session_state.uploaded_file.name}` (as table alias `{default_table_name}`)",
                    },
                    {
                        "role": "assistant",
                        # "content": st.session_state.data.df()
                        # if row_limit <= 0
                        # else st.session_state.data.df().head(row_limit),
                        "content": st.session_state.data.df().head(10),
                    },
                )
            )

        if auto_initial_table_schema:
            # TODO: (Adhoc) we shouldn't register table twice
            duckdb_connect.register(default_table_name, st.session_state.data)
            st.session_state.messages.extend(
                (
                    {
                        "role": "initial",
                        "content": f"Schema of table `{default_table_name}`",
                    },
                    {
                        "role": "assistant",
                        "content": duckdb_connect.execute(
                            f"DESCRIBE {default_table_name};"
                        ).df(),
                    },
                )
            )

        if auto_initial_table_status:
            # TODO: (Adhoc) we shouldn't register table twice
            duckdb_connect.register(default_table_name, st.session_state.data)
            st.session_state.messages.extend(
                (
                    {
                        "role": "initial",
                        "content": f"Summary of table `{default_table_name}`",
                    },
                    {
                        "role": "assistant",
                        "content": duckdb_connect.execute(
                            f"SUMMARIZE {default_table_name};"
                        ).df(),
                    },
                )
            )
        if auto_initial_table_status2:
            st.session_state.messages.extend(
                (
                    {
                        "role": "initial",
                        "content": f"Statistic summary of table `{default_table_name}`",
                    },
                    {
                        "role": "assistant",
                        "content": st.session_state.data.df().describe(),
                    },
                )
            )

        if auto_initial_memory_status:
            st.session_state.messages.extend(
                (
                    {
                        "role": "initial",
                        "content": f"Memory consumption of `{default_table_name} DataFrame`",
                    },
                    {
                        "role": "initial",
                        "content": f"{st.session_state.data.df().memory_usage(index=False).sum()} bytes.",
                    },
                )
            )

# Create alias for duckdb
# CatalogException: Catalog Error: Failed to create view 'tbl': Existing object tbl is of type Table, trying to replace with type View
# tbl = st.session_state.data
if st.session_state.data is not None:
    try:
        # This will create VIEW instead of TABLE
        duckdb_connect.register(default_table_name, st.session_state.data)
        if keep_latest_statement_as_last_table:
            duckdb_connect.register(TEMP_TABLE_NAME, st.session_state.data)
            st.session_state.current_active_tables.add(TEMP_TABLE_NAME)
    except duckdb.CatalogException as e:
        print(e)

query_rewriter = QueryRewriterForDuckDB(use_view_over_table=use_view_over_table, auto_from_table=auto_from_table)
query_rewriter.current_active_tables = st.session_state.current_active_tables

# duckdb.alias
# Not working
# https://stackoverflow.com/questions/5036700/how-can-you-dynamically-create-variables
# exec(f"{default_table_name} = st.session_state.data")

# Rendering history message
for i, message in enumerate(st.session_state.messages):
    if message["role"] in {"user", "assistant"}:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.code(message["content"][0], language="sql")
                if (
                    show_and_save_actual_prompt
                    and message["content"][0] != message["content"][1]
                ):
                    st.text("modified:")
                    st.code(message["content"][1], language="sql")
            elif message["role"] == "assistant":
                if isinstance(message["content"], pd.DataFrame):
                    if not message.get("time_usage", "is_initial_dfs") is None:
                        st.dataframe(message["content"])
                        if show_information and message.get("time_usage"):
                            row, col = message["content"].shape
                            st.caption(
                                f"Time usage: {message['time_usage']:.2f} seconds; Total rows {row}; Total columns {col}."
                            )
                    else:
                        # For EXPLAIN
                        lines = []
                        for i, row in message["content"].iterrows():
                            lines.append(row["explain_key"])
                            lines.append(row["explain_value"])
                        st.text("\n".join(lines))
                else:
                    # For EXPLAIN (legacy)
                    if message.get("time_usage", "is_initial_dfs") is None:
                        st.text(message["content"])

                    else:
                        st.error(message["content"])
                        if show_information:
                            st.caption(
                                f"Time usage: {message['time_usage']:.2f} seconds."
                            )
    else:
        with st.chat_message(name="assistant"):
            if message["role"] == "initial":
                st.markdown(message["content"])

if prompt := st.chat_input(
    "Please input SQL query.", disabled=st.session_state.data is None
):
    with st.chat_message("user"):
        user_message_placeholder = st.empty()
        if show_and_save_actual_prompt:
            modified_placeholder = st.empty()
            modified_user_message_placeholder = st.empty()

    old_prompt = prompt = prompt.strip()

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        if not prompt.endswith(";"):
            prompt = query_rewriter.rewrite(prompt, st.session_state.latest_table_name)

        new_table_name = query_rewriter.creating_table(prompt)

        st.session_state.messages.append(
            {"role": "user", "content": (old_prompt, prompt), "time_usage": None}
        )
        user_message_placeholder.code(old_prompt, language="sql")
        if show_and_save_actual_prompt and old_prompt != prompt:
            modified_placeholder.text("modified:")
            modified_user_message_placeholder.code(prompt, language="sql")

        with st.spinner():
            start = time.perf_counter()
            # https://www.geeksforgeeks.org/try-except-else-and-finally-in-python/
            try:
                result = duckdb.execute(prompt, connection=duckdb_connect)
            except Exception as e:
                # except duckdb.CatalogException as e:

                # CatalogException

                error = e
                result_df = None
                # if new_table_name:
                #     # Create new table failed, we need to remove table
                #     # Catalog Error: Table with name "tbl2" already exists!
                #     duckdb.execute(f"DROP TABLE {new_table_name};")

                # Binder Error: * expression without FROM clause!
                # TODO
            else:
                # Success

                error = None
                result_df = result.df()
                if new_table_name:
                    # Successfully created new table
                    st.session_state.current_active_tables.add(new_table_name)
                    st.session_state.latest_table = new_table_name
            finally:
                time_usage = time.perf_counter() - start
                if result_df is not None:
                    # TODO: improve this to prevent column contains EXPLAIN etc.
                    # if prompt.upper().startswith("EXPLAIN") and :
                    if "EXPLAIN" in prompt.upper():
                        # https://duckdb.org/docs/guides/meta/explain
                        lines = []
                        for i, row in result_df.iterrows():
                            lines.append(row["explain_key"])
                            lines.append(row["explain_value"])
                        message_placeholder.text("\n".join(lines))
                        time_usage = None  # NOTE: (Adhoc) we use time_usage = None to indicate it is a EXPLAIN dataframe
                    else:
                        message_placeholder.dataframe(result_df)
                        if show_information:
                            row, col = result_df.shape
                            st.caption(
                                f"Time usage: {time_usage:.2f} seconds; Total rows {row}; Total columns {col}."
                            )
                else:
                    message_placeholder.error(error)
                    if show_information:
                        st.caption(f"Time usage: {time_usage:.2f} seconds.")

    # Update history
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result_df if result_df is not None else error,
            "time_usage": time_usage,
        }
    )

with st.sidebar:
    messages = []
    # TODO: show memory usage..?
    messages.append("Current active tables:")
    for table in st.session_state.current_active_tables:
        messages.append(f"- {table}")
    messages.append(f"\nLatest used table: `{st.session_state.latest_table}`")
    if st.session_state.latest_table:
        messages.append("\nPreview:")
    st.markdown("\n".join(messages))
    if st.session_state.latest_table:
        temp_df = duckdb.sql(
            f"SELECT * FROM {st.session_state.latest_table};",
            connection=duckdb_connect,
        ).df()
        st.dataframe(temp_df.head(5))
        row, col = temp_df.shape
        st.markdown(f"Total rows {row}; Total columns {col}")
        st.markdown("Available columns:\n")
        st.write(temp_df.columns)

# https://pandas.pydata.org/docs/user_guide/visualization.html
# TODO: support simple plot options for each dataframe
#     if show_plot_button:
#         st.session_state.latest_result_df = result_df
#
#
# def plot_dataframe(df: pd.DataFrame, pandas_df_plot_kwargs: dict):
#     try:
#         st.session_state.figure = df.plot(**pandas_df_plot_kwargs).figure
#     except Exception as e:
#         st.error(e)
#         st.session_state.figure = None
#
#
# if show_plot_button and "latest_result_df" in st.session_state:
#     image_placeholder = st.empty()
#
#     pandas_df_plot_kwargs = eval(
#         st.text_area(
#             "Plot arguments (argument in json format [pandas.DataFrame.plot](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.plot.html))",
#             value='{"x": None, "y": "your_column", "use_index": True, "kind": "bar", "title": "plot"}',
#         )
#     )
#
#     click = st.button(
#         "Plot",
#         on_click=partial(
#             plot_dataframe, st.session_state.latest_result_df, pandas_df_plot_kwargs
#         ),
#         key=len(st.session_state.messages),
#     )
#
#     if click and "figure" in st.session_state and st.session_state.figure is not None:
#         image_placeholder.pyplot(st.session_state.figure)
