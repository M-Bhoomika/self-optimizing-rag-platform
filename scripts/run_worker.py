#!/usr/bin/env python3
"""Run the background worker queue consumer."""

from __future__ import annotations

import argparse
import logging

from api.observability.logging import configure_logging
from api.worker.consumer import WorkerConsumer


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG platform background worker.")
    parser.add_argument("--once", action="store_true", help="Process at most one task and exit.")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    configure_logging(args.log_level)
    consumer = WorkerConsumer()

    if args.once:
        consumer.run_once()
        return

    consumer.run_forever()


if __name__ == "__main__":
    main()
