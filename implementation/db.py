from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "lab.db"


class ValidationError(ValueError):
    """Raised when a database request cannot be safely executed."""


class SQLiteAdapter:
    """Small SQLite adapter with identifier validation and parameterized values."""

    ALLOWED_OPERATORS = {
        "=": "=",
        "==": "=",
        "eq": "=",
        "!=": "!=",
        "<>": "!=",
        "ne": "!=",
        "<": "<",
        "lt": "<",
        "<=": "<=",
        "lte": "<=",
        ">": ">",
        "gt": ">",
        ">=": ">=",
        "gte": ">=",
        "like": "LIKE",
        "in": "IN",
    }
    ALLOWED_METRICS = {"count", "avg", "sum", "min", "max"}
    MAX_LIMIT = 100

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def list_tables(self) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        return [row["name"] for row in rows]

    def get_table_schema(self, table: str) -> dict[str, Any]:
        table = self._validate_table(table)
        quoted_table = self._quote_identifier(table)
        with self.connect() as conn:
            rows = conn.execute(f"PRAGMA table_info({quoted_table})").fetchall()
            foreign_keys = conn.execute(f"PRAGMA foreign_key_list({quoted_table})").fetchall()

        columns = [
            {
                "name": row["name"],
                "type": row["type"],
                "not_null": bool(row["notnull"]),
                "default": row["dflt_value"],
                "primary_key": bool(row["pk"]),
            }
            for row in rows
        ]
        relationships = [
            {
                "column": row["from"],
                "references_table": row["table"],
                "references_column": row["to"],
            }
            for row in foreign_keys
        ]
        return {"table": table, "columns": columns, "foreign_keys": relationships}

    def get_database_schema(self) -> dict[str, Any]:
        return {
            "database": str(self.db_path),
            "tables": {table: self.get_table_schema(table) for table in self.list_tables()},
        }

    def search(
        self,
        table: str,
        filters: dict[str, Any] | list[dict[str, Any]] | None = None,
        columns: list[str] | str | None = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str | None = None,
        descending: bool = False,
    ) -> dict[str, Any]:
        table = self._validate_table(table)
        selected_columns = self._normalize_columns(table, columns)
        limit = self._normalize_limit(limit)
        offset = self._normalize_offset(offset)

        where_sql, params = self._build_where_clause(table, filters)
        select_sql = ", ".join(self._quote_identifier(column) for column in selected_columns)
        sql = f"SELECT {select_sql} FROM {self._quote_identifier(table)}"
        if where_sql:
            sql += f" WHERE {where_sql}"
        if order_by:
            order_column = self._validate_column(table, order_by)
            direction = "DESC" if descending else "ASC"
            sql += f" ORDER BY {self._quote_identifier(order_column)} {direction}"
        sql += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        return {
            "table": table,
            "columns": selected_columns,
            "filters": filters or [],
            "limit": limit,
            "offset": offset,
            "count": len(rows),
            "rows": [dict(row) for row in rows],
        }

    def insert(self, table: str, values: dict[str, Any]) -> dict[str, Any]:
        table = self._validate_table(table)
        if not isinstance(values, dict) or not values:
            raise ValidationError("insert requires a non-empty values object")

        columns = [self._validate_column(table, column) for column in values.keys()]
        quoted_columns = ", ".join(self._quote_identifier(column) for column in columns)
        placeholders = ", ".join("?" for _ in columns)
        sql = f"INSERT INTO {self._quote_identifier(table)} ({quoted_columns}) VALUES ({placeholders})"
        params = [values[column] for column in columns]

        with self.connect() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            inserted_id = cursor.lastrowid

        payload = dict(values)
        primary_key = self._primary_key_column(table)
        if primary_key and primary_key not in payload:
            payload[primary_key] = inserted_id

        return {"table": table, "inserted": payload}

    def aggregate(
        self,
        table: str,
        metric: str,
        column: str | None = None,
        filters: dict[str, Any] | list[dict[str, Any]] | None = None,
        group_by: str | list[str] | None = None,
    ) -> dict[str, Any]:
        table = self._validate_table(table)
        metric = self._validate_metric(metric)

        if metric == "count" and column is None:
            aggregate_expr = "COUNT(*)"
            aggregate_column = "*"
        else:
            if column is None:
                raise ValidationError(f"{metric} requires a column")
            aggregate_column = self._validate_column(table, column)
            aggregate_expr = f"{metric.upper()}({self._quote_identifier(aggregate_column)})"

        group_columns = self._normalize_group_by(table, group_by)
        select_parts = [self._quote_identifier(column) for column in group_columns]
        select_parts.append(f"{aggregate_expr} AS value")

        where_sql, params = self._build_where_clause(table, filters)
        sql = f"SELECT {', '.join(select_parts)} FROM {self._quote_identifier(table)}"
        if where_sql:
            sql += f" WHERE {where_sql}"
        if group_columns:
            group_sql = ", ".join(self._quote_identifier(column) for column in group_columns)
            sql += f" GROUP BY {group_sql}"

        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        return {
            "table": table,
            "metric": metric,
            "column": aggregate_column,
            "group_by": group_columns,
            "filters": filters or [],
            "rows": [dict(row) for row in rows],
        }

    def schema_json(self, table: str | None = None) -> str:
        schema = self.get_table_schema(table) if table else self.get_database_schema()
        return json.dumps(schema, ensure_ascii=True, indent=2)

    def _validate_table(self, table: str) -> str:
        if not isinstance(table, str) or not table.strip():
            raise ValidationError("table name must be a non-empty string")
        table = table.strip()
        tables = set(self.list_tables())
        if table not in tables:
            raise ValidationError(f"unknown table: {table}")
        return table

    def _validate_column(self, table: str, column: str) -> str:
        if not isinstance(column, str) or not column.strip():
            raise ValidationError("column name must be a non-empty string")
        column = column.strip()
        columns = self._table_columns(table)
        if column not in columns:
            raise ValidationError(f"unknown column for {table}: {column}")
        return column

    def _validate_metric(self, metric: str) -> str:
        if not isinstance(metric, str):
            raise ValidationError("metric must be a string")
        metric = metric.lower().strip()
        if metric not in self.ALLOWED_METRICS:
            allowed = ", ".join(sorted(self.ALLOWED_METRICS))
            raise ValidationError(f"unsupported aggregate metric: {metric}. Allowed: {allowed}")
        return metric

    def _table_columns(self, table: str) -> set[str]:
        schema = self.get_table_schema(table)
        return {column["name"] for column in schema["columns"]}

    def _primary_key_column(self, table: str) -> str | None:
        schema = self.get_table_schema(table)
        for column in schema["columns"]:
            if column["primary_key"]:
                return column["name"]
        return None

    def _normalize_columns(self, table: str, columns: list[str] | str | None) -> list[str]:
        if columns is None or columns == []:
            return [column["name"] for column in self.get_table_schema(table)["columns"]]
        if isinstance(columns, str):
            columns = [column.strip() for column in columns.split(",") if column.strip()]
        if not isinstance(columns, list) or not columns:
            raise ValidationError("columns must be a non-empty list, comma string, or null")
        return [self._validate_column(table, column) for column in columns]

    def _normalize_group_by(self, table: str, group_by: str | list[str] | None) -> list[str]:
        if group_by is None or group_by == []:
            return []
        if isinstance(group_by, str):
            group_by = [column.strip() for column in group_by.split(",") if column.strip()]
        if not isinstance(group_by, list) or not group_by:
            raise ValidationError("group_by must be a column, list of columns, or null")
        return [self._validate_column(table, column) for column in group_by]

    def _normalize_limit(self, limit: int) -> int:
        try:
            limit = int(limit)
        except (TypeError, ValueError) as exc:
            raise ValidationError("limit must be an integer") from exc
        if limit < 1:
            raise ValidationError("limit must be at least 1")
        return min(limit, self.MAX_LIMIT)

    def _normalize_offset(self, offset: int) -> int:
        try:
            offset = int(offset)
        except (TypeError, ValueError) as exc:
            raise ValidationError("offset must be an integer") from exc
        if offset < 0:
            raise ValidationError("offset cannot be negative")
        return offset

    def _build_where_clause(
        self,
        table: str,
        filters: dict[str, Any] | list[dict[str, Any]] | None,
    ) -> tuple[str, list[Any]]:
        normalized = self._normalize_filters(filters)
        clauses: list[str] = []
        params: list[Any] = []

        for filter_item in normalized:
            column = self._validate_column(table, filter_item["column"])
            operator_key = str(filter_item["op"]).lower().strip()
            if operator_key not in self.ALLOWED_OPERATORS:
                raise ValidationError(f"unsupported filter operator: {filter_item['op']}")
            operator = self.ALLOWED_OPERATORS[operator_key]
            value = filter_item["value"]

            if operator == "IN":
                if not isinstance(value, list) or not value:
                    raise ValidationError("IN filters require a non-empty list value")
                placeholders = ", ".join("?" for _ in value)
                clauses.append(f"{self._quote_identifier(column)} IN ({placeholders})")
                params.extend(value)
            else:
                clauses.append(f"{self._quote_identifier(column)} {operator} ?")
                params.append(value)

        return " AND ".join(clauses), params

    def _normalize_filters(
        self,
        filters: dict[str, Any] | list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        if filters is None or filters == {} or filters == []:
            return []

        if isinstance(filters, dict):
            if {"column", "op", "value"}.issubset(filters.keys()):
                return [filters]
            normalized = []
            for column, value in filters.items():
                if isinstance(value, dict):
                    if len(value) != 1:
                        raise ValidationError(f"filter for {column} must contain exactly one operator")
                    op, op_value = next(iter(value.items()))
                    normalized.append({"column": column, "op": op, "value": op_value})
                else:
                    normalized.append({"column": column, "op": "=", "value": value})
            return normalized

        if isinstance(filters, list):
            normalized = []
            for item in filters:
                if not isinstance(item, dict) or not {"column", "op", "value"}.issubset(item.keys()):
                    raise ValidationError("each filter must include column, op, and value")
                normalized.append(item)
            return normalized

        raise ValidationError("filters must be an object, list, or null")

    def _quote_identifier(self, identifier: str) -> str:
        if '"' in identifier:
            raise ValidationError("identifier cannot contain double quotes")
        return f'"{identifier}"'

