"""Tests for the HTTP API (F-001, F-007, F-008)."""
from __future__ import annotations


def test_health_endpoint(api_client):
    resp = api_client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "customers" in data["schema_tables"]


def test_query_endpoint_simple(api_client):
    resp = api_client.post("/api/query", json={"question": "How many customers do we have?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["question"] == "How many customers do we have?"
    assert "SELECT" in data["sql"]
    assert data["status"] == "success"
    assert data["results"] is not None
    assert data["explanation"]


def test_query_endpoint_top_products(api_client):
    resp = api_client.post("/api/query", json={"question": "Which product sold the most?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "GROUP BY" in data["sql"].upper()


def test_query_endpoint_empty_question(api_client):
    resp = api_client.post("/api/query", json={"question": ""})
    assert resp.status_code == 422


def test_query_endpoint_missing_question(api_client):
    resp = api_client.post("/api/query", json={})
    assert resp.status_code == 422


def test_query_endpoint_too_long(api_client):
    resp = api_client.post("/api/query", json={"question": "x" * 501})
    assert resp.status_code == 422


def test_root_endpoint(api_client):
    resp = api_client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_query_endpoint_includes_sql_and_explanation(api_client):
    resp = api_client.post("/api/query", json={"question": "How many customers do we have?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "sql" in data
    assert "explanation" in data
    assert "results" in data