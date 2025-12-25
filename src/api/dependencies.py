from fastapi import Request
from aio_pika.pool import Pool


async def get_channel_pool(request: Request) -> Pool:
    return request.app.state.channel_pool
