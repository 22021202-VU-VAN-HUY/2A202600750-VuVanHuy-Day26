from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

try:
    from .db import DEFAULT_DB_PATH, SQLiteAdapter, ValidationError
    from .init_db import create_database
except ImportError:  # Allows running this file directly.
    from db import DEFAULT_DB_PATH, SQLiteAdapter, ValidationError
    from init_db import create_database


SERVER_INSTRUCTIONS = (
    "Use this MCP server for the SQLite lab database. Read schema://database "
    "or schema://table/{table_name} before choosing columns. Tools reject "
    "unknown tables, columns, unsupported operators, and invalid aggregates. "
    "Prefer small limits for search output."
)


def ensure_database(db_path: str | Path = DEFAULT_DB_PATH) -> Path:
    """Create the default lab database when it does not exist yet."""

    db_path = Path(db_path)
    if not db_path.exists():
        create_database(db_path)
    return db_path


def create_mcp_server(adapter: SQLiteAdapter | None = None) -> FastMCP:
    adapter = adapter or SQLiteAdapter(ensure_database())
    mcp = FastMCP("SQLite Lab MCP Server", instructions=SERVER_INSTRUCTIONS)

    @mcp.tool(
        name="search",
        description=(
            "Search rows in a validated table. Supports selected columns, "
            "filters, ordering, limit, and offset."
        ),
    )
    def search(
        table: str,
        filters: dict[str, Any] | list[dict[str, Any]] | None = None,
        columns: list[str] | str | None = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = False,
    ) -> dict[str, Any]:
        try:
            return adapter.search(
                table=table,
                filters=filters,
                columns=columns,
                limit=limit,
                offset=offset,
                order_by=order_by,
                descending=descending,
            )
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc
        except sqlite3.Error as exc:
            raise RuntimeError(f"database error: {exc}") from exc

    @mcp.tool(
        name="insert",
        description=(
            "Insert one row into a validated table. The values object must be "
            "non-empty and every column must exist."
        ),
    )
    def insert(table: str, values: dict[str, Any]) -> dict[str, Any]:
        try:
            return adapter.insert(table=table, values=values)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"insert violates database constraints: {exc}") from exc
        except sqlite3.Error as exc:
            raise RuntimeError(f"database error: {exc}") from exc

    @mcp.tool(
        name="aggregate",
        description=(
            "Run count, avg, sum, min, or max over a validated table. Supports "
            "optional filters and group_by."
        ),
    )
    def aggregate(
        table: str,
        metric: str,
        column: str | None = None,
        filters: dict[str, Any] | list[dict[str, Any]] | None = None,
        group_by: str | list[str] | None = None,
    ) -> dict[str, Any]:
        try:
            return adapter.aggregate(
                table=table,
                metric=metric,
                column=column,
                filters=filters,
                group_by=group_by,
            )
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc
        except sqlite3.Error as exc:
            raise RuntimeError(f"database error: {exc}") from exc

    @mcp.resource(
        "schema://database",
        name="database_schema",
        description="Full SQLite database schema as JSON text.",
        mime_type="application/json",
    )
    def database_schema() -> str:
        try:
            return adapter.schema_json()
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc

    @mcp.resource(
        "schema://table/{table_name}",
        name="table_schema",
        description="Single table schema as JSON text.",
        mime_type="application/json",
    )
    def table_schema(table_name: str) -> str:
        try:
            return adapter.schema_json(table_name)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc

    return mcp


mcp = create_mcp_server()


if __name__ == "__main__":
    mcp.run()
