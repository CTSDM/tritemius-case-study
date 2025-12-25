from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.pubsub.pubsub import QueueName, get_connection
from src.api.routes import transactions
from src.config.config import settings
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
