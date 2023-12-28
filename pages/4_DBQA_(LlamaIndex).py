from typing import Literal
import streamlit as st
from llama_index import LLMPredictor, ServiceContext, SQLDatabase, VectorStoreIndex
from llama_index.objects import SQLTableNodeMapping, ObjectIndex, SQLTableSchema
from llama_index.indices.struct_store import (
    NLSQLTableQueryEngine,
    SQLTableRetrieverQueryEngine,
)

# https://docs.llamaindex.ai/en/stable/examples/customization/llms/AzureOpenAI.html
from llama_index.llms import AzureOpenAI, OpenAI
import pandas as pd
from sqlalchemy import create_engine, MetaData
import sqlite3
from dotenv import load_dotenv
import os

# import tiktoken
# from llama_index.callbacks import CallbackManager, TokenCountingHandler
# import logging
# import sys
# logging.basicConfig(
#     stream=sys.stdout, level=logging.INFO
# )  # logging.DEBUG for more verbose output
# logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

curr_dir = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(curr_dir, "../.env"))

st.set_page_config(page_title="Database Question Answering (using LlamaIndex)")

st.title("Database Question Answering (using LlamaIndex)")

table_name = st.text_input(
    "Table Name (better be meaningful and related to the file you uploaded)",
    value="tbl",
)
additional_prompt_guide = st.text_area(
    "Additional Prompt Guide that follows at the end of user prompt",
    value=" (You should double quote the column name)",
)

# TODO: haven't implement SQLTableRetrieverQueryEngine
llamaindex_query_engine: Literal[
    "NLSQLTableQueryEngine", "SQLTableRetrieverQueryEngine"
] = st.selectbox(
    "LlamaIndex Query Engine", ["NLSQLTableQueryEngine", "SQLTableRetrieverQueryEngine"]
)

# sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread. The object was created in thread id 47584 and this is thread id 15496.
if "dbqa_llamaindex_uploaded_file" not in st.session_state:
    st.session_state.dbqa_llamaindex_uploaded_file = None
    st.session_state.dbqa_llamaindex_db_engine = create_engine("sqlite:///:memory:")
    st.session_state.dbqa_llamaindex_data = None

sqlite_connect = sqlite3.connect(":memory:")

uploaded_file = st.file_uploader(
    "Data you want to query (support CSV, Parquet, and Json).",
    accept_multiple_files=False,
)

if uploaded_file is None:
    st.session_state.dbqa_llamaindex_messages = []
else:
    if st.session_state.dbqa_llamaindex_uploaded_file != uploaded_file:
        st.session_state.dbqa_llamaindex_messages = []
        st.session_state.dbqa_llamaindex_uploaded_file = uploaded_file

        if uploaded_file.name.endswith(".csv"):
            st.session_state.dbqa_llamaindex_data = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".parquet"):
            st.session_state.dbqa_llamaindex_data = pd.read_parquet(uploaded_file)
        else:
            st.error("Please provide valid file type.")
            st.stop()

    st.session_state.dbqa_llamaindex_data.to_sql(
        table_name, st.session_state.dbqa_llamaindex_db_engine
    )

# TODO: maybe put these initialization into st.session_state..?
sql_database = SQLDatabase(st.session_state.dbqa_llamaindex_db_engine)

if llamaindex_query_engine == "SQLTableRetrieverQueryEngine":
    metadata_obj = MetaData()
    metadata_obj.reflect(st.session_state.dbqa_llamaindex_db_engine)
    table_node_mapping = SQLTableNodeMapping(sql_database)
    table_schema_objs = []
    for name in metadata_obj.tables.keys():
        table_schema = SQLTableSchema(table_name=name)
        table_schema_objs.append(table_schema)
        st.write(table_schema)

with st.sidebar:
    openai_selection: Literal["OpenAI", "Azure OpenAI"] = st.selectbox(
        "OpenAI Version", ["OpenAI", "Azure OpenAI"]
    )

    # TODO: this should be a global settings
    if openai_selection == "OpenAI":
        st.session_state.openai_api_key = st.text_input(
            "OpenAI API Key",
            # key="openai_api_key_input_text",
            value=st.session_state.get("openai_api_key", os.getenv("OPENAI_API_KEY")),
            type="password",
        )

    elif openai_selection == "Azure OpenAI":
        st.session_state.azure_openai_api_key = st.text_input(
            "Azure OpenAI API Key",
            # key="azure_openai_api_key_input_text",
            value=st.session_state.get(
                "azure_openai_api_key", os.getenv("AZURE_OPENAI_KEY")
            ),
            type="password",
        )
        st.session_state.azure_openai_endpoint = st.text_input(
            "Azure OpenAI Endpoint",
            # key="azure_openai_endpoint_input_text",
            value=st.session_state.get(
                "azure_openai_endpoint", os.getenv("AZURE_OPENAI_ENDPOINT")
            ),
            type="default",
        )
        st.session_state.azure_openai_deployment_name = st.text_input(
            "Azure OpenAI Deployment Name",
            # key="azure_openai_deployment_name_input_text",
            value=st.session_state.get(
                "azure_openai_deployment_name",
                os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            ),
            type="default",
        )
        st.session_state.azure_openai_version = st.text_input(
            "Azure OpenAI Version",
            # key="azure_openai_version_input_text",
            value=st.session_state.get(
                "azure_openai_version", os.getenv("AZURE_OPENAI_VERSION")
            ),
            type="default",
        )


