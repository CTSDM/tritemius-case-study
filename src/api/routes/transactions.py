from fastapi import APIRouter, Depends, HTTPException
from aio_pika.pool import Pool
from src.api.dependencies import get_channel_pool
from src.schemas.transaction import TransactionInput, TransactionResponse
from src.pubsub.pubsub import publish_transaction

router = APIRouter()


@router.post("/", status_code=202, response_model=TransactionResponse)
async def process_transaction(
    tx_input: TransactionInput, channel_pool: Pool = Depends(get_channel_pool)
):
    msg, success = await publish_transaction(channel_pool, tx_input)
    if not success:
        raise HTTPException(status_code=503, detail=msg)
    return TransactionResponse(tx_hash=tx_input.tx_hash)
