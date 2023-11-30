# DuckDB Chat

Access file as a database with interactive SQL query experience.

- [Online Demo](https://duckdb-chat-demo.streamlit.app/)

## Getting Started

![Demo](demo/DuckDB-Chat-Demo.png)

```bash
pip install -r requirements.txt
```

```bash
# Optional
cp example.env .env
# Fill-in your keys
# ...
```

```bash
streamlit run app.py
```

## Todo

- [ ] Add [demo of DuckDB with Jupyter Notebook](DuckDB_with_JupyterNotebook)
- [X] Able to use customized table alias
  - [ ] Implement with more elegant way
- [ ] Support multiple file loading (same extension and schema)
- [X] Add row limit for potential large file
  - [X] `<= 0` as no limit
  - [X] Add `df.head()` at initial state
  - [X] Add LIMIT at the end of SQL query
  - [ ] Use more elegant way...?
- [ ] Support no header CSV (or see what will happened)
- [ ] Support DuckDB, SQLite, ... ([Connecting to a database — Python documentation](https://jupysql.ploomber.io/en/latest/connecting.html))
- [ ] Able to plot (maybe indicate by some prefix like Jupyter magics)
  - [ ] Plot button (for each DataFrame or at the end) => this will make code very mess
- [ ] Retrieve file from URL ([DuckDB — Python documentation](https://jupysql.ploomber.io/en/latest/integrations/duckdb.html#id1))
- [X] Maybe user can ignore "FROM" clause, which by default indicate ~~latest generated table~~ original file
  - [ ] Think of option between latest generated table or the original file
- [X] Option to print statistics (e.g. running time, rows, columns, ...)
- [X] ~~Add clear page button (clear the chat history but keep the file pointer)~~ => Delete file or upload new one to clear history
- [X] Add SQL hint and external resources on page
  - [ ] Add cheat sheet image
- [X] Add option of auto `SELECT * FROM table` when the file loaded => Add session initial options
  - [X] Also print some memory information
- [X] Deploy this repository to Streamlit
- [ ] Support DuckDB extensions
  - [ ] [httpfs Extension - DuckDB](https://duckdb.org/docs/extensions/httpfs)
- [ ] Support web file path / API e.g. https://api.github.com/search/repositories?q=jupyter&sort=stars&order=desc
  - [Analyzing Github Data with JupySQL + DuckDB — Python documentation](https://jupysql.ploomber.io/en/latest/tutorials/duckdb-github.html)
- [ ] Remove the file size limit of the file uploader
- [ ] Add natural language query support
  - [ ] Can refer to this [neural-maze/talking_with_hn: The full experience of chatting with your favourite news website.](https://github.com/neural-maze/talking_with_hn)
  - [ ] Making agent that can generate DuckDB SQL query
  - [ ] Making agent that can summary table
- [ ] Can not only do SQL query but can modify table
- [ ] See how to change the main page name (i.e. app) without re-deploy Streamlit app
- [X] Manage OpenAI keys in global settings
  - [ ] Maybe move duplicate code block into one place

## Resources

### DuckDB

- [Python API - DuckDB](https://duckdb.org/docs/api/python/overview)
- [SQL Introduction - DuckDB](https://duckdb.org/docs/sql/introduction)
- [DuckDB Documentation](https://duckdb.org/duckdb-docs.pdf)

### Streamlit

- [Build a basic LLM chat app - Streamlit Docs](https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps)
- [Chat elements - Streamlit Docs](https://docs.streamlit.io/library/api-reference/chat)

Deploy

- [Deploy your app - Streamlit Docs](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)
- [App dependencies - Streamlit Docs](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/app-dependencies)
- [Configuration - Streamlit Docs](https://docs.streamlit.io/library/advanced-features/configuration)

LangChain x Streamlit

- [Streamlit | 🦜️🔗 Langchain](https://python.langchain.com/docs/integrations/callbacks/streamlit)
- [Streamlit • Generative AI](https://streamlit.io/generative-ai)
  - [streamlit/llm-examples: Streamlit LLM app examples for getting started](https://github.com/streamlit/llm-examples/)

### LangChain

- [**SQL | 🦜️🔗 Langchain**](https://python.langchain.com/docs/use_cases/qa_structured/sql)
  - Case 1: Text-to-SQL query
  - Case 2: Text-to-SQL query and execution
  - Case 3: SQL agents
- [SQL Database | 🦜️🔗 Langchain](https://python.langchain.com/docs/integrations/toolkits/sql_database)
  - [feat: parquet file support for SQL agent · Issue #2002 · langchain-ai/langchain](https://github.com/langchain-ai/langchain/issues/2002) (this guy use parquet with duckdb => convert to SQLite)
- [CSV | 🦜️🔗 Langchain](https://python.langchain.com/docs/integrations/toolkits/csv)
- [sugarforever/LangChain-SQL-Chain](https://github.com/sugarforever/LangChain-SQL-Chain)
- [**LLMs and SQL**](https://blog.langchain.dev/llms-and-sql/)
