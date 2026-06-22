"""Worker process that consumes tasks from the queue."""

from __future__ import annotations

import logging
import signal
import time
from typing import Optional

from .executor import execute_task
from .queue import TaskQueue, get_task_queue

logger = logging.getLogger(__name__)


class WorkerConsumer:
    """Poll the task queue and execute jobs until stopped."""

    def __init__(
        self,
        queue: Optional[TaskQueue] = None,
        poll_timeout_seconds: float = 5.0,
    ) -> None:
        self.queue = queue or get_task_queue()
        self.poll_timeout_seconds = poll_timeout_seconds
        self._running = False

    def run_once(self) -> bool:
        task = self.queue.dequeue(timeout_seconds=self.poll_timeout_seconds)
        if task is None:
            return False
        task_id = task.get("task_id", "unknown")
        try:
            result = execute_task(task)
            logger.info("Task %s finished: %s", task_id, result.get("status"))
        except Exception:
            logger.exception("Task %s failed", task_id)
        return True

    def run_forever(self) -> None:
        self._running = True

        def _stop(_signum, _frame) -> None:
            self._running = False

        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGTERM, _stop)

        logger.info("Worker started (queue backend=%s)", self.queue.backend)
        while self._running:
            processed = self.run_once()
            if not processed:
                time.sleep(0.1)
        logger.info("Worker stopped")
