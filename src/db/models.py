from datetime import datetime

from sqlalchemy import DateTime, Integer, Float, Text, text
from sqlalchemy.orm import Mapped, mapped_column
from src.db.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, init=False)
    tx_hash: Mapped[str] = mapped_column(Text)
    from_address: Mapped[str] = mapped_column(Text)
    to_address: Mapped[str] = mapped_column(Text)
    value_eth: Mapped[float] = mapped_column(Float)
    gas_price_gwei: Mapped[int] = mapped_column(Integer)
    input_data: Mapped[str] = mapped_column(Text)
    tx_timestamp: Mapped[int] = mapped_column(Integer)

    risk_score: Mapped[float] = mapped_column(Float)
    priority: Mapped[str] = mapped_column(Text)
    inference_time_ms: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("timezone('utc', now())"), init=False
    )
