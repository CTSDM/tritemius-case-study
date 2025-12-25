from typing import Protocol
from src.schemas.transaction import TransactionInput


class BaseClassifier(Protocol):
    def predict(self, transaction: TransactionInput) -> float: ...
