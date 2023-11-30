import streamlit as st

# from dotenv import load_dotenv
# import os
# load_dotenv()

st.set_page_config(
    page_title="DuckDB Chat Demo",
    page_icon="👋",
)

st.write("# DuckDB Chat - Chat with your DB files")

with st.sidebar:
    st.markdown(
        """
    ## Functionality Explanation

    - `SQL query`: You can try SQL query on your file

    ## LLM API Keys

    - [Get an OpenAI API key](https://platform.openai.com/account/api-keys)
    """
    )

    # st.session_state.openai_selection = st.selectbox(
    #     "OpenAI Version", ["OpenAI", "Azure OpenAI"]
    # )

    # st.text("OpenAI")
    # openai_api_key = st.text_input(
    #     "OpenAI API Key",
    #     key="openai_api_key",
    #     value=os.getenv("OPENAI_API_KEY"),
    #     type="password",
    # )
    # # BUG: streamlit.errors.StreamlitAPIException: `st.session_state.openai_api_key` cannot be modified after the widget with key `openai_api_key` is instantiated.
    # # https://stackoverflow.com/questions/74968179/session-state-is-reset-in-streamlit-multipage-app
    # st.session_state.openai_api_key = openai_api_key

    # st.text("Azure OpenAI")
    # azure_openai_api_key = st.text_input(
    #     "OpenAI API Key",
    #     key="azure_openai_api_key",
    #     value=os.getenv("AZURE_OPENAI_KEY"),
    #     type="password",
    # )
    # st.session_state.azure_openai_api_key = azure_openai_api_key
    # azure_openai_endpoint = st.text_input(
    #     "Azure OpenAI Endpoint",
    #     key="azure_openai_endpoint",
    #     value=os.getenv("AZURE_OPENAI_ENDPOINT"),
    #     type="password",
    # )
    # st.session_state.azure_openai_endpoint = azure_openai_endpoint
    # azure_openai_deployment_name = st.text_input(
    #     "Azure OpenAI Deployment Name",
    #     key="azure_openai_deployment_name",
    #     value=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    #     type="default",
    # )
    # st.session_state.azure_openai_deployment_name = azure_openai_deployment_name
    # azure_openai_version = st.text_input(
    #     "Azure OpenAI Version",
    #     key="azure_openai_version",
    #     value=os.getenv("AZURE_OPENAI_VERSION"),
    #     type="default",
    # )
    # st.session_state.azure_openai_version = azure_openai_version

st.markdown(
    """
    - Github Page: [daviddwlee84/DuckDB_Chat: Access file as a database with interactive SQL query experience. Built on Streamlit and DuckDB.](https://github.com/daviddwlee84/DuckDB_Chat)
    - Personal Website: [David Lee](https://dwlee-personal-website.netlify.app/)
"""
)
