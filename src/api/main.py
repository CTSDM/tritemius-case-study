from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from src.pubsub.pubsub import QueueName, get_connection
from src.api.routes import transactions
from src.config.config import settings
from src.db.database import SessionLocal
from aio_pika import Channel
from aio_pika.pool import Pool


async def get_channel() -> Channel:
    async with app.state.connection_pool.acquire() as connection:
        return await connection.channel()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.connection_pool = Pool(get_connection, max_size=2)
    app.state.channel_pool = Pool(get_channel, max_size=settings.rabbitmq_max_channels)

    async with app.state.channel_pool.acquire() as channel:
        await channel.declare_queue(name=QueueName.TRANSACTION, durable=True)

    yield

    if app.state.channel_pool:
        await app.state.channel_pool.close()
    if app.state.connection_pool:
        await app.state.connection_pool.close()


app = FastAPI(lifespan=lifespan)

app.include_router(transactions.router, prefix="/transactions")


@app.get("/healthz")
async def healthz():
    health = {"status": "ok", "rabbitmq": "ok", "postgres": "ok"}

    try:
        async with app.state.channel_pool.acquire() as channel:
            await channel.declare_queue(
                name=QueueName.TRANSACTION, durable=True, passive=True
            )
    except Exception:
        health["rabbitmq"] = "error"
        health["status"] = "degraded"

    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        health["postgres"] = "error"
        health["status"] = "degraded"

    status_code = 200 if health["status"] == "ok" else 503
    return JSONResponse(content=health, status_code=status_code)
