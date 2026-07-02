from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from fastmcp import Client

try:
    from .db import DEFAULT_DB_PATH, SQLiteAdapter
    from .init_db import create_database
    from .mcp_server import create_mcp_server
except ImportError:  # Allows running this file directly.
    from db import DEFAULT_DB_PATH, SQLiteAdapter
    from init_db import create_database
    from mcp_server import create_mcp_server


def print_json(label: str, payload: Any) -> None:
    print(f"\n== {label} ==")
    print(json.dumps(payload, ensure_ascii=True, indent=2))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


async def verify(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    db_path = create_database(db_path)
    server = create_mcp_server(SQLiteAdapter(db_path))

    async with Client(server) as client:
        tools = await client.list_tools()
        tool_names = {tool.name for tool in tools}
        print_json("tools", sorted(tool_names))
        require(tool_names == {"search", "insert", "aggregate"}, "required tools not discovered")

        resources = await client.list_resources()
        resource_uris = {str(resource.uri) for resource in resources}
        print_json("resources", sorted(resource_uris))
        require("schema://database" in resource_uris, "database schema resource not discovered")

        templates = await client.list_resource_templates()
        template_uris = {str(template.uriTemplate) for template in templates}
        print_json("resource templates", sorted(template_uris))
        require("schema://table/{table_name}" in template_uris, "table schema template not discovered")

        database_schema = await client.read_resource("schema://database")
        require("students" in database_schema[0].text, "database schema missing students table")
        print("\n== schema://database ==")
        print(database_schema[0].text[:500] + "...")

        students_schema = await client.read_resource("schema://table/students")
        require("cohort" in students_schema[0].text, "students schema missing cohort column")
        print("\n== schema://table/students ==")
        print(students_schema[0].text)

        search_result = await client.call_tool(
            "search",
            {
                "table": "students",
                "filters": {"cohort": "A1"},
                "columns": ["name", "cohort", "score"],
                "order_by": "score",
                "descending": True,
                "limit": 3,
            },
        )
        print_json("search students in A1", search_result.data)
        require(search_result.data["count"] == 3, "search should return 3 A1 students")

        insert_result = await client.call_tool(
            "insert",
            {
                "table": "students",
                "values": {
                    "name": "Do Minh",
                    "cohort": "A3",
                    "email": "minh.do@example.com",
                    "score": 84.0,
                    "active": 1,
                },
            },
        )
        print_json("insert student", insert_result.data)
        require(insert_result.data["inserted"]["id"] > 0, "insert did not return generated id")

        aggregate_result = await client.call_tool(
            "aggregate",
            {"table": "students", "metric": "avg", "column": "score", "group_by": "cohort"},
        )
        print_json("average score by cohort", aggregate_result.data)
        cohorts = {row["cohort"] for row in aggregate_result.data["rows"]}
        require({"A1", "A2", "A3"}.issubset(cohorts), "aggregate missing expected cohorts")

        logging.disable(logging.CRITICAL)
        try:
            invalid_result = await client.call_tool(
                "search", {"table": "missing_table"}, raise_on_error=False
            )
        finally:
            logging.disable(logging.NOTSET)
        print("\n== invalid search error ==")
        print(invalid_result.content[0].text)
        require(invalid_result.is_error, "invalid search unexpectedly succeeded")
        require(
            "unknown table" in invalid_result.content[0].text,
            "invalid search did not return clear unknown table error",
        )

    print("\nAll MCP verification checks passed.")


def main() -> int:
    asyncio.run(verify())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
