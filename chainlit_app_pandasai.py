from typing import Optional, Dict, List, Union
import chainlit as cl
import pandas as pd
import time
import os
from chainlit.element import ElementBased
from pandasai.llm import OpenAI, AzureOpenAI
from pandasai_lib import ModifiedAgent, ModifiedSmartDatalake, ModifiedMemory
import pathlib
import pandasai

DEFAULT_TABLE_NAME = "tbl"
curr_dir = os.path.dirname(os.path.abspath(__file__))
CHARTS_PATH = os.path.join(curr_dir, "static/images/")
# https://docs.pandas-ai.com/en/latest/custom-whitelisted-dependencies/
# 1. pip install
# 2. Add whitelist
DEPENDENCY_WHITELIST = ["pypinyin", "xpinyin"]


async def _load_df_file(
    temp_file_path: str, file_name: str = None, description: str = None
) -> Optional[pandasai.SmartDataframe]:
    """
    TODO: description
    """
    path = pathlib.Path(file_name)
    if path.suffix == ".csv":
        df = pd.read_csv(temp_file_path)
    elif path.suffix == ".parquet":
        df = pd.read_parquet(temp_file_path)
    else:
        raise NotImplementedError(f"Unknown extension {path.suffix}")

    # Let the user know that the system is ready
    await cl.Message(
        content=f"`{path.name}` uploaded. It contains {len(df)} rows!"
    ).send()
    # TODO: merge them into single markdown message
    await cl.Message(content="Table Preview (first 10 rows):").send()
    await cl.Message(content=df.head(10).to_markdown(index=True)).send()

    return pandasai.SmartDataframe(df, path.stem, description)


def _update_pandas_df_from_global_table_dfs():
    global_table_dfs: Dict[str, pd.DataFrame] = cl.user_session.get(
        "global_table_dfs", {}
    )
    if not global_table_dfs:
        return False

    config = {
        "llm": cl.user_session.get("llm"),
        "verbose": True,
        "save_charts": True,
        "save_charts_path": CHARTS_PATH,
        "open_charts": False,
        "enable_cache": True,
        "custom_whitelisted_dependencies": DEPENDENCY_WHITELIST,
    }
    if cl.user_session.get("is_multi_turn"):
        pandasai_df = ModifiedAgent(
            global_table_dfs.values(),
            config=config,
            memory=cl.user_session.get("Memory", ModifiedMemory(10)),
        )
    else:
        pandasai_df = ModifiedSmartDatalake(global_table_dfs.values(), config=config)
    cl.user_session.set("pandasai_df", pandasai_df)

    return pandasai_df


async def _process_file_elements(elements: List[ElementBased]):
    global_table_dfs: Dict[str, pd.DataFrame] = cl.user_session.get(
        "global_table_dfs", {}
    )
    for element in elements:
        global_table_dfs[element.name] = await _load_df_file(element.path, element.name)

    cl.user_session.set("global_table_dfs", global_table_dfs)
    if not _update_pandas_df_from_global_table_dfs():
        await cl.Message(content="No valid data.").send()
    else:
        await cl.Message(content="New Data Uploaded. Create new Agent.").send()


@cl.on_chat_start
async def start():
    settings = await cl.ChatSettings(
        [
            cl.input_widget.Select(
                id="chat_mode",
                label="Chat Mode",
                initial_index=1,
                values=["Single Turn", "Multi Turn"],
                description="Single Turn will use SmartDatalake, while Multi Turn will use Agent.",
            ),
            cl.input_widget.Select(
                id="openai_selection",
                label="OpenAI Version",
                initial_index=1,
                values=["OpenAI", "Azure OpenAI"],
            ),
            cl.input_widget.TextInput(
                id="openai_api_key",
                label="OpenAI API Key",
                initial=os.getenv("OPENAI_API_KEY"),
            ),
            cl.input_widget.TextInput(
                id="azure_openai_api_key",
                label="Azure OpenAI API Key",
                initial=os.getenv("AZURE_OPENAI_KEY"),
            ),
            cl.input_widget.TextInput(
                id="azure_openai_endpoint",
                label="Azure OpenAI Endpoint",
                initial=os.getenv("AZURE_OPENAI_ENDPOINT"),
            ),
            cl.input_widget.TextInput(
                id="azure_openai_deployment_name",
                label="Azure OpenAI Deployment Name",
                initial=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            ),
            cl.input_widget.TextInput(
                id="azure_openai_version",
                label="Azure OpenAI Version",
                initial=os.getenv("AZURE_OPENAI_VERSION"),
            ),
            # TODO: make sure gpt-3.5-turbo is default
            cl.input_widget.Select(
                id="chat_model",
                label="Chat Model",
                initial_index=5,
                values=OpenAI._supported_chat_models,
            ),
        ]
    ).send()
    await update_settings(settings)
    await cl.Message(
        "Add a csv/parquet file as attachment with any dummy message to begin!"
    ).send()
    cl.user_session.set("Memory", ModifiedMemory(memory_size=0))


