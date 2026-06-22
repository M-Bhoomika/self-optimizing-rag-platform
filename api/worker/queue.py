"""Redis-backed task queue with in-memory fallback."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, Optional

logger = logging.getLogger(__name__)

QUEUE_KEY = "rag:worker:tasks"


@dataclass
class EnqueuedTask:
    task_id: str
    payload: Dict[str, Any]


class TaskQueue:
    """Push and consume background tasks."""

    def __init__(self, redis_url: Optional[str] = None, queue_key: str = QUEUE_KEY) -> None:
        self.queue_key = queue_key
        self._redis = None
        self._memory: Deque[str] = deque()
        self._lock = threading.Lock()
        url = redis_url if redis_url is not None else os.getenv("REDIS_URL")
        if url:
            try:
                import redis  # type: ignore

                self._redis = redis.Redis.from_url(url, decode_responses=True)
                self._redis.ping()
            except Exception as exc:
                logger.info("TaskQueue using in-memory fallback: %s", exc)
                self._redis = None

    @property
    def backend(self) -> str:
        return "redis" if self._redis is not None else "memory"

    def enqueue(self, task_type: str, payload: Dict[str, Any]) -> EnqueuedTask:
        task_id = str(uuid.uuid4())
        body = json.dumps({"task_id": task_id, "type": task_type, "payload": payload})
        if self._redis is not None:
            self._redis.lpush(self.queue_key, body)
        else:
            with self._lock:
                self._memory.append(body)
        return EnqueuedTask(task_id=task_id, payload={"type": task_type, **payload})

    def dequeue(self, timeout_seconds: float = 5.0) -> Optional[Dict[str, Any]]:
        if self._redis is not None:
            item = self._redis.brpop(self.queue_key, timeout=max(1, int(timeout_seconds)))
            if item is None:
                return None
            _, raw = item
            return json.loads(raw)

        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            with self._lock:
                if self._memory:
                    return json.loads(self._memory.popleft())
            time.sleep(0.05)
        return None

    def depth(self) -> int:
        if self._redis is not None:
            return int(self._redis.llen(self.queue_key))
        with self._lock:
            return len(self._memory)


_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    global _queue
    if _queue is None:
        _queue = TaskQueue()
    return _queue
