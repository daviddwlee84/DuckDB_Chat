import streamlit as st
import duckdb

st.set_page_config(page_title="DuckDB Chat Demo")

st.title("DuckDB Chat")
# TODO: customized table name
st.markdown("Table name alias is `tbl`. Do things like `SELECT * FROM tbl;`")

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
        # result_df = st.session_state.data.sql(prompt).df()
        result_df = duckdb.sql(prompt).df()
        message_placeholder.dataframe(result_df)
    st.session_state.messages.append({"role": "assistant", "content": result_df})
