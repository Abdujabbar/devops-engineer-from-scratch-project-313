import os
import logging
from fastapi import FastAPI
from shortener.middlewares.secret_headers_process_time import add_process_time_header
from shortener.handlers.healthchecker import router as healthchecker_router
from shortener.handlers.links import router as links_router
from shortener.db import init_db
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk

from dotenv import load_dotenv

load_dotenv()

SENTRY_DNS = os.getenv("SENTRY_DNS")

sentry_sdk.init(
    dsn=SENTRY_DNS,
    traces_sample_rate=1.0,
    send_default_pii=True,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.middleware("http")(add_process_time_header)

app.include_router(healthchecker_router)
app.include_router(links_router)


@app.on_event("startup")
def on_startup():
    init_db()
