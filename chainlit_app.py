from typing import Optional
import chainlit as cl
import pandas as pd
import duckdb
import time


duckdb_connect = duckdb.connect(
    ":memory:", config={"allow_unsigned_extensions": "true"}
)
# duckdb_connect.install_extension("httpfs")
# duckdb_connect.load_extension("httpfs")

global_df: Optional[pd.DataFrame] = None
global_settings: dict = {}

DEFAULT_TABLE_NAME = "tbl"


@cl.on_chat_start
async def start():
    global global_df
    global duckdb_connect
    global global_settings

    settings = await cl.ChatSettings(
        [
            cl.input_widget.Select(
                id="ShowIndex",
                label="Show Index",
                values=["Yes", "No"],
                initial_index=0,
            ),
            cl.input_widget.Select(
                id="ShowTime",
                label="Show Time",
                values=["Yes", "No"],
                initial_index=0,
            ),
        ]
    ).send()
    global_settings.update(settings)

    files = None

    # Wait for the user to upload a file
    while files == None:
        # https://docs.chainlit.io/api-reference/ask/ask-for-file
        files = await cl.AskFileMessage(
            content="Please upload a csv file to begin!",
            accept={"text/plain": [".csv"]},
            max_size_mb=200,
        ).send()

    text_file = files[0]

    # TODO: add more file type support
    # TODO: add multi-file suport
    with open(text_file.path, "r", encoding="utf-8") as fp:
        global_df = pd.read_csv(fp)

    # Let the user know that the system is ready
    await cl.Message(
        content=f"`{text_file.name}` uploaded, it contains {len(global_df)} rows!"
    ).send()

    # TODO: merge them into single markdown message
    await cl.Message(content="Table Preview (first 10 rows):").send()
    await cl.Message(content=global_df.head(10).to_markdown(index=True)).send()

    duckdb_connect.register(DEFAULT_TABLE_NAME, global_df)


@cl.step
async def query_duckdb(sql_query: str) -> str:
    global duckdb_connect
    try:
        return duckdb_connect.execute(sql_query).df().to_markdown(index=True)
    except Exception as e:
        return repr(e)


@cl.on_message
async def main(message: cl.Message):
    global global_settings

    start = time.perf_counter()
    # Call the tool
    result = await query_duckdb(message.content)
    time_usage = time.perf_counter() - start

    # TODO: merge them into single markdown message
    # Send the final answer.
    await cl.Message(content=result).send()
    if global_settings.get("ShowTime") == "Yes":
        await cl.Message(content=f"Time usage: {time_usage:.2f} seconds.").send()
