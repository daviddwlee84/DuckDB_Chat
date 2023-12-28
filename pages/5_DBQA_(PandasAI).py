from typing import Literal, Union
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
import pandas as pd
from pandasai import SmartDataframe, Agent, SmartDatalake
from pandasai.llm import OpenAI, AzureOpenAI

llm = OpenAI(api_token="YOUR_API_TOKEN")


curr_dir = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(curr_dir, "../.env"))

st.set_page_config(page_title="Database Question Answering (using PandasAI)")

st.title("Database Question Answering (using PandasAI)")

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

if openai_selection == "OpenAI":
    if not st.session_state.openai_api_key:
        st.warning("🥸 Please add your OpenAI API key to continue.")
        st.stop()

    llm = OpenAI(
        model="gpt-35-turbo",
        api_token=st.session_state.openai_api_key,
    )

elif openai_selection == "Azure OpenAI":
    if not st.session_state.azure_openai_api_key:
        st.warning("🥸 Please add your Azure OpenAI API key to continue.")
        st.stop()

    llm = AzureOpenAI(
        model="gpt-35-turbo",
        api_token=st.session_state.azure_openai_api_key,
        azure_endpoint=st.session_state.azure_openai_endpoint,
        api_version=st.session_state.azure_openai_version,
        deployment_name=st.session_state.azure_openai_deployment_name,
        is_chat_model=True,
    )

if "dbqa_pandasai_uploaded_file" not in st.session_state:
    st.session_state.dbqa_pandasai_uploaded_file = None
    st.session_state.dbqa_pandasai_data = None

chat_mode: Literal["Single Turn", "Multi Turn"] = st.selectbox(
    "Chat Mode", ["Single Turn", "Multi Turn"]
)

uploaded_file = st.file_uploader(
    "Data you want to query (support CSV, Parquet, and Json).",
    accept_multiple_files=False,
)

if uploaded_file is None:
    st.session_state.dbqa_pandasai_messages = []
    st.session_state.pandasai_df = None
else:
    config = {
        "llm": llm,
        "verbose": True,
        "save_charts": True,
        "save_charts_path": os.path.join(curr_dir, "../exports/charts/"),
        "open_charts": False,
        "enable_cache": True,
    }

    if st.session_state.dbqa_pandasai_uploaded_file != uploaded_file:
        st.session_state.dbqa_pandasai_messages = []
        st.session_state.dbqa_pandasai_uploaded_file = uploaded_file

        if uploaded_file.name.endswith(".csv"):
            st.session_state.dbqa_pandasai_data = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".parquet"):
            st.session_state.dbqa_pandasai_data = pd.read_parquet(uploaded_file)
        else:
            st.error("Please provide valid file type.")
            st.stop()

        st.session_state.chat_mode = chat_mode
        if chat_mode == "Single Turn":
            st.session_state.pandasai_df = SmartDatalake(
                [st.session_state.dbqa_pandasai_data], config=config
            )
        elif chat_mode == "Multi Turn":
            st.session_state.pandasai_df = Agent(
                [st.session_state.dbqa_pandasai_data], config=config
            )

    if st.session_state.chat_mode != chat_mode:
        st.session_state.dbqa_pandasai_messages = []
        if chat_mode == "Single Turn":
            st.session_state.pandasai_df = SmartDatalake(
                [st.session_state.dbqa_pandasai_data], config=config
            )
        elif chat_mode == "Multi Turn":
            st.session_state.pandasai_df = Agent(
                [st.session_state.dbqa_pandasai_data], config=config
            )


if "dbqa_pandasai_messages" not in st.session_state:
    st.session_state["dbqa_pandasai_messages"] = []


def render_message(
    message: Union[SmartDataframe, pd.DataFrame, str, int, float], placeholder=None
):
    if placeholder is None:
        placeholder = st

    if isinstance(message, SmartDataframe):
        placeholder.dataframe(message.dataframe)
    elif isinstance(message, str):
        if os.path.isfile(message):
            placeholder.image(message)
        else:
            placeholder.text(message)
    else:
        placeholder.write(message)


for msg in st.session_state.dbqa_pandasai_messages:
    render_message(msg["content"], st.chat_message(msg["role"]))

# https://streamlit.io/generative-ai
# TODO: make response streaming https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps#build-a-simple-chatbot-gui-with-streaming
if prompt := st.chat_input(disabled=st.session_state.pandasai_df is None):
    st.session_state.dbqa_pandasai_messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # TODO: can't properly save image
    response = st.session_state.pandasai_df.chat(prompt)
    # Debug
    # st.write(response)
    st.session_state.dbqa_pandasai_messages.append(
        {"role": "assistant", "content": response}
    )
    render_message(response, st.chat_message("assistant"))
