import streamlit as st
import duckdb
import time
import pandas as pd

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
        "Print table schema when file is uploaded", True
    )
    auto_initial_table_status = st.checkbox(
        "Print table statistics when file is uploaded", False
    )
    auto_initial_memory_status = st.checkbox(
        "Show memory consumption of the DataFrame", False
    )
    row_limit = st.number_input("Maximum rows to show (`<= 0` means no limit)", value=0)

with st.expander("Hints and Syntax"):
    st.markdown(
        """
Use `"column_name"` for column name and `'string'` for string literal.

You can [casting](https://duckdb.org/docs/sql/expressions/cast) Timestamp to Time by `timestamp_column::TIME`

- DuckDB SQL Syntax: [SQL Introduction - DuckDB](https://duckdb.org/docs/sql/introduction)
- DuckDB Data Types: [Data Types - DuckDB](https://duckdb.org/docs/sql/data_types/overview)
- DuckDB Functions: [Functions - DuckDB](https://duckdb.org/docs/sql/functions/overview)
"""
    )

# TODO: customized table name
st.markdown(
    f"""
    - Table name alias is `{default_table_name}`. Do things like `SELECT * FROM {default_table_name};`.
    - Note that, the `FROM {default_table_name}` can be omitted now. You can `SELECT *` which implies the use of table `{default_table_name}`.
    - Do not use preserve keyword like "table" for the table name.
    - Now support DuckDB statement like `SHOW TABLES;`, `DESCRIBE {default_table_name};`, etc.
    """
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.data = None
    st.session_state.duckdb_connect = duckdb.connect()

duckdb_connect = st.session_state.duckdb_connect.cursor()

# TODO: Support multiple file
# If upload multiple file, they must have same extension and schema.
# TODO: Add option that if CSV doesn't have header
uploaded_file = st.file_uploader(
    "Data you want to query (support CSV, Parquet, Excel, and Json).",
    accept_multiple_files=False,
)

if uploaded_file is None:
    st.session_state.messages = []
else:
    if st.session_state.uploaded_file != uploaded_file:
        st.session_state.messages = []
        st.session_state.uploaded_file = uploaded_file

        if uploaded_file.name.endswith(".csv"):
            # st.session_state.data = duckdb.read_csv(uploaded_file)
            st.session_state.data = duckdb.read_csv(
                uploaded_file, connection=duckdb_connect
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

        # BUG: we shouldn't register table twice
        if auto_initial_table_schema:
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
        duckdb_connect.register(default_table_name, st.session_state.data)
    except duckdb.CatalogException as e:
        print(e)

# duckdb.alias
# Not working
# https://stackoverflow.com/questions/5036700/how-can-you-dynamically-create-variables
# exec(f"{default_table_name} = st.session_state.data")

# Rendering history message
for i, message in enumerate(st.session_state.messages):
    if message["role"] in {"user", "assistant"}:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.code(message["content"], language="sql")
            elif message["role"] == "assistant":
                st.dataframe(message["content"])
                if show_information and message.get("time_usage"):
                    row, col = message["content"].shape
                    st.caption(
                        f"Time usage: {message['time_usage']:.2f} seconds; Total rows {row}; Total columns {col}."
                    )
    else:
        with st.chat_message(name="assistant"):
            if message["role"] == "initial":
                st.markdown(message["content"])

if prompt := st.chat_input(
    "Please input SQL query.", disabled=st.session_state.data is None
):
    st.session_state.messages.append(
        {"role": "user", "content": prompt, "time_usage": None}
    )
    with st.chat_message("user"):
        st.code(prompt, language="sql")

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        # if "FROM" in prompt:
        #     pass
        #     # if default_table_name != "tbl":
        #     #     # TODO: make this regular expression
        #     #     # TODO: this should also support lower-case from
        #     #     prompt = prompt.replace(f"FROM {default_table_name}", "FROM tbl")
        # else:
        #     #  using the FROM-first syntax
        #     # prompt = f"FROM tbl " + prompt
        #     prompt = f"FROM {default_table_name} " + prompt
        #     # if use_implicit_from and st.session_state.get('latest_result'):
        #     #     prompt = f'FROM latest_result ' + prompt
        #     # else:
        #     #     prompt = f"FROM {default_table_name} " + prompt

        if prompt.upper().startswith("SELECT") and "FROM" not in prompt.upper():
            prompt = f"FROM {default_table_name} " + prompt

        # TODO: not sure if this part make sense. Ideally, user should be aware of what they are doing.
        # (operation can cancel when it took too much time)
        if row_limit > 0:
            if prompt.endswith(";"):
                prompt = prompt.replace(";", f" LIMIT {row_limit};")
            elif "LIMIT" in prompt:
                st.toast("User has override row limit.")
            else:
                prompt += f" LIMIT {row_limit};"

        with st.spinner():
            start = time.perf_counter()
            result = duckdb.execute(prompt, connection=duckdb_connect)
            # result = duckdb.sql(prompt)
            time_usage = time.perf_counter() - start

        result_df = result.df()
        message_placeholder.dataframe(result_df)
        if show_information:
            row, col = result_df.shape
            st.caption(
                f"Time usage: {time_usage:.2f} seconds; Total rows {row}; Total columns {col}."
            )

    # Update history
    st.session_state.messages.append(
        {"role": "assistant", "content": result_df, "time_usage": time_usage}
    )

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