@cl.on_settings_update
async def update_settings(settings: dict):
    """
    Setup llm
    Update global settings
    """
    try:
        if settings["openai_selection"] == "OpenAI":
            llm = OpenAI(
                model="gpt-35-turbo",
                api_token=settings["openai_api_key"],
            )
        elif settings["openai_selection"] == "Azure OpenAI":
            llm = AzureOpenAI(
                model="gpt-35-turbo",
                api_token=settings["azure_openai_api_key"],
                azure_endpoint=settings["azure_openai_endpoint"],
                api_version=settings["azure_openai_version"],
                deployment_name=settings["azure_openai_deployment_name"],
                is_chat_model=True,
            )
    except:
        llm = None

    cl.user_session.set("llm", llm)
    if cl.user_session.get("is_multi_turn") is None:
        cl.user_session.set("is_multi_turn", settings["chat_mode"] == "Multi Turn")
    else:
        if (settings["chat_mode"] == "Multi Turn") == cl.user_session.get(
            "is_multi_turn"
        ):
            return
        cl.user_session.set("is_multi_turn", settings["chat_mode"] == "Multi Turn")

        if not cl.user_session.get("pandasai_df"):
            return

        if not _update_pandas_df_from_global_table_dfs():
            await cl.Message(content="No valid data.").send()
            return

        await cl.Message(content="Chat mode changed. Create new Agent.").send()


def get_latest_image() -> str:
    """
    https://stackoverflow.com/questions/76513782/capture-image-response-from-pandasai-as-flask-api-response
    https://support.google.com/chrome/thread/162698059/not-allowed-to-load-local-resource-how-to-fix-this?hl=en
    https://docs.streamlit.io/library/advanced-features/static-file-serving
    """
    images = pathlib.Path(CHARTS_PATH).glob("*.png")
    latest_image = max(images, key=os.path.getctime)
    return str(latest_image.absolute())


@cl.on_message
async def main(message: cl.Message) -> None:
    if not cl.user_session.get("llm"):
        await cl.Message("🥸 Please setup OpenAI API key properly to continue.").send()
        return

    # Upload file
    if message.elements:
        await _process_file_elements(message.elements)
        return

    prompt = message.content
    pandasai_df: Optional[
        Union[ModifiedSmartDatalake, ModifiedAgent]
    ] = cl.user_session.get("pandasai_df")

    start = time.perf_counter()
    author = "Chatbot"
    if pandasai_df is not None:
        response = pandasai_df.chat(prompt)
        author = pandasai_df.__class__.__name__
    else:
        # NOTE: memory_size=0 means unlimited memory
        memory: ModifiedMemory = cl.user_session.get(
            "Memory", ModifiedMemory(memory_size=0)
        )
        memory.add(prompt, is_user=True)
        llm: Union[OpenAI, AzureOpenAI] = cl.user_session.get("llm")
        # Debug
        # response = str(memory.get_openai_messages())
        if cl.user_session.get("is_multi_turn"):
            response = (
                llm.client.create(
                    model=llm.model, messages=memory.get_openai_messages()
                )
                .choices[0]
                .message.content
            )
        else:
            # NOTE: this don't have memory
            response = llm.chat_completion(prompt)
        memory.add(response, is_user=False)
        cl.user_session.set("Memory", memory)
        author = llm.__class__.__name__
    if cl.user_session.get("is_multi_turn"):
        author += " (with Memory)"
    time_usage = time.perf_counter() - start

    elements = []
    if response is None:
        real_path = get_latest_image()
        cl.user_session.set(
            "temp_images", cl.user_session.get("temp_images", []) + [real_path]
        )
        response = real_path
        # https://docs.chainlit.io/api-reference/elements/image
        elements.append(cl.Image(path=real_path, name=prompt, display="inline"))

    if isinstance(response, pd.DataFrame) or isinstance(
        response, pandasai.SmartDataframe
    ):
        if len(response) > 10:
            await cl.Message(content=f"Since response is too large, we truncate the response and show the top 5 and last 5 results. Original shape {response.shape}").send()
            response = pd.concat([response.head(5), response.tail(5)])
        await cl.Message(
            content=response.to_markdown(), author=author, elements=elements
        ).send()
    else:
        await cl.Message(content=response, author=author, elements=elements).send()

    if isinstance(pandasai_df, ModifiedAgent):
        explanation = pandasai_df.explain()
        await cl.Message(content=explanation, author=author).send()

    await cl.Message(
        content=f"Time usage: {time_usage:.2f} seconds.", author=author
    ).send()


@cl.on_logout
def on_chat_end():
    for img_path in cl.user_session.get("temp_images", []):
        os.remove(img_path)
        print(f"Clean cache image {img_path}")
