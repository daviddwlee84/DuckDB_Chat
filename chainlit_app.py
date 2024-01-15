from typing import Optional
import chainlit as cl
import pandas as pd
import duckdb
import time
from utils import QueryRewriterForDuckDB


duckdb_connect = duckdb.connect(
    ":memory:", config={"allow_unsigned_extensions": "true"}
)
# duckdb_connect.install_extension("httpfs")
# duckdb_connect.load_extension("httpfs")

global_df: Optional[pd.DataFrame] = None
global_settings: dict = {}
query_rewriter = QueryRewriterForDuckDB(use_view_over_table=False, auto_from_table=True)


DEFAULT_TABLE_NAME = "tbl"


@cl.on_chat_start
async def start():
    global global_df
    global duckdb_connect
    global global_settings
    global query_rewriter

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
            cl.input_widget.Select(
                id="QueryRewrite",
                label="Query Rewrite",
                values=["Yes", "No"],
                initial_index=0,
            ),
            cl.input_widget.Select(
                id="QueryAutoFrom",
                label="Auto FROM Table",
                values=["Yes", "No"],
                initial_index=0,
            ),
        ]
    ).send()
    global_settings.update(settings)
    query_rewriter.auto_from_table = settings.get("QueryAutoFrom") == "Yes"

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
    query_rewriter.add_new_table(DEFAULT_TABLE_NAME)


# @cl.on_chat_end
# def on_chat_end():
#     global duckdb_connect
#     duckdb_connect.close()


@cl.step(name="Query DuckDB")
async def query_duckdb(sql_query: str) -> str:
    global duckdb_connect
    try:
        return duckdb_connect.execute(sql_query).df().to_markdown(index=True)
    except Exception as e:
        return str(e)


@cl.step(name="Query Rewrite", language="sql")
async def query_rewrite(query: str) -> str:
    global query_rewriter
    return query_rewriter(query)


@cl.on_message
async def main(message: cl.Message):
    global global_settings
    query = message.content
    start = time.perf_counter()
    # Call the tool
    if global_settings.get("QueryAutoFrom") == "Yes":
        query = await query_rewrite(query)
    result = await query_duckdb(query)
    time_usage = time.perf_counter() - start

    # TODO: merge them into single markdown message
    # Send the final answer.
    await cl.Message(content=result).send()
    if global_settings.get("ShowTime") == "Yes":
        await cl.Message(content=f"Time usage: {time_usage:.2f} seconds.").send()
