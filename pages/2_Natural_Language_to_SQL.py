import streamlit as st
from dotenv import load_dotenv
import os

curr_dir = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(curr_dir, "../.env"))

st.set_page_config(
    page_title="Natural Language to SQL",
)

st.title("Natural Language to SQL")

with st.sidebar:
    openai_selection = st.selectbox("OpenAI Version", ["OpenAI", "Azure OpenAI"])

    # TODO: this should be a global settings
    if openai_selection == "OpenAI":
        openai_api_key = st.text_input(
            "OpenAI API Key",
            key="openai_api_key",
            value=os.getenv("OPENAI_API_KEY"),
            type="password",
        )
    elif openai_selection == "Azure OpenAI":
        azure_openai_api_key = st.text_input(
            "Azure OpenAI API Key",
            key="azure_openai_api_key",
            value=os.getenv("AZURE_OPENAI_KEY"),
            type="password",
        )
        azure_openai_endpoint = st.text_input(
            "Azure OpenAI Endpoint",
            key="azure_openai_endpoint",
            value=os.getenv("AZURE_OPENAI_ENDPOINT"),
            type="default",
        )
        azure_openai_deployment_name = st.text_input(
            "Azure OpenAI Deployment Name",
            key="azure_openai_deployment_name",
            value=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            type="default",
        )
        azure_openai_version = st.text_input(
            "Azure OpenAI Version",
            key="azure_openai_version",
            value=os.getenv("AZURE_OPENAI_VERSION"),
            type="default",
        )
