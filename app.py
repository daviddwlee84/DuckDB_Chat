import streamlit as st
import duckdb

st.set_page_config(page_title="DuckDB Chat Demo")

st.title("DuckDB Chat")

with st.expander("Settings"):
    default_table_name = st.text_input("Default Table Name", "tbl")
    st.text("Chat initial settings (take effect when uploading new file):")
    auto_initial_table = st.checkbox("Print table when file is uploaded", False)
    auto_initial_table_status = st.checkbox(
        "Print table statistics when file is uploaded", False
    )
    auto_initial_memory_status = st.checkbox(
        "Show memory consumption of the DataFrame", False
    )
    row_limit = st.number_input("Maximum rows to show (`<= 0` means no limit)", value=0)

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

if uploaded_file is None:
    st.session_state.messages = []
else:
    if st.session_state.uploaded_file != uploaded_file:
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

        if auto_initial_table:
            st.session_state.messages.extend(
                (
                    {
                        "role": "initial",
                        "content": f"DataFrame of file `{st.session_state.uploaded_file.name}` (as table alias `{default_table_name}`)",
                    },
                    {
                        "role": "assistant",
                        "content": st.session_state.data.df()
                        if row_limit <= 0
                        else st.session_state.data.df().head(row_limit),
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
tbl = st.session_state.data
# duckdb.alias
# Not working
# https://stackoverflow.com/questions/5036700/how-can-you-dynamically-create-variables
# exec(f"{default_table_name} = st.session_state.data")

# Rendering history message
for message in st.session_state.messages:
    if message["role"] in {"user", "assistant"}:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.code(message["content"], language="sql")
            elif message["role"] == "assistant":
                st.dataframe(message["content"])
    else:
        with st.chat_message(name="assistant"):
            if message["role"] == "initial":
                st.markdown(message["content"])

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
            result_df = duckdb.sql(prompt).df()
            # if row_limit > 0:
            #     result_df = duckdb.sql(prompt).df().head(row_limit)
            # else:
            #     result_df = duckdb.sql(prompt).df()

        message_placeholder.dataframe(result_df)
    st.session_state.messages.append({"role": "assistant", "content": result_df})
