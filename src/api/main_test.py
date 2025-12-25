import os
import pytest
import random
import time
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager
from src.schemas.transaction import TransactionInput, TransactionResponse
from testcontainers.rabbitmq import RabbitMqContainer
from src.config.config import settings

from .main import app


def create_random_hex_with_suffix(length: int) -> str:
    return "0x" + os.urandom(length).hex()


def create_transaction() -> TransactionInput:
    return TransactionInput(
        tx_hash=create_random_hex_with_suffix(32),
        from_address=create_random_hex_with_suffix(20),
        to_address=create_random_hex_with_suffix(20),
        value_eth=random.random(),
        gas_price_gwei=round(random.random() * 100),
        input_data=create_random_hex_with_suffix(100),
        timestamp=round(
            time.time() - random.random() * 5
        ),  # Simulated delay from transaction creation and arriving to the endpoint
    )


@pytest.mark.anyio
async def test_publish_message():
    # Setup rabbit testcontainer
    with RabbitMqContainer(
        image="rabbitmq:3.9.10",
    ) as rabbitmq:
        # Overwrite settings with the rabbitmq port and host
        settings.rabbitmq_host = rabbitmq.get_container_host_ip()
        settings.rabbitmq_queue_port = rabbitmq.get_exposed_port(5672)
        async with LifespanManager(app) as manager:
            async with AsyncClient(
                transport=ASGITransport(app=manager.app), base_url="http://test"
            ) as ac:
                tx_input = create_transaction()
                response = await ac.post(
                    "/transactions/", content=tx_input.model_dump_json().encode("utf-8")
                )

                assert response.status_code == 202
                assert TransactionResponse(**response.json()) == TransactionResponse(
                    tx_hash=tx_input.tx_hash
                )
