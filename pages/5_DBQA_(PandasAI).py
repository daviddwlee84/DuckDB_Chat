from typing import Literal, Union, Tuple
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import glob
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
    st.session_state.temp_images = []

chat_mode: Literal["Single Turn", "Multi Turn"] = st.selectbox(
    "Chat Mode", ["Single Turn", "Multi Turn"]
)
rephrase_query: bool = st.checkbox(
    "Rephrase Query (Only used in Multi-Turn Agent)",
    disabled=not chat_mode == "Multi Turn",
)


uploaded_file = st.file_uploader(
    "Data you want to query (support CSV, Parquet, and Json).",
    accept_multiple_files=False,
)

# https://docs.streamlit.io/library/advanced-features/static-file-serving
CHARTS_PATH = os.path.join(curr_dir, "../static/images/")

if uploaded_file is None:
    st.session_state.dbqa_pandasai_messages = []
    st.session_state.pandasai_df = None
else:
    config = {
        "llm": llm,
        "verbose": True,
        "save_charts": True,
        "save_charts_path": CHARTS_PATH,
        "open_charts": False,
        "enable_cache": True,
    }

    if st.session_state.dbqa_pandasai_uploaded_file != uploaded_file:
        st.session_state.dbqa_pandasai_messages = []
        st.session_state.dbqa_pandasai_uploaded_file = uploaded_file
        for img_path in st.session_state.temp_images:
            os.remove(img_path)
            st.toast(f'Clean cache image {img_path}')
        st.session_state.temp_images = []

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
        st.session_state.chat_mode = chat_mode
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
    elif isinstance(message, str) and message.endswith(".png"):
        # BUG: streamlit.runtime.media_file_storage.MediaFileStorageError
        # placeholder.image(message)
        placeholder.markdown(f"![]({message})")
    else:
        placeholder.write(message)


def get_latest_image() -> Tuple[str, str]:
    """
    https://stackoverflow.com/questions/76513782/capture-image-response-from-pandasai-as-flask-api-response
    https://support.google.com/chrome/thread/162698059/not-allowed-to-load-local-resource-how-to-fix-this?hl=en
    https://docs.streamlit.io/library/advanced-features/static-file-serving
    """
    images = glob.glob(os.path.join(CHARTS_PATH, "*.png"))
    latest_image = max(images, key=os.path.getctime)
    return (
        latest_image,
        os.path.join("app/static/images/", os.path.basename(latest_image)),
    )


for msg in st.session_state.dbqa_pandasai_messages:
    render_message(msg["content"], st.chat_message(msg["role"]))
    if explanation := msg.get("explanation"):
        render_message(explanation, st.chat_message(msg["role"]))

# https://streamlit.io/generative-ai
# TODO: make response streaming https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps#build-a-simple-chatbot-gui-with-streaming
if prompt := st.chat_input(disabled=st.session_state.pandasai_df is None):
    st.session_state.dbqa_pandasai_messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    if isinstance(st.session_state.pandasai_df, Agent):
        if rephrase_query:
            # BUG: st.session_state.temp_images
            response = st.session_state.pandasai_df.rephrase_query(prompt)
        else:
            response = st.session_state.pandasai_df.chat(prompt)
        if response is None:
            real_path, response = get_latest_image()
            st.session_state.temp_images.append(real_path)
        explanation = st.session_state.pandasai_df.explain()
        st.session_state.dbqa_pandasai_messages.append(
            {"role": "assistant", "content": response, "explanation": explanation}
        )
        render_message(response, st.chat_message("assistant"))
        render_message(explanation, st.chat_message("assistant"))
    else:
        response = st.session_state.pandasai_df.chat(prompt)
        if response is None:
            real_path, response = get_latest_image()
            st.session_state.temp_images.append(real_path)
        st.session_state.dbqa_pandasai_messages.append(
            {"role": "assistant", "content": response}
        )
        render_message(response, st.chat_message("assistant"))
