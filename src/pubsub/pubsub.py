import aio_pika
from enum import Enum
from typing import Tuple
from aio_pika import Message, DeliveryMode
from aio_pika.abc import AbstractRobustConnection
from aio_pika.pool import Pool
from src.config.config import settings
from src.schemas.transaction import TransactionInput


class QueueName(str, Enum):
    TRANSACTION = "transaction"


async def get_connection() -> AbstractRobustConnection:
    return await aio_pika.connect_robust(
        host=settings.rabbitmq_host, port=settings.rabbitmq_queue_port
    )


async def publish_transaction(
    channel_pool: Pool, tx: TransactionInput
) -> Tuple[str, bool]:
    try:
        async with channel_pool.acquire() as channel:
            message = Message(
                body=tx.model_dump_json().encode(encoding="utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
            )
            await channel.default_exchange.publish(
                message, routing_key=QueueName.TRANSACTION
            )

        return ("", True)

    except Exception as e:
        return (f"Error: {e}", False)
