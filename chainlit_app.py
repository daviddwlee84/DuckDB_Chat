import chainlit as cl
import pandas as pd


@cl.on_chat_start
async def start():
    files = None

    # Wait for the user to upload a file
    while files == None:
        # https://docs.chainlit.io/api-reference/ask/ask-for-file
        files = await cl.AskFileMessage(
            content="Please upload a csv file to begin!",
            accept={"text/plain": [".csv"]},
        ).send()

    text_file = files[0]

    with open(text_file.path, "r", encoding="utf-8") as fp:
        df = pd.read_csv(fp)

    # Let the user know that the system is ready
    await cl.Message(
        content=f"`{text_file.name}` uploaded, it contains {len(df)} rows!"
    ).send()
