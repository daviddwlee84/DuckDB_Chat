# `chainlit_app.py`: SQL App

1. Upload initial file (default table name is now `tbl`)
2. Every Round
   - Input SQL query
   - Attach a file and give a table name

# `chainlit_app_pandasai.py`: LLM App

If not upload any file, it is a simple LLM app.
By default it is using multi-turn (i.e. with chat memory)

You can upload any file as attachment with a dummy message to upload data.
Then it will become a PandasAI agent or smart datalake.

If you found your generated code has "dependencies" that is not in the whitelist

You can

1. `pip install` it
2. Add to `DEPENDENCY_WHITELIST`
