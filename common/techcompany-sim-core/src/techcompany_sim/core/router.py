"""
Router factory.

Given a list of EventStream instances, builds a FastAPI app with:

  GET  /<source>/events           — poll (since, limit)
  GET  /<source>/events/stream    — SSE push
  GET  /<source>/status           — health + stats
  GET  /health                    — overall health
  GET  /anomaly/status            — anomaly state across all sources
"""
from __future__ import annotations

import time
from typing import Sequence

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from techcompany_sim.core.stream import EventStream


def build_app(
    title: str,
    streams: Sequence[EventStream],
    use_case: str,
) -> FastAPI:
    app = FastAPI(
        title=title,
        description=f"Techcompany Hackathon Simulator — {use_case}",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    stream_map: dict[str, EventStream] = {s.source.name: s for s in streams}

    # ── Startup / shutdown ──────────────────────────────────────────────────

    @app.on_event("startup")
    async def _startup():
        for s in streams:
            s.start()

    @app.on_event("shutdown")
    async def _shutdown():
        for s in streams:
            s.stop()

    # ── Overall health ──────────────────────────────────────────────────────

    @app.get("/health", tags=["meta"])
    async def health():
        return {
            "status":    "ok",
            "use_case":  use_case,
            "sources":   list(stream_map.keys()),
            "server_time": time.time(),
        }

    # ── Anomaly status ──────────────────────────────────────────────────────

    @app.get("/anomaly/status", tags=["meta"])
    async def anomaly_status():
        return {
            s.source.name: {
                "anomaly_active": s.anomaly_active,
                "anomaly_delay_seconds": s.anomaly_delay,
                "intensity": s.intensity.value,
            }
            for s in streams
        }

    # ── Per-source routes ───────────────────────────────────────────────────

    for stream in streams:
        _register_source_routes(app, stream)

    return app


def _register_source_routes(app: FastAPI, stream: EventStream):
    name = stream.source.name
    tag  = name.replace("-", " ").title()

    # Poll endpoint
    @app.get(f"/{name}/events", tags=[tag])
    async def poll_events(
        since: float = Query(
            default=0.0,
            description="Unix timestamp — return events with timestamp > since",
        ),
        limit: int = Query(default=100, ge=1, le=1000),
    ):
        events = stream.events_since(since, limit=limit)
        return JSONResponse({
            "source":       name,
            "count":        len(events),
            "server_time":  time.time(),
            "anomaly_active": stream.anomaly_active,
            "events":       events,
        })

    # Latest shortcut (no timestamp needed)
    @app.get(f"/{name}/events/latest", tags=[tag])
    async def latest_events(
        limit: int = Query(default=50, ge=1, le=500),
    ):
        events = stream.latest(limit=limit)
        return JSONResponse({
            "source":      name,
            "count":       len(events),
            "server_time": time.time(),
            "events":      events,
        })

    # SSE stream endpoint
    @app.get(f"/{name}/events/stream", tags=[tag])
    async def sse_stream():
        async def generator():
            async for evt in stream.sse_generator():
                import json
                yield {"data": json.dumps(evt)}

        return EventSourceResponse(generator())

    # Source status
    @app.get(f"/{name}/status", tags=[tag])
    async def source_status():
        return {
            "source":         name,
            "buffered_events": len(stream.max_buffer),
            "anomaly_active": stream.anomaly_active,
            "anomaly_delay":  stream.anomaly_delay,
            "intensity":      stream.intensity.value,
            "tick_interval":  stream.tick_interval,
        }
