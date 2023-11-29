# DuckDB Chat

Access file as a database with interactive SQL query experience.

- [Online Demo](https://duckdb-chat-demo.streamlit.app/)

## Getting Started

![Demo](demo/DuckDB-Chat-Demo.png)

```bash
pip install -r requirements.txt
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
- [ ] Maybe user can ignore "FROM" clause, which by default indicate latest generated table
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
