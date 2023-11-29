import streamlit as st
import duckdb

st.set_page_config(page_title="DuckDB Chat Demo")

st.title("DuckDB Chat")

with st.expander("Settings"):
    default_table_name = st.text_input("Default Table Name", "tbl")

# TODO: customized table name
st.markdown(
    f"Table name alias is `{default_table_name}`. Do things like `SELECT * FROM {default_table_name};`"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
    st.session_state.data = None

# TODO: Support multiple file
# If upload multiple file, they must have same extension and schema.
# TODO: Add option that if CSV doesn't have header
uploaded_file = st.file_uploader(
    "Data you want to query (support CSV, Parquet, and Json).",
    accept_multiple_files=False,
)

if st.session_state.uploaded_file != uploaded_file and uploaded_file is not None:
    st.session_state.messages = []
    st.session_state.uploaded_file = uploaded_file

    if uploaded_file.name.endswith(".csv"):
        st.session_state.data = duckdb.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".parquet"):
        st.session_state.data = duckdb.read_parquet(uploaded_file)
    elif uploaded_file.name.endswith(".json"):
        st.session_state.data = duckdb.read_json(uploaded_file)
    else:
        st.session_state.data = None

# Create alias for duckdb
tbl = st.session_state.data
# duckdb.alias
# Not working
# https://stackoverflow.com/questions/5036700/how-can-you-dynamically-create-variables
# exec(f"{default_table_name} = st.session_state.data")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.code(message["content"], language="sql")
        elif message["role"] == "assistant":
            st.dataframe(message["content"])

if prompt := st.chat_input(
    "Please input SQL query.", disabled=st.session_state.data is None
):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.code(prompt, language="sql")

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        if default_table_name != "tbl":
            # TODO: make this regular expression
            prompt = prompt.replace(f"FROM {default_table_name}", "FROM tbl")

        with st.spinner():
            result_df = duckdb.sql(prompt).df()

        message_placeholder.dataframe(result_df)
    st.session_state.messages.append({"role": "assistant", "content": result_df})
