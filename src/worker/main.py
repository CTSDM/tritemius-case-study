import time
from src.oracle.base import BaseClassifier
from src.schemas.transaction import ClassificationResult, Priority, TransactionInput
from src.config.config import settings


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
