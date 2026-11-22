import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from src.config.database import Base, Session, engine
from src.middlewares.http import ErrorMiddleware, RequestIdMiddleware
from src.routes.api import router
from src.services.business import queue


MIGRATIONS = (
    'ALTER TABLE enrollments ADD COLUMN IF NOT EXISTS version integer NOT NULL DEFAULT 1',
    'ALTER TABLE linkage_reviews ADD COLUMN IF NOT EXISTS base_id integer',
)


@asynccontextmanager
async def lifespan(app):
    with engine.begin() as connection:
        for statement in MIGRATIONS:
            connection.execute(text(statement))
    Base.metadata.create_all(engine)
    if os.getenv('SEED_DEMO', 'true').lower() == 'true':
        try:
            from scripts.seed_demo import seed
            seed()
        except Exception:
            logging.exception('Demo seed failed')
    yield


app = FastAPI(title='禾埠木作·工坊课程联报核查', lifespan=lifespan)
app.add_middleware(ErrorMiddleware)
app.add_middleware(RequestIdMiddleware)
app.include_router(router)


@app.get('/health')
def health():
    with Session() as db:
        db.execute(text('SELECT 1'))
    queue.ping()
    return {'status': 'ok'}
