from __future__ import annotations

import asyncio
import json

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from implementation.db import SQLiteAdapter
from implementation.init_db import create_database
from implementation.mcp_server import create_mcp_server


def run(coro):
    return asyncio.run(coro)


def build_server(tmp_path):
    db_path = create_database(tmp_path / "lab.db")
    return create_mcp_server(SQLiteAdapter(db_path))


def test_tools_and_resources_are_discoverable(tmp_path):
    async def scenario():
        async with Client(build_server(tmp_path)) as client:
            tools = await client.list_tools()
            assert {tool.name for tool in tools} == {"search", "insert", "aggregate"}

            resources = await client.list_resources()
            assert {str(resource.uri) for resource in resources} == {"schema://database"}

            templates = await client.list_resource_templates()
            assert {str(template.uriTemplate) for template in templates} == {
                "schema://table/{table_name}"
            }

    run(scenario())


def test_schema_resources_are_readable(tmp_path):
    async def scenario():
        async with Client(build_server(tmp_path)) as client:
            database_schema = await client.read_resource("schema://database")
            database_payload = json.loads(database_schema[0].text)
            assert {"students", "courses", "enrollments"}.issubset(
                database_payload["tables"].keys()
            )

            table_schema = await client.read_resource("schema://table/students")
            table_payload = json.loads(table_schema[0].text)
            assert table_payload["table"] == "students"
            assert {column["name"] for column in table_payload["columns"]} >= {
                "id",
                "name",
                "cohort",
                "score",
            }

    run(scenario())


def test_search_insert_and_aggregate_tools(tmp_path):
    async def scenario():
        async with Client(build_server(tmp_path)) as client:
            search = await client.call_tool(
                "search",
                {
                    "table": "students",
                    "filters": {"cohort": "A1"},
                    "columns": ["name", "cohort", "score"],
                    "order_by": "score",
                    "descending": True,
                    "limit": 2,
                },
            )
            assert search.data["count"] == 2
            assert search.data["rows"][0]["name"] == "Vu Huy"

            insert = await client.call_tool(
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
            assert insert.data["inserted"]["id"] == 6
            assert insert.data["inserted"]["email"] == "minh.do@example.com"

            aggregate = await client.call_tool(
                "aggregate",
                {"table": "students", "metric": "avg", "column": "score", "group_by": "cohort"},
            )
            cohort_values = {row["cohort"]: row["value"] for row in aggregate.data["rows"]}
            assert pytest.approx(cohort_values["A1"], rel=0.001) == 91.6666666667
            assert pytest.approx(cohort_values["A3"], rel=0.001) == 84.0

    run(scenario())


@pytest.mark.parametrize(
    ("tool", "payload", "expected"),
    [
        ("search", {"table": "missing"}, "unknown table"),
        ("search", {"table": "students", "columns": ["missing"]}, "unknown column"),
        (
            "search",
            {"table": "students", "filters": [{"column": "score", "op": "between", "value": [80, 90]}]},
            "unsupported filter operator",
        ),
        ("insert", {"table": "students", "values": {}}, "non-empty values"),
        ("aggregate", {"table": "students", "metric": "median", "column": "score"}, "unsupported aggregate"),
        ("aggregate", {"table": "students", "metric": "avg"}, "requires a column"),
    ],
)
def test_invalid_tool_calls_return_clear_errors(tmp_path, tool, payload, expected):
    async def scenario():
        async with Client(build_server(tmp_path)) as client:
            with pytest.raises(ToolError, match=expected):
                await client.call_tool(tool, payload)

    run(scenario())

