"""Source Fetch Runs repository — domain-specific queries."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.reality_tables import SourceFetchRunORM
from src.data_foundation.repositories.base import BaseRepository


class SourceFetchRunRepository(BaseRepository[SourceFetchRunORM]):
    model_class = SourceFetchRunORM
    pk_field = "run_id"

    async def find_by_source(
        self,
        source_id: str,
        *,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> Sequence[SourceFetchRunORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.source_id == source_id)
        )
        if status:
            stmt = stmt.where(self.model_class.status == status)
        stmt = stmt.order_by(self.model_class.fetch_timestamp.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_latest_by_source(
        self,
        source_id: str,
    ) -> Optional[SourceFetchRunORM]:
        """Get the most recent fetch run for a source."""
        stmt = (
            select(self.model_class)
            .where(self.model_class.source_id == source_id)
            .order_by(self.model_class.fetch_timestamp.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_failed(
        self,
        *,
        limit: int = 100,
    ) -> Sequence[SourceFetchRunORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.status == "FAILED")
            .order_by(self.model_class.fetch_timestamp.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_running(self) -> Sequence[SourceFetchRunORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.status.in_(["PENDING", "RUNNING"]))
            .order_by(self.model_class.started_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
