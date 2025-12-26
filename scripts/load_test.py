#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx>=0.28.1",
#     "aio-pika>=9.5.8",
#     "asyncpg>=0.31.0",
#     "python-dotenv>=1.0.0",
# ]
# ///
"""
Load testing script for the transaction API endpoint.

Usage:
    uv run scripts/load_test.py [OPTIONS]

Options:
    --url         Base URL of the API (default: http://localhost:8000)
    --requests    Total number of requests to send (default: 1000)
    --concurrency Number of concurrent requests (default: 20)
"""

import argparse
import asyncio
import os
import random
import time
from dataclasses import dataclass

import aio_pika
import asyncpg
import httpx
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Stats:
    total: int = 0
    success: int = 0
    failed: int = 0
    latencies: list[float] = None

    def __post_init__(self):
        self.latencies = []


def generate_transaction() -> dict:
    """Generate a random Ethereum transaction payload."""
    tx_hash = "0x" + "".join(random.choices("0123456789abcdef", k=64))
    from_addr = "0x" + "".join(random.choices("0123456789abcdef", k=40))
    to_addr = "0x" + "".join(random.choices("0123456789abcdef", k=40))

    return {
        "tx_hash": tx_hash,
        "from_address": from_addr,
        "to_address": to_addr,
        "value_eth": round(random.uniform(0, 100), 4),
        "gas_price_gwei": random.randint(1, 500),
        "input_data": "0x"
        + "".join(random.choices("0123456789abcdef", k=random.randint(0, 200))),
        "timestamp": int(time.time()) - random.randint(0, 86400),
    }


async def send_request(
    client: httpx.AsyncClient, url: str, stats: Stats, semaphore: asyncio.Semaphore
):
    """Send a single transaction request."""
    async with semaphore:
        payload = generate_transaction()
        start = time.perf_counter()
        try:
            response = await client.post(f"{url}/transactions/", json=payload)
            latency = (time.perf_counter() - start) * 1000

            stats.total += 1
            stats.latencies.append(latency)

            if response.status_code == 202:
                stats.success += 1
            else:
                stats.failed += 1
                print(f"Failed: {response.status_code} - {response.text}")

        except Exception as e:
            stats.total += 1
            stats.failed += 1
            print(f"Error: {e}")


async def run_load_test(url: str, num_requests: int, concurrency: int):
    """Run the load test."""
    print("Starting load test...")
    print(f"  URL: {url}")
    print(f"  Requests: {num_requests}")
    print(f"  Concurrency: {concurrency}")
    print()

    initial_db_count = await get_db_transaction_count()
    print(f"Initial DB transaction count: {initial_db_count}")
    print()

    stats = Stats()
    semaphore = asyncio.Semaphore(concurrency)

    # Both timers start at the same time
    start_time = time.perf_counter()

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            send_request(client, url, stats, semaphore) for _ in range(num_requests)
        ]
        await asyncio.gather(*tasks)

    api_time = time.perf_counter() - start_time

    # Calculate statistics
    print("=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Total requests:    {stats.total}")
    print(f"Successful (202):  {stats.success}")
    print(f"Failed:            {stats.failed}")
    print(f"Success rate:      {stats.success / stats.total * 100:.1f}%")
    print()
    print(f"API time:          {api_time:.2f}s")
    print(f"Requests/sec:      {stats.total / api_time:.2f}")
    print()

    if stats.latencies:
        sorted_latencies = sorted(stats.latencies)
        print("Latency (ms):")
        print(f"  Min:    {min(sorted_latencies):.2f}")
        print(f"  Max:    {max(sorted_latencies):.2f}")
        print(f"  Avg:    {sum(sorted_latencies) / len(sorted_latencies):.2f}")
        print(f"  p50:    {sorted_latencies[int(len(sorted_latencies) * 0.5)]:.2f}")
        print(f"  p95:    {sorted_latencies[int(len(sorted_latencies) * 0.95)]:.2f}")
        print(f"  p99:    {sorted_latencies[int(len(sorted_latencies) * 0.99)]:.2f}")

    await wait_for_queue_drain(start_time)
    total_time = time.perf_counter() - start_time

    final_db_count = await get_db_transaction_count()
    new_transactions = final_db_count - initial_db_count

    print()
    print("=" * 50)
    print("QUEUE & DATABASE STATS")
    print("=" * 50)
    print(f"Total time:            {total_time:.2f}s")
    print()
    print(f"Initial DB count:      {initial_db_count}")
    print(f"Final DB count:        {final_db_count}")
    print(f"New transactions:      {new_transactions}")
    print(f"High priority rate:    {new_transactions / num_requests * 100:.1f}%")


async def get_queue_message_count() -> int:
    """Get the number of messages in the transaction queue."""
    connection = await aio_pika.connect_robust(
        host=os.getenv("RABBITMQ_HOST", "localhost"),
        port=int(os.getenv("RABBITMQ_QUEUE_PORT", "5672")),
    )
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(
            name="transaction", durable=True, passive=True
        )
        return queue.declaration_result.message_count


async def get_db_transaction_count() -> int:
    """Get the number of transactions in the database."""
    conn = await asyncpg.connect(
        user=os.getenv("POSTGRES_USER", "test"),
        password=os.getenv("POSTGRES_PASSWORD", "test"),
        database=os.getenv("POSTGRES_DB", "test"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_EXTERNAL_PORT", "5432")),
    )
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM transactions")
        return count
    finally:
        await conn.close()


async def wait_for_queue_drain(start_time: float, poll_interval: float = 1.0):
    """Wait until the queue is empty."""
    print()
    print("Waiting for queue to drain...")

    while True:
        count = await get_queue_message_count()
        elapsed = time.perf_counter() - start_time
        print(
            f"\r  Queue messages: {count} (elapsed: {elapsed:.1f}s)", end="", flush=True
        )

        if count == 0:
            print()
            return

        await asyncio.sleep(poll_interval)


def main():
    api_port = os.getenv("API_PORT", "8000")
    default_url = f"http://localhost:{api_port}"

    parser = argparse.ArgumentParser(description="Load test the transaction API")
    parser.add_argument("--url", default=default_url, help="Base URL of the API")
    parser.add_argument(
        "--requests", type=int, default=1_000, help="Total number of requests"
    )
    parser.add_argument(
        "--concurrency", type=int, default=20, help="Number of concurrent requests"
    )

    args = parser.parse_args()

    asyncio.run(run_load_test(args.url, args.requests, args.concurrency))


if __name__ == "__main__":
    main()
