import time
from typing import Callable
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from pytest_mock import MockerFixture
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.schemas.transaction import Priority, TransactionInput
from src.config.config import settings
from src.db.database import Base
from src.db import crud
from .main import work_classify, callback_with_classifier


def create_transaction(tx_hash_char: str = "a") -> TransactionInput:
    return TransactionInput(
        tx_hash="0x" + tx_hash_char * 64,
        from_address="0x" + "a" * 40,
        to_address="0x" + "a" * 40,
        value_eth=1.0,
        gas_price_gwei=10,
        input_data="0x",
        timestamp=int(time.time()),
    )


# ------------------------------
# Unit Tests (no containers)
# ------------------------------


def test_work_classify_high_priority(mocker: MockerFixture):
    mock_classifier = mocker.Mock()
    risk_score = settings.risk_threshold + 0.01
    mock_classifier.predict.return_value = risk_score

    transaction = create_transaction()
    result = work_classify(mock_classifier, transaction)

    assert result.risk_score == risk_score
    assert result.priority == Priority.HIGH


def test_work_classify_low_priority(mocker: MockerFixture):
    mock_classifier = mocker.Mock()
    risk_score = settings.risk_threshold
    mock_classifier.predict.return_value = risk_score

    transaction = create_transaction()
    result = work_classify(mock_classifier, transaction)

    assert result.risk_score == risk_score
    assert result.priority == Priority.LOW


# ------------------------------
# Testcontainers - postgres
# ------------------------------


@pytest_asyncio.fixture
async def db_session():
    # Each test will spin up its own postgres container
    with PostgresContainer("postgres:16-alpine") as postgres:
        db_url = (
            f"postgresql+asyncpg://{postgres.username}:{postgres.password}"
            f"@{postgres.get_container_host_ip()}:{postgres.get_exposed_port(5432)}"
            f"/{postgres.dbname}"
        )
        engine = create_async_engine(db_url)
        session_factory = async_sessionmaker(engine)

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield session_factory

        await engine.dispose()


def create_mock_message(mocker: MockerFixture, transaction: TransactionInput):
    mock_message = mocker.Mock()
    mock_message.body = transaction.model_dump_json().encode()
    mock_message.ack = AsyncMock()
    mock_message.nack = AsyncMock()
    return mock_message


@pytest.mark.asyncio
async def test_callback_saves_high_risk_transaction(
    db_session: Callable, mocker: MockerFixture
):
    mock_classifier = mocker.Mock()
    risk = settings.risk_threshold + 0.01
    mock_classifier.predict.return_value = risk

    tx = create_transaction("a")
    mock_message = create_mock_message(mocker, tx)

    with patch("src.worker.main.SessionLocal", db_session):
        callback = callback_with_classifier(mock_classifier)
        await callback(mock_message)

    mock_message.ack.assert_called_once()
    mock_message.nack.assert_not_called()

    async with db_session() as session:
        transactions = await crud.get_transactions(session, offset=0, limit=10)
        assert len(transactions) == 1
        assert transactions[0].tx_hash == tx.tx_hash
        assert transactions[0].priority == "HIGH"
        assert transactions[0].risk_score == risk


@pytest.mark.asyncio
async def test_callback_does_not_save_low_risk_transaction(
    db_session: Callable, mocker: MockerFixture
):
    mock_classifier = mocker.Mock()
    mock_classifier.predict.return_value = settings.risk_threshold

    tx = create_transaction("b")
    mock_message = create_mock_message(mocker, tx)

    with patch("src.worker.main.SessionLocal", db_session):
        callback = callback_with_classifier(mock_classifier)
        await callback(mock_message)

    mock_message.ack.assert_called_once()
    mock_message.nack.assert_not_called()

    async with db_session() as session:
        transactions = await crud.get_transactions(session, offset=0, limit=10)
        assert len(transactions) == 0
