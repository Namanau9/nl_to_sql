"""Schema discovery: introspect a live database into a structured model.

Uses SQLAlchemy reflection so the same discovery logic works against the
read-only execution database. Nothing about a specific question is hard-coded
here -- the returned model is a faithful representation of whatever tables the
database actually contains.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import inspect

from app.core import get_logger

log = get_logger(__name__)


@dataclass
class ColumnInfo:
    name: str
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    column_default: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "is_nullable": self.is_nullable,
            "is_primary_key": self.is_primary_key,
            "column_default": self.column_default,
        }


@dataclass
class TableInfo:
    name: str
    schema: str = "public"
    columns: list[ColumnInfo] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    description: str | None = None

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "schema": self.schema,
            "columns": [c.to_dict() for c in self.columns],
            "primary_key": list(self.primary_key),
            "description": self.description,
        }


@dataclass
class ForeignKeyInfo:
    name: str
    table_schema: str
    table_name: str
    columns: list[str]
    referenced_schema: str
    referenced_table: str
    referenced_columns: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "table_schema": self.table_schema,
            "table_name": self.table_name,
            "columns": list(self.columns),
            "referenced_schema": self.referenced_schema,
            "referenced_table": self.referenced_table,
            "referenced_columns": list(self.referenced_columns),
        }


@dataclass
class DatabaseSchema:
    tables: list[TableInfo] = field(default_factory=list)
    foreign_keys: list[ForeignKeyInfo] = field(default_factory=list)

    @property
    def table_names(self) -> list[str]:
        return [t.name for t in self.tables]

    def find_table(self, name: str) -> TableInfo | None:
        for t in self.tables:
            if t.name == name:
                return t
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tables": [t.to_dict() for t in self.tables],
            "foreign_keys": [fk.to_dict() for fk in self.foreign_keys],
        }

    def to_llm_context(self) -> str:
        """Compact, authorization-safe schema description for the LLM.

        Only table/column names and relationships are exposed; no data or
        credentials.
        """
        lines: list[str] = ["TABLES"]
        for t in self.tables:
            pk = ", ".join(t.primary_key) if t.primary_key else ""
            pk_note = f" [PK: {pk}]" if pk else ""
            cols = ", ".join(f"{c.name} ({c.data_type})" for c in t.columns)
            lines.append(f"- {t.schema}.{t.name}{pk_note}: {cols}")
        if self.foreign_keys:
            lines.append("RELATIONSHIPS")
            for fk in self.foreign_keys:
                cols = ",".join(fk.columns)
                rcols = ",".join(fk.referenced_columns)
                lines.append(
                    f"- {fk.table_name}.{cols} -> "
                    f"{fk.referenced_table}.{rcols}"
                )
        return "\n".join(lines)


class SchemaDiscoveryService:
    """Discovers the schema of a database reachable through an engine."""

    def __init__(self, engine):
        self._engine = engine

    def discover(self, schema_name: str | None = None) -> DatabaseSchema:
        """Reflect tables, columns, PKs and FKs for the given schema.

        When schema_name is None the dialect default schema is used (e.g.
        public on PostgreSQL, main on SQLite).
        """
        inspector = inspect(self._engine)
        table_names = inspector.get_table_names(schema=schema_name) or []
        log.info("Discovered tables", extra={"extra_data": {"tables": table_names}})

        pk_map: dict[str, list[str]] = {}
        for tname in table_names:
            pk = inspector.get_pk_constraint(tname, schema=schema_name)
            pk_map[tname] = list(pk.get("constrained_columns", []))

        fk_map: dict[str, list[dict]] = {}
        for tname in table_names:
            fk_map[tname] = inspector.get_foreign_keys(tname, schema=schema_name)

        tables: list[TableInfo] = []
        for tname in table_names:
            columns: list[ColumnInfo] = []
            for col in inspector.get_columns(tname, schema=schema_name):
                columns.append(
                    ColumnInfo(
                        name=col["name"],
                        data_type=str(col["type"]),
                        is_nullable=bool(col.get("nullable", True)),
                        is_primary_key=col["name"] in pk_map.get(tname, []),
                        column_default=col.get("default"),
                    )
                )
            tables.append(
                TableInfo(
                    name=tname,
                    schema=schema_name or "public",
                    columns=columns,
                    primary_key=pk_map.get(tname, []),
                )
            )

        fks: list[ForeignKeyInfo] = []
        for tname, table_fks in fk_map.items():
            for fk in table_fks:
                ref_table = fk.get("referred_table")
                ref_columns = fk.get("referred_columns") or []
                ref_schema = fk.get("referred_schema") or schema_name or "public"
                fks.append(
                    ForeignKeyInfo(
                        name=fk.get("name") or f"{tname}_fk",
                        table_schema=schema_name or "public",
                        table_name=tname,
                        columns=list(fk.get("constrained_columns", [])),
                        referenced_schema=ref_schema,
                        referenced_table=ref_table,
                        referenced_columns=list(ref_columns),
                    )
                )

        return DatabaseSchema(tables=tables, foreign_keys=fks)

    def table_exists(self, table_name: str, schema_name: str | None = None) -> bool:
        inspector = inspect(self._engine)
        return table_name in (
            inspector.get_table_names(schema=schema_name) or []
        )

