"""FastAPI application entry point.

Wires together database, LLM service, and the API router.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import configure_services, router as api_router
from app.config.settings import settings
from app.core import configure_logging
from app.database.connection import Database
from app.services.llm import LLMService, create_provider

configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app_context: FastAPI):
    """Startup: create database + LLM service and register them."""
    if settings.database_url:
        db = Database(
            database_url=settings.database_url,
            readonly_database_url=settings.readonly_database_url,
        )
    else:
        db = Database(
            database_url="sqlite:///:memory:",
            readonly_database_url="sqlite:///:memory:",
        )

    provider = create_provider(
        provider_name=settings.llm_provider,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        temperature=settings.llm_temperature,
    )
    llm_service = LLMService(provider)
    configure_services(database=db, llm_service=llm_service)
    yield
    db.close()


app = FastAPI(title="NL to SQL Analytics Assistant", lifespan=lifespan)
app.include_router(api_router)


@app.get("/")
def root():
    return {"status": "ok"}
