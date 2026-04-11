"""Raw Source Records repository — domain-specific queries."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.reality_tables import RawSourceRecordORM
from src.data_foundation.repositories.base import BaseRepository


class RawSourceRecordRepository(BaseRepository[RawSourceRecordORM]):
    model_class = RawSourceRecordORM
    pk_field = "record_id"

    async def find_by_source(
        self,
        source_id: str,
        *,
        limit: int = 100,
    ) -> Sequence[RawSourceRecordORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.source_id == source_id)
            .order_by(self.model_class.fetch_timestamp.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_content_hash(
        self,
        content_hash: str,
    ) -> Optional[RawSourceRecordORM]:
        """Check if a payload with this hash already exists (dedup)."""
        stmt = select(self.model_class).where(self.model_class.content_hash == content_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_pending_normalization(
        self,
        *,
        source_id: Optional[str] = None,
        limit: int = 500,
    ) -> Sequence[RawSourceRecordORM]:
        """Records waiting to be normalized."""
        stmt = (
            select(self.model_class)
            .where(self.model_class.normalization_status == "PENDING")
            .where(self.model_class.is_duplicate.is_(False))
        )
        if source_id:
            stmt = stmt.where(self.model_class.source_id == source_id)
        stmt = stmt.order_by(self.model_class.fetch_timestamp).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_fetch_run(
        self,
        fetch_run_id: str,
    ) -> Sequence[RawSourceRecordORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.fetch_run_id == fetch_run_id)
            .order_by(self.model_class.fetch_timestamp)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
