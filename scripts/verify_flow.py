#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx>=0.28.1",
#     "asyncpg>=0.31.0",
#     "python-dotenv>=1.0.0",
# ]
# ///
"""
Verification script: sends 20 transactions, waits, then queries DB for high-risk matches.
Usage: uv run scripts/verify_flow.py
"""

import asyncio
import os
import random
import time

import asyncpg
import httpx
from dotenv import load_dotenv

load_dotenv()

API_PORT = os.getenv("API_PORT", "8000")
API_URL = "http://localhost:" + API_PORT


def generate_transaction() -> dict:
    tx_hash = "0x" + "".join(random.choices("0123456789abcdef", k=64))
    from_addr = "0x" + "".join(random.choices("0123456789abcdef", k=40))
    to_addr = "0x" + "".join(random.choices("0123456789abcdef", k=40))

    return {
        "tx_hash": tx_hash,
        "from_address": from_addr,
        "to_address": to_addr,
        "value_eth": round(random.uniform(0, 100), 4),
        "gas_price_gwei": random.randint(1, 500),
        "input_data": "0x",
        "timestamp": int(time.time()),
    }


async def main():
    num_requests = 20
    wait_seconds = 3

    # Generate and send transactions
    transactions = [generate_transaction() for _ in range(num_requests)]
    sent_hashes = [tx["tx_hash"] for tx in transactions]

    print(f"Sending {num_requests} transactions to {API_URL}...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        for tx in transactions:
            response = await client.post(f"{API_URL}/transactions/", json=tx)
            status = "ok" if response.status_code == 202 else "fail"
            print(f"  {tx['tx_hash'][:18]}... -> {status}")

    print(f"\nWaiting {wait_seconds} seconds for processing...")
    await asyncio.sleep(wait_seconds)

    # Query database for matching transactions
    print("\nQuerying database for high-risk transactions...\n")

    conn = await asyncpg.connect(
        user=os.getenv("POSTGRES_USER", "myuser"),
        password=os.getenv("POSTGRES_PASSWORD", "mypassword"),
        database=os.getenv("POSTGRES_DB", "transactions"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_EXTERNAL_PORT", "5454")),
    )

    try:
        rows = await conn.fetch(
            """
            SELECT tx_hash, risk_score, inference_time_ms
            FROM transactions
            WHERE tx_hash = ANY($1)
            ORDER BY risk_score DESC
            """,
            sent_hashes,
        )

        if rows:
            print(f"{'TX HASH':<68} {'RISK':>6} {'TIME':>6}")
            print("-" * 82)
            for row in rows:
                print(
                    f"{row['tx_hash']}  {row['risk_score']:>5.3f}  {row['inference_time_ms']:>4}ms"
                )
            print("-" * 82)
            print(f"Found {len(rows)}/{num_requests} transactions (risk_score > 0.8)")
        else:
            print("No high-risk transactions found in database.")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
