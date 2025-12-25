from pydantic import BaseModel, Field
from enum import Enum


class Priority(str, Enum):
    HIGH = "HIGH"
    LOW = "LOW"


class TransactionInput(BaseModel):
    tx_hash: str = Field(..., pattern=r"^0x[a-fA-F0-9]{64}$")
    from_address: str = Field(..., pattern=r"^0x[a-fA-F0-9]{40}$")
    to_address: str = Field(..., pattern=r"^0x[a-fA-F0-9]{40}$")
    value_eth: float = Field(..., ge=0)
    gas_price_gwei: int = Field(..., gt=0)
    input_data: str
    timestamp: int


class TransactionResponse(BaseModel):
    status: str = "accepted"
    tx_hash: str
    message: str = "Transaction queued for processing"


class ClassificationResult(BaseModel):
    risk_score: float = Field(..., ge=0, le=1)
    inference_time_ms: float = Field(..., gt=0)
    priority: Priority
