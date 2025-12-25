import random
import time
from src.schemas.transaction import TransactionInput
from src.config.config import settings


class DummyClassifier:
    def predict(self, transaction: TransactionInput) -> float:
        time.sleep(
            random.uniform(
                settings.calculation_time_min_ms, settings.calculation_time_max_ms
            )
        )
        return random.uniform(0, 1)
