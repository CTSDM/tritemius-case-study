#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "psycopg2-binary>=2.9.11",
# ]
# ///
"""Query the database for transaction statistics."""

import argparse
import os

import psycopg2


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_EXTERNAL_PORT", "5454"),
        user=os.getenv("POSTGRES_USER", "myuser"),
        password=os.getenv("POSTGRES_PASSWORD", "mypassword"),
        dbname=os.getenv("POSTGRES_DB", "transactions"),
    )


def get_stats(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM transactions")
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM transactions WHERE priority = 'HIGH'")
        high_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM transactions WHERE priority = 'LOW'")
        low_count = cur.fetchone()[0]

        cur.execute("SELECT AVG(risk_score) FROM transactions")
        avg_risk = cur.fetchone()[0]

        cur.execute("SELECT AVG(inference_time_ms) FROM transactions")
        avg_inference = cur.fetchone()[0]

        return {
            "total": total or 0,
            "high_priority": high_count or 0,
            "low_priority": low_count or 0,
            "avg_risk_score": round(avg_risk, 4) if avg_risk else 0,
            "avg_inference_time_ms": round(avg_inference, 2) if avg_inference else 0,
        }


def get_recent_transactions(conn, limit: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tx_hash, risk_score, priority, inference_time_ms
            FROM transactions
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall()


def main(show_recent: int = 0):
    conn = get_connection()

    try:
        stats = get_stats(conn)

        print("=" * 50)
        print("TRANSACTION STATISTICS")
        print("=" * 50)
        print(f"Total transactions:      {stats['total']}")
        print(f"High priority:           {stats['high_priority']}")
        print(f"Low priority:            {stats['low_priority']}")
        print(f"Avg risk score:          {stats['avg_risk_score']}")
        print(f"Avg inference time (ms): {stats['avg_inference_time_ms']}")

        if show_recent > 0:
            print()
            print(f"RECENT TRANSACTIONS (last {show_recent})")
            print("=" * 50)
            transactions = get_recent_transactions(conn, show_recent)
            for tx_hash, risk_score, priority, inference_time in transactions:
                print(
                    f"{tx_hash[:16]}... | "
                    f"risk: {risk_score:.3f} | "
                    f"priority: {priority} | "
                    f"inference: {inference_time}ms"
                )
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query transaction database")
    parser.add_argument(
        "--recent",
        type=int,
        default=0,
        help="Show N most recent transactions",
    )
    args = parser.parse_args()

    main(show_recent=args.recent)
