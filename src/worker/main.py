import asyncio
import time
from typing import Awaitable, Callable
from pydantic import ValidationError
from asyncpg import PostgresError
from aio_pika.abc import AbstractIncomingMessage
from src.db import crud
from src.db.database import SessionLocal
from src.oracle.base import BaseClassifier
from src.oracle.dummy import DummyClassifier
from src.schemas.transaction import ClassificationResult, Priority, TransactionInput
from src.config.config import settings
from src.pubsub.pubsub import get_connection, QueueName


def work_classify(
    classifier: BaseClassifier, transaction: TransactionInput
) -> ClassificationResult:
    time_start = time.perf_counter()
    risk_score = classifier.predict(transaction)
    time_end = time.perf_counter()

    inference_time_ms = round((time_end - time_start) * 1_000)
    priority = Priority.HIGH if risk_score > settings.risk_threshold else Priority.LOW

    return ClassificationResult(
        risk_score=risk_score, inference_time_ms=inference_time_ms, priority=priority
    )


def get_classifier(dummy: bool) -> BaseClassifier:
    if dummy:
        return DummyClassifier()
    else:
        raise Exception("Real ML Oracle not implemented")


def callback_with_classifier(
    classifier: BaseClassifier,
) -> Callable[[AbstractIncomingMessage], Awaitable[None]]:
    async def callback(message: AbstractIncomingMessage) -> None:
        try:
            transaction = TransactionInput.model_validate_json(message.body)
            result = await asyncio.get_event_loop().run_in_executor(
                None, work_classify, classifier, transaction
            )

            if result.priority == Priority.HIGH:
                async with SessionLocal() as session:
                    await crud.create_transaction(session, transaction, result)
            await message.ack()

        except ValidationError as e:
            print(f"Error: could not parse the message into a transaction, {e}")
            await message.nack()
        except PostgresError as e:
            print(f"Error: could not save the transaction into the db, {e}")
            await message.nack()
        except Exception as e:
            print(f"Error: Unexpected error{e}")
            await message.nack()

    return callback


async def main() -> None:
    connection = await get_connection()
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=32)
        queue = await channel.declare_queue(name=QueueName.TRANSACTION, durable=True)
        classifier = get_classifier(settings.use_dummy)
        callback = callback_with_classifier(classifier)
        await queue.consume(callback)

        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
