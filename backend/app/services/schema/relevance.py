"""Relevant schema selection.

Given a user question and a fully-discovered schema, select the subset of
tables (and the relationships between them) that are likely needed to answer
the question. Only the relevant subset is forwarded to the SQL-generation LLM
so that large schemas do not blow up the prompt.

Selection is heuristic but schema-driven:
  1. Token matching against table names and column names.
  2. A small, documented map of analytics "metric" keywords to fact tables
     (e.g. "revenue" implies the order-line fact table). This is a pragmatic
     MVP heuristic and is easily replaced by an LLM-based selector.
  3. Join closure: include every table that lies on a foreign-key path between
     two directly-matched tables, so the LLM receives a joinable subgraph.
"""
from __future__ import annotations

import re
from itertools import combinations
from typing import Iterable

from app.core import get_logger
from app.services.schema.discovery import DatabaseSchema, TableInfo

log = get_logger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Analytics terms that imply fact/line-item tables rather than a literal
# column or table name. Mapping values must be real table names in the schema.
METRIC_KEYWORDS_TO_FACT_TABLES = {
    "revenue", "sales", "income", "amount", "total", "earned", "profit",
    "sold", "spent", "most", "top", "best", "highest", "lowest", "average",
    "avg", "sum", "count",
}

# Table names that hold per-order / per-line facts. Added to the candidate set
# when any metric keyword is detected.
FACT_TABLES = {"order_items", "orders"}


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _table_token_set(table: TableInfo) -> set[str]:
    tokens = set(_TOKEN_RE.findall(table.name.lower()))
    for col in table.columns:
        tokens |= set(_TOKEN_RE.findall(col.name.lower()))
    return tokens


def _build_undirected_graph(schema: DatabaseSchema) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {t.name: set() for t in schema.tables}
    for fk in schema.foreign_keys:
        if fk.table_name in graph and fk.referenced_table in graph:
            graph[fk.table_name].add(fk.referenced_table)
            graph[fk.referenced_table].add(fk.table_name)
    return graph


def _shortest_path(graph: dict[str, set[str]], start: str, goal: str) -> list[str]:
    """BFS shortest path; returns [start, ..., goal] or [] if unreachable."""
    if start == goal:
        return [start]
    queue: list[tuple[str, list[str]]] = [(start, [start])]
    seen: set[str] = {start}
    while queue:
        node, path = queue.pop(0)
        for nxt in graph.get(node, ()):  # noqa: PERF401
            if nxt == goal:
                return path + [nxt]
            if nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, path + [nxt]))
    return []


class RelevanceSelector:
    """Selects the relevant sub-schema for a natural-language question."""

    def __init__(self, schema: DatabaseSchema):
        self._schema = schema
        self._graph = _build_undirected_graph(schema)

    def select(self, question: str) -> DatabaseSchema:
        question_tokens = set(_tokenize(question))
        metric_hit = bool(question_tokens & METRIC_KEYWORDS_TO_FACT_TABLES)

        directly_matched: set[str] = set()
        for table in self._schema.tables:
            table_tokens = _table_token_set(table)
            if table_tokens & question_tokens:
                directly_matched.add(table.name)

        # Metric questions need the fact tables even if no column name matches.
        if metric_hit:
            directly_matched |= {t.name for t in self._schema.tables} & FACT_TABLES

        # Fallback: if nothing matched, return the whole schema so the system
        # can still attempt an answer rather than silently failing.
        if not directly_matched:
            log.warning("No schema tokens matched the question; returning full schema")
            return self._subschema(self._schema.table_names)

        # Join closure: include every table on a shortest FK path between two
        # directly-matched tables, so the LLM receives a joinable subgraph.
        closure: set[str] = set(directly_matched)
        for a, b in combinations(directly_matched, 2):
            path = _shortest_path(self._graph, a, b)
            closure.update(path)

        ordered = [t.name for t in self._schema.tables if t.name in closure]
        log.info("Selected relevant tables", extra={"extra_data": {
            "question": question, "tables": ordered,
            "matched": sorted(directly_matched), "closure": sorted(closure)}})
        return self._subschema(ordered)

    def _subschema(self, table_names: Iterable[str]) -> DatabaseSchema:
        wanted = set(table_names)
        tables = [t for t in self._schema.tables if t.name in wanted]
        fks = [fk for fk in self._schema.foreign_keys
               if fk.table_name in wanted and fk.referenced_table in wanted]
        return DatabaseSchema(tables=tables, foreign_keys=fks)
