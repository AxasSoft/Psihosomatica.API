import logging
import os


from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import settings
from logs.config import setup_logging, logger

ENV = os.getenv("ENVIRONMENT", "development")

setup_logging(ENV)

logger.info("Starting application initialization")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_STR}/openapi.json",
)

BACKEND_CORS_ORIGINS = ["*"]
# if settings.BACKEND_CORS_ORIGINS:
if BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_origins=[str(origin) for origin in BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_STR)

from app import errors
