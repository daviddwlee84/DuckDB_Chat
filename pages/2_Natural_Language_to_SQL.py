import streamlit as st
from dotenv import load_dotenv
import os
import openai

curr_dir = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(curr_dir, "../.env"))

st.set_page_config(
    page_title="Natural Language to SQL",
)

st.title("Natural Language to SQL")
# st.markdown("Note that, we don't keep chat history to ChatGPT, queries are independent.")

with st.sidebar:
    openai_selection = st.selectbox("OpenAI Version", ["OpenAI", "Azure OpenAI"])

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

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if openai_selection == "OpenAI":
        if not st.session_state.openai_api_key:
            st.info("Please add your OpenAI API key to continue.")
            st.stop()

        # TODO: Update code to https://github.com/streamlit/llm-examples/blob/main/Chatbot.py
        # APIRemovedInV1: You tried to access openai.ChatCompletion, but this is no longer supported in openai>=1.0.0 - see the README at https://github.com/openai/openai-python for the API. You can run `openai migrate` to automatically upgrade your codebase to use the 1.0.0 interface. Alternatively, you can pin your installation to the old version, e.g. `pip install openai==0.28` A detailed migration guide is available here: https://github.com/openai/openai-python/discussions/742
        openai.api_key = st.session_state.openai_api_key
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=st.session_state.messages
        )
        msg = response.choices[0].message
        st.session_state.messages.append(msg)
        st.chat_message("assistant").write(msg.content)

    elif openai_selection == "Azure OpenAI":
        if not st.session_state.azure_openai_api_key:
            st.info("Please add your Azure OpenAI API key to continue.")
            st.stop()

        # TODO
