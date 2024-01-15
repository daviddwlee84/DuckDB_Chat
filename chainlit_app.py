from typing import Optional, Dict
import chainlit as cl
import pandas as pd
import duckdb
import time
from utils import QueryRewriterForDuckDB
import os


# TODO: make this user session
do_query_rewrite: bool = False
show_time: bool = True

DEFAULT_TABLE_NAME = "tbl"


async def upload_new_table(
    file_path: str,
    simplified_file_name: str = None,
    table_name: str = DEFAULT_TABLE_NAME,
    extension: str = None,
):
    global_table_df: Dict[str, pd.DataFrame] = cl.user_session.get("global_table_df")
    # TODO: add more file type support
    # TODO: add multi-file suport
    if not extension:
        if simplified_file_name:
            extension = simplified_file_name.rsplit(".", 1)[-1]
        else:
            extension = file_path.rsplit('.', 1)[-1]
    if extension == "csv":
        with open(file_path, "r", encoding="utf-8") as fp:
            global_table_df[table_name] = pd.read_csv(fp)
    elif extension == "parquet":
        with open(file_path, "rb") as fp:
            global_table_df[table_name] = pd.read_parquet(fp)
    else:
        raise NotImplementedError(f"Unknown extension {extension}")

    if not simplified_file_name:
        simplified_file_name = os.path.basename(file_path)

    # Let the user know that the system is ready
    await cl.Message(
        content=f"`{simplified_file_name}` uploaded as table `{table_name}`, it contains {len(global_table_df[table_name])} rows!"
    ).send()

    # TODO: merge them into single markdown message
    await cl.Message(content="Table Preview (first 10 rows):").send()
    await cl.Message(
        content=global_table_df[table_name].head(10).to_markdown(index=True)
    ).send()

    duckdb_connect: duckdb.DuckDBPyConnection = cl.user_session.get("duckdb_connect")
    # https://duckdb.org/docs/api/python/data_ingestion
    # https://duckdb.org/docs/api/python/overview.html
    duckdb_connect.register(table_name, global_table_df[table_name])
    query_rewriter: QueryRewriterForDuckDB = cl.user_session.get("query_rewriter")
    query_rewriter.add_new_table(table_name)


@cl.on_chat_start
async def start():
    cl.user_session.set(
        "duckdb_connect",
        duckdb.connect(":memory:", config={"allow_unsigned_extensions": "true"}),
    )
    cl.user_session.set(
        "global_table_df",
        {},
    )

    # https://docs.chainlit.io/advanced-features/chat-settings
    # https://github.com/Chainlit/cookbook/blob/main/image-gen/app.py
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

    # files = None
    #
    # # Wait for the user to upload a file
    # while files == None:
    #     # https://docs.chainlit.io/api-reference/ask/ask-for-file
    #     files = await cl.AskFileMessage(
    #         content="Please upload a csv file to begin!",
    #         accept={"text/plain": [".csv"]},
    #         max_size_mb=200,
    #     ).send()
    #
    # text_file = files[0]
    #
    # await upload_new_table(text_file.path, text_file.name, DEFAULT_TABLE_NAME)

    # TODO:
    await cl.Message(
        "Add a csv/parquet file as attachment with a table name to begin!"
    ).send()


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
    # Chainlit can handle Error and print
    return duckdb_connect.execute(sql_query).df().to_markdown(index=True)


@cl.step(name="Query Rewrite", language="sql")
async def query_rewrite(query: str) -> str:
    query_rewriter: QueryRewriterForDuckDB = cl.user_session.get("query_rewriter")
    return query_rewriter(query)


@cl.on_message
async def main(message: cl.Message) -> None:
    query = message.content
    if message.elements:
        print(message.elements)
        if len(query.strip().split()) != 1:
            # TODO: prevent from something like 123data
            raise ValueError("Table name should be single string.")
        if len(message.elements) > 1:
            raise ValueError("Too many file uploaded. Currently only support 1.")
        file = message.elements[0]
        await upload_new_table(file.path, file.name, query)
        return

    start = time.perf_counter()
    # Call the tool
    global do_query_rewrite
    if do_query_rewrite:
        query = await query_rewrite(query)
    result = await query_duckdb(query)
    time_usage = time.perf_counter() - start

    actions = [
        cl.Action(name="Plot", value=query),
        # cl.Action(name="Statistics", value=query, df=result),
    ]

    # TODO: merge them into single markdown message
    # Send the final answer.
    await cl.Message(content=result, actions=actions).send()
    global show_time
    if show_time:
        await cl.Message(content=f"Time usage: {time_usage:.2f} seconds.").send()


@cl.action_callback("Plot")
async def plot(action: cl.Action) -> None:
    await cl.Message(f"TBD: plotting {action.value}").send()


# @cl.action_callback("Statistics")
# async def statistics(action: cl.Action) -> None:
#     await cl.Message(action.df.to_markdown(index=True)).send()