if "dbqa_llamaindex_messages" not in st.session_state:
    st.session_state["dbqa_llamaindex_messages"] = []

for msg in st.session_state.dbqa_llamaindex_messages:
    # https://discuss.streamlit.io/t/disable-latex/44995/10
    # https://discuss.streamlit.io/t/how-to-stop-attempted-k-latex-rendering-of-1-million-or-100-000/41473
    st.chat_message(msg["role"]).write(msg["content"])

# https://streamlit.io/generative-ai
# TODO: make response streaming https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps#build-a-simple-chatbot-gui-with-streaming
if prompt := st.chat_input():
    if openai_selection == "OpenAI":
        if not st.session_state.openai_api_key:
            st.warning("🥸 Please add your OpenAI API key to continue.")
            st.stop()

        llm = OpenAI(
            model="gpt-35-turbo",
            api_key=st.session_state.openai_api_key,
        )

    elif openai_selection == "Azure OpenAI":
        if not st.session_state.azure_openai_api_key:
            st.warning("🥸 Please add your Azure OpenAI API key to continue.")
            st.stop()

        llm = AzureOpenAI(
            model="gpt-35-turbo",
            deployment_name=st.session_state.azure_openai_deployment_name,
            api_key=st.session_state.azure_openai_api_key,
            azure_endpoint=st.session_state.azure_openai_endpoint,
            api_version=st.session_state.azure_openai_version,
        )

    # token_counter = TokenCountingHandler(
    #     tokenizer=tiktoken.encoding_for_model("gpt-3.5-turbo").encode
    # )
    # callback_manager = CallbackManager([token_counter])
    # BUG: AttributeError: 'CompletionUsage' object has no attribute 'get'
    service_context = ServiceContext.from_defaults(
        llm=llm,
        embed_model=None,  # callback_manager=callback_manager  # TODO
    )
    # llm_predictor = LLMPredictor(llm=llm)
    # service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)

    if llamaindex_query_engine == "SQLTableRetrieverQueryEngine":
        # We dump the table schema information into a vector index. The vector index is stored within the context builder for future use.
        obj_index = ObjectIndex.from_objects(
            table_schema_objs,
            table_node_mapping,
            VectorStoreIndex,
            service_context=service_context,
        )

        # We construct a SQLTableRetrieverQueryEngine.
        # Note that we pass in the ObjectRetriever so that we can dynamically retrieve the table during query-time.
        # ObjectRetriever: A retriever that retrieves a set of query engine tools.
        query_engine = SQLTableRetrieverQueryEngine(
            sql_database,
            obj_index.as_retriever(similarity_top_k=1),
            service_context=service_context,
        )
    elif llamaindex_query_engine == "NLSQLTableQueryEngine":
        query_engine = NLSQLTableQueryEngine(
            sql_database,
            service_context=service_context,
        )

    st.session_state.dbqa_llamaindex_messages.append(
        {"role": "user", "content": prompt}
    )
    st.chat_message("user").write(prompt)
    response = query_engine.query(prompt + additional_prompt_guide)

    # token_count = {
    #     "Embedding Tokens": token_counter.total_embedding_token_count,
    #     "LLM Prompt Tokens": token_counter.prompt_llm_token_count,
    #     "LLM Completion Tokens": token_counter.completion_llm_token_count,
    #     "Total LLM Token Count": token_counter.total_llm_token_count,
    # }
    # # reset counts
    # token_counter.reset_counts()

    # TODO: able to filter metadata and for detail result
    assistant_content = f"**{response.response}**\n```sql\n{response.metadata.get('sql_query')}\n```\n- result: {response.metadata.get('result')}\n- column keys: {response.metadata.get('col_keys')}"  # \n- token count: {token_count}"
    assistant_content = assistant_content.replace("$", "\\$")
    st.session_state.dbqa_llamaindex_messages.append(
        {"role": "assistant", "content": assistant_content}
    )
    st.chat_message("assistant").write(assistant_content)
