"""signals.broadcaster — WebSocket connection manager for the Live Signal Layer.

Push-only.  Clients connect and receive events; they cannot write.
No SSE, no Redis, no batching, no queues.

The broadcaster has NO authority over the decision flow:
  - It does not call run_unified_pipeline().
  - It does not approve or reject seeds.
  - It does not mutate any seed or run state.

If a send fails, the dead connection is removed and the caller is unaffected.

Event shapes — every message: { "event": "<type>", "data": { ... } }

    signal.scored   — { signal_id, sector, event_type, signal_score, source, scored_at }
    seed.pending    — { seed_id, signal_id, sector, suggested_template_id,
                        suggested_severity, suggested_horizon_hours, rationale }
    seed.approved   — { seed_id, run_id, reviewed_by, sector, suggested_template_id }
    seed.rejected   — { seed_id, reviewed_by, sector, reason }
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and fan-out broadcast."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        logger.debug("ws.connect total=%d", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        logger.debug("ws.disconnect total=%d", len(self._connections))

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    async def broadcast(self, event: str, data: dict[str, Any]) -> tuple[int, int]:
        """Fan-out a JSON event to all connected clients.

        Returns (delivered, failed) counts.  Dead connections are removed.
        Failures are logged at WARNING level so they appear in production logs.
        """
        if not self._connections:
            return 0, 0

        payload  = json.dumps({"event": event, "data": data}, default=str)
        dead:     list[WebSocket] = []
        delivered = 0

        for ws in list(self._connections):
            try:
                await ws.send_text(payload)
                delivered += 1
            except Exception as exc:
                logger.warning(
                    "ws.broadcast failed event=%s — dropping dead connection: %s",
                    event, exc,
                )
                dead.append(ws)

        for ws in dead:
            self._connections.discard(ws)

        failed = len(dead)
        if failed:
            logger.info(
                "ws.broadcast event=%s delivered=%d failed=%d total_remaining=%d",
                event, delivered, failed, len(self._connections),
            )
        return delivered, failed


# ── Module-level singleton ────────────────────────────────────────────────────

manager = ConnectionManager()


# ── Typed broadcast helpers ───────────────────────────────────────────────────

async def broadcast_signal_scored(scored: Any) -> None:
    try:
        await manager.broadcast("signal.scored", {
            "signal_id":    scored.signal.signal_id,
            "sector":       scored.signal.sector.value,
            "event_type":   scored.signal.event_type,
            "signal_score": scored.signal_score,
            "source":       scored.signal.source.value,
            "scored_at":    scored.scored_at.isoformat(),
        })
    except Exception as exc:
        logger.warning("broadcast_signal_scored failed: %s", exc)


async def broadcast_seed_pending(seed: Any) -> None:
    try:
        await manager.broadcast("seed.pending", {
            "seed_id":                 seed.seed_id,
            "signal_id":               seed.signal_id,
            "sector":                  seed.sector.value,
            "suggested_template_id":   seed.suggested_template_id,
            "suggested_severity":      seed.suggested_severity,
            "suggested_horizon_hours": seed.suggested_horizon_hours,
            "rationale":               seed.rationale,
        })
    except Exception as exc:
        logger.warning("broadcast_seed_pending failed: %s", exc)


async def broadcast_seed_approved(seed: Any, run_id: str) -> None:
    try:
        await manager.broadcast("seed.approved", {
            "seed_id":               seed.seed_id,
            "run_id":                run_id,
            "reviewed_by":           seed.reviewed_by,
            "sector":                seed.sector.value,
            "suggested_template_id": seed.suggested_template_id,
        })
    except Exception as exc:
        logger.warning("broadcast_seed_approved failed: %s", exc)


async def broadcast_seed_rejected(seed: Any) -> None:
    try:
        await manager.broadcast("seed.rejected", {
            "seed_id":     seed.seed_id,
            "reviewed_by": seed.reviewed_by,
            "sector":      seed.sector.value,
            "reason":      seed.review_reason,
        })
    except Exception as exc:
        logger.warning("broadcast_seed_rejected failed: %s", exc)
