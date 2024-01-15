from typing import Set, Optional
import re


class QueryRewriterForDuckDB:
    latest_table: str
    current_active_tables: Set[str] = set()

    create_table_alias_re: re.Pattern = re.compile(r"(?i)^(\w+)\s*=\s*(.*)")
    create_table_name_re: re.Pattern = re.compile(
        r"(?i)create\s+(?:or\s+replace\s+)?(?:view|table)\s+(?P<table_name>\w+)\s+as"
    )

    def __init__(
        self,
        latest_table: Optional[str] = None,
        use_view_over_table: bool = False,
        auto_from_table: bool = True,
        keep_latest_statement_as_last_table: bool = False,
        # row_limit: int = 0,
        default_temp_table_name: str = "_temp",
    ) -> None:
        """
        row_limit is for super large data, you want to force every query as preview (deprecated now)
        """

        if latest_table is not None:
            self.latest_table = latest_table
        self.use_view_over_table = use_view_over_table
        self.auto_from_table = auto_from_table
        self.keep_latest_statement_as_last_table = keep_latest_statement_as_last_table
        self.default_temp_table_name = default_temp_table_name

    def add_new_table(self, table_name: str) -> bool:
        """
        if True means no existing table
        """
        existing = table_name in self.current_active_tables

        self.current_active_tables.add(table_name)
        self.latest_table = table_name

        return existing

    def rewrite(self, query: str, latest_table: str = None):
        if latest_table is not None:
            self.latest_table = latest_table

        if create_table_alias := self.create_table_alias_re.search(query):
            # https://duckdb.org/docs/sql/statements/create_table.html
            latest_table_name = create_table_alias.group(1)
            expression = create_table_alias.group(2)
            # NOTE: use OR REPLACE can support same table name override
            if self.use_view_over_table:
                # https://duckdb.org/docs/sql/statements/create_view.html
                query = f"CREATE OR REPLACE VIEW {latest_table_name} AS {expression}"
            else:
                query = f"CREATE OR REPLACE TABLE {latest_table_name} AS {expression}"

        if self.auto_from_table and "FROM" not in query.upper():
            if "SELECT" in query:
                query = query.replace("SELECT", f"FROM {self.latest_table} SELECT")
            elif "select" in query:
                query = query.replace("select", f"FROM {self.latest_table} SELECT")

        if "SELECT" not in query.upper():
            if query.strip() in self.current_active_tables:
                # query is table name
                # If only table name (without SELECT and FROM), then by default just output the table
                query = f"FROM {query.strip()} SELECT *;"
            else:
                # https://duckdb.org/docs/sql/functions/char.html
                # https://duckdb.org/docs/sql/functions/patternmatching.html
                # Special case, query is a quick test
                query = f"SELECT {query};"

        # TODO: if use aggregate function but without GROUP BY, automatically inference columns
        # BinderException: Binder Error: column "symbol" must appear in the GROUP BY clause or must be part of an aggregate function.
        # Either add it to the GROUP BY list, or use "ANY_VALUE(symbol)" if the exact value of "symbol" is not important.

        # TODO: not sure if this part make sense. Ideally, user should be aware of what they are doing.
        # (operation can cancel when it took too much time)
        # if self.row_limit > 0:
        #     if prompt.endswith(";"):
        #         prompt = prompt.replace(";", f" LIMIT {self.row_limit};")
        #     else:
        #         prompt += f" LIMIT {self.row_limit};"

        if not prompt.endswith(";"):
            # This is not necessary but will make description seems complete
            prompt += ";"

        return query

    def creating_table(self, query: str) -> Optional[str]:
        if is_creating_table := self.create_table_name_re.search(query):
            new_table_name = is_creating_table.group("table_name")
        else:
            new_table_name = (
                None
                if not self.keep_latest_statement_as_last_table
                else self.default_temp_table_name
            )
        return new_table_name
