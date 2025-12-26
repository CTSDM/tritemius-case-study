from src.db.models import Transaction
from src.schemas.transaction import TransactionInput, ClassificationResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def create_transaction(
    session: AsyncSession,
    tx_input: TransactionInput,
    classification: ClassificationResult,
) -> Transaction:
    transaction = Transaction(
        tx_hash=tx_input.tx_hash,
        from_address=tx_input.from_address,
        to_address=tx_input.to_address,
        value_eth=tx_input.value_eth,
        gas_price_gwei=tx_input.gas_price_gwei,
        input_data=tx_input.input_data,
        tx_timestamp=tx_input.timestamp,
        risk_score=classification.risk_score,
        priority=classification.priority,
        inference_time_ms=classification.inference_time_ms,
    )

    session.add(transaction)
    await session.commit()
    await session.refresh(transaction)
    return transaction


async def get_transactions(session: AsyncSession, offset: int, limit: int):
    result = await session.execute(select(Transaction).limit(limit).offset(offset))
    return result.scalars().all()
