from typing import Optional
import chainlit as cl
import pandas as pd
import duckdb
import time
from utils import QueryRewriterForDuckDB


# TODO: make this user session
global_df: Optional[pd.DataFrame] = None
do_query_rewrite: bool = False
show_time: bool = True

DEFAULT_TABLE_NAME = "tbl"


@cl.on_chat_start
async def start():
    cl.user_session.set(
        "duckdb_connect",
        duckdb.connect(":memory:", config={"allow_unsigned_extensions": "true"}),
    )

    global global_df

    settings = await cl.ChatSettings(
        [
            cl.input_widget.Switch(
                id="ShowIndex",
                label="Show Index",
                initial=True,
                description="Show table index.",
            ),
            cl.input_widget.Switch(
                id="ShowTime",
                label="Show Time",
                initial=True,
                description="Show execution time.",
            ),
            cl.input_widget.Switch(
                id="QueryRewrite",
                label="Query Rewrite",
                initial=True,
                description="Rewrite query.",
            ),
            cl.input_widget.Switch(
                id="QueryAutoFrom",
                label="Auto FROM Table",
                initial=True,
                description="Automatically add FROM table if not given.",
            ),
            cl.input_widget.NumberInput(
                id="RowNumberLimit",
                label="Row Number Limit",
                initial=0,
                description="If > 0, will only return specific number rows.",
            ),
        ]
    ).send()
    await update_settings(settings)

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

    duckdb_connect: duckdb.DuckDBPyConnection = cl.user_session.get("duckdb_connect")
    duckdb_connect.register(DEFAULT_TABLE_NAME, global_df)
    query_rewriter: QueryRewriterForDuckDB = cl.user_session.get("query_rewriter")
    query_rewriter.add_new_table(DEFAULT_TABLE_NAME)


@cl.on_settings_update
async def update_settings(settings: dict):
    """
    Setup query rewriter
    Update global settings
    """
    if cl.user_session.get("query_rewriter") is None:
        cl.user_session.set(
            "query_rewriter",
            QueryRewriterForDuckDB(
                use_view_over_table=False,
                auto_from_table=settings.get("QueryAutoFrom"),
                row_limit=settings.get("RowNumberLimit", 0),
            ),
        )
    else:
        query_rewriter: QueryRewriterForDuckDB = cl.user_session.get("query_rewriter")
        query_rewriter.auto_from_table = settings.get("QueryAutoFrom")
        query_rewriter.row_limit = settings.get("RowNumberLimit", 0)

    global do_query_rewrite, show_time
    do_query_rewrite = settings.get("QueryRewrite")
    show_time = settings.get("ShowTime")


# @cl.on_chat_end
# def on_chat_end():
#     global duckdb_connect
#     duckdb_connect.close()


@cl.step(name="Query DuckDB")
async def query_duckdb(sql_query: str) -> str:
    duckdb_connect: duckdb.DuckDBPyConnection = cl.user_session.get("duckdb_connect")
    try:
        return duckdb_connect.execute(sql_query).df().to_markdown(index=True)
    except Exception as e:
        return str(e)


@cl.step(name="Query Rewrite", language="sql")
async def query_rewrite(query: str) -> str:
    query_rewriter: QueryRewriterForDuckDB = cl.user_session.get("query_rewriter")
    return query_rewriter(query)


@cl.on_message
async def main(message: cl.Message):
    query = message.content
    start = time.perf_counter()
    # Call the tool
    global do_query_rewrite
    if do_query_rewrite:
        query = await query_rewrite(query)
    result = await query_duckdb(query)
    time_usage = time.perf_counter() - start

    # TODO: merge them into single markdown message
    # Send the final answer.
    await cl.Message(content=result).send()
    global show_time
    if show_time:
        await cl.Message(content=f"Time usage: {time_usage:.2f} seconds.").send()
