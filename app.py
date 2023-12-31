import streamlit as st
from dotenv import load_dotenv
import os

curr_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(curr_dir, ".env"))

st.set_page_config(
    page_title="DuckDB Chat Demo",
    page_icon="👋",
)

st.write("# DuckDB Chat - Chat with your DB files")

with st.sidebar:
    st.markdown(
        """

    ## LLM API Keys

    > [Get an OpenAI API key](https://platform.openai.com/account/api-keys)
    >
    > Default key is loaded from `.env`.
    > You can fill keys here or later.
    """
    )

    st.text("OpenAI")
    st.session_state.openai_api_key = st.text_input(
        "OpenAI API Key",
        # session_state should not content key of other item (just rename them)
        # streamlit.errors.StreamlitAPIException: `st.session_state.openai_api_key` cannot be modified after the widget with key `openai_api_key` is instantiated.
        # https://stackoverflow.com/questions/74968179/session-state-is-reset-in-streamlit-multipage-app
        # key="openai_api_key_text_input",
        # https://github.com/streamlit/streamlit/issues/4458
        value=st.session_state.get("openai_api_key", os.getenv("OPENAI_API_KEY")),
        type="password",
    )

    st.divider()

    st.text("Azure OpenAI")
    st.session_state.azure_openai_api_key = st.text_input(
        "Azure OpenAI API Key",
        # key="azure_openai_api_key_text_input",
        value=st.session_state.get(
            "azure_openai_api_key", os.getenv("AZURE_OPENAI_KEY")
        ),
        type="password",
    )
    st.session_state.azure_openai_endpoint = st.text_input(
        "Azure OpenAI Endpoint",
        # key="azure_openai_endpoint_text_input",
        value=st.session_state.get(
            "azure_openai_endpoint", os.getenv("AZURE_OPENAI_ENDPOINT")
        ),
        type="default",
    )
    st.session_state.azure_openai_deployment_name = st.text_input(
        "Azure OpenAI Deployment Name",
        # key="azure_openai_deployment_name_text_input",
        value=st.session_state.get(
            "azure_openai_deployment_name",
            os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        ),
        type="default",
    )
    st.session_state.azure_openai_version = st.text_input(
        "Azure OpenAI Version",
        # key="azure_openai_version_text_input",
        value=st.session_state.get(
            "azure_openai_version", os.getenv("AZURE_OPENAI_VERSION")
        ),
        type="default",
    )

st.markdown(
    """
    ## Functionality Explanation

    1. `SQL query`: You can try SQL query on your file
    2. `Natural Language to SQL` (TBD): Currently, just a pure chat
    3. `DBQA` (TDB): Will based on `Natural Language to SQL` to do search
    4. `DBQA (LlamaIndex)`: Use LlamaIndex to do DBQA. It contains SQL generation and the QA part.
    5. `DBQA (PandasAI)`: Use PandasAI to do DBQA. Support answering (sentence, number), plotting, and show data.

    ---

    ## Links

    - Github Page: [daviddwlee84/DuckDB_Chat](https://github.com/daviddwlee84/DuckDB_Chat)
    - Personal Website: [David Lee](https://dwlee-personal-website.netlify.app/)

    NOTE: Currently, LangChain's SQLDatabase cannot integrate with DuckDB well.
    Currently, we will stick with the workaround => Pandas DataFrame => SQLite => SQLDatabase
"""
)
