"""
Core event stream engine.

Each signal source registers a generator function that produces one event
per tick. The EventStream buffers events internally; agents poll via the
REST endpoints or subscribe via SSE.
"""
from __future__ import annotations

import asyncio
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Deque


class AnomalyIntensity(str, Enum):
    SUBTLE   = "subtle"
    MODERATE = "moderate"
    OBVIOUS  = "obvious"


@dataclass
class Event:
    id: str
    source: str
    timestamp: float
    data: dict[str, Any]
    is_anomaly: bool = False

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "source":     self.source,
            "timestamp":  self.timestamp,
            "data":       self.data,
            "is_anomaly": self.is_anomaly,   # visible to teams for verification
        }


# Type alias for generator functions
GeneratorFn = Callable[["StreamContext"], dict[str, Any] | None]


@dataclass
class StreamContext:
    """Passed to every generator function each tick."""
    tick:        int
    elapsed:     float          # seconds since stream start
    anomaly_active: bool
    intensity:   AnomalyIntensity
    rng:         Any            # numpy-free: use random.Random seeded instance


@dataclass
class SignalSource:
    name:        str
    normal_gen:  GeneratorFn
    anomaly_gen: GeneratorFn
    tick_rate:   int = 1        # emit every N ticks (1 = every tick)


class EventStream:
    """
    Manages one named signal source: generates events on a background task,
    buffers the last `max_buffer` events, and lets callers poll by timestamp.
    """

    def __init__(
        self,
        source: SignalSource,
        tick_interval: float,
        anomaly_delay: float,
        intensity: AnomalyIntensity,
        seed: int,
        max_buffer: int = 5_000,
        anomaly_duration: float = 0.0,
        anomaly_cycle_interval: float = 0.0,
    ):
        self.source                 = source
        self.tick_interval          = tick_interval
        self.anomaly_delay          = anomaly_delay
        self.intensity              = intensity
        self.anomaly_duration       = anomaly_duration
        self.anomaly_cycle_interval = anomaly_cycle_interval
        self.max_buffer: Deque[Event] = deque(maxlen=max_buffer)
        self._start_time: float | None = None
        self._tick         = 0
        self._task: asyncio.Task | None = None

        import random
        self._rng = random.Random(seed)

    @property
    def anomaly_active(self) -> bool:
        if self._start_time is None:
            return False
        elapsed = time.time() - self._start_time
        if elapsed < self.anomaly_delay:
            return False
        if self.anomaly_duration <= 0.0:          # permanent latch — default / backward compat
            return True
        cycle_len = self.anomaly_duration + self.anomaly_cycle_interval
        phase = (elapsed - self.anomaly_delay) % cycle_len
        return phase < self.anomaly_duration

    def events_since(self, since: float, limit: int = 200) -> list[dict]:
        results = [e for e in self.max_buffer if e.timestamp > since]
        return [e.to_dict() for e in results[-limit:]]

    def latest(self, limit: int = 50) -> list[dict]:
        items = list(self.max_buffer)[-limit:]
        return [e.to_dict() for e in items]

    async def _run(self):
        self._start_time = time.time()
        while True:
            await asyncio.sleep(self.tick_interval)
            self._tick += 1

            if self._tick % self.source.tick_rate != 0:
                continue

            ctx = StreamContext(
                tick=self._tick,
                elapsed=time.time() - self._start_time,
                anomaly_active=self.anomaly_active,
                intensity=self.intensity,
                rng=self._rng,
            )

            gen = self.source.anomaly_gen if self.anomaly_active else self.source.normal_gen
            data = gen(ctx)
            if data is None:
                continue

            event = Event(
                id=str(uuid.uuid4()),
                source=self.source.name,
                timestamp=time.time(),
                data=data,
                is_anomaly=self.anomaly_active,
            )
            self.max_buffer.append(event)

    def start(self):
        self._task = asyncio.create_task(self._run())

    def stop(self):
        if self._task:
            self._task.cancel()

    async def sse_generator(self):
        """Async generator for Server-Sent Events — yields new events as they arrive."""
        last_ts = time.time()
        while True:
            await asyncio.sleep(self.tick_interval)
            new = self.events_since(last_ts, limit=50)
            for evt in new:
                last_ts = evt["timestamp"]
                yield evt
