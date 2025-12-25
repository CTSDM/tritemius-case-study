import time

from pytest_mock import MockerFixture
from src.schemas.transaction import Priority, TransactionInput
from src.config.config import settings
from .main import work_classify


def create_transaction() -> TransactionInput:
    return TransactionInput(
        tx_hash="0x" + "a" * 64,
        from_address="0x" + "a" * 40,
        to_address="0x" + "a" * 40,
        value_eth=1.0,
        gas_price_gwei=10,
        input_data="0x",
        timestamp=int(time.time()),
    )


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
