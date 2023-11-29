# DuckDB Chat

Access file as a database with interactive SQL query experience.

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
- [ ] Support no header CSV (or see what will happened)
- [ ] Support DuckDB, SQLite, ... ([Connecting to a database — Python documentation](https://jupysql.ploomber.io/en/latest/connecting.html))
- [ ] Able to plot (maybe indicate by some prefix like Jupyter magics)
- [ ] Retrieve file from URL ([DuckDB — Python documentation](https://jupysql.ploomber.io/en/latest/integrations/duckdb.html#id1))
- [ ] Maybe user can ignore "FROM" clause, which by default indicate latest generated table
- [ ] Option to print statistics (e.g. running time, rows, columns, ...)

## Resources

### DuckDB

- [Python API - DuckDB](https://duckdb.org/docs/api/python/overview)

### Streamlit

- [Build a basic LLM chat app - Streamlit Docs](https://docs.streamlit.io/knowledge-base/tutorials/build-conversational-apps)
- [Chat elements - Streamlit Docs](https://docs.streamlit.io/library/api-reference/chat)
