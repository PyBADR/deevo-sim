"""Normalization Runs repository — domain-specific queries."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.reality_tables import NormalizationRunORM
from src.data_foundation.repositories.base import BaseRepository


class NormalizationRunRepository(BaseRepository[NormalizationRunORM]):
    model_class = NormalizationRunORM
    pk_field = "run_id"

    async def find_by_fetch_run(
        self,
        fetch_run_id: str,
    ) -> Sequence[NormalizationRunORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.fetch_run_id == fetch_run_id)
            .order_by(self.model_class.started_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_source(
        self,
        source_id: str,
        *,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> Sequence[NormalizationRunORM]:
        stmt = select(self.model_class).where(self.model_class.source_id == source_id)
        if status:
            stmt = stmt.where(self.model_class.status == status)
        stmt = stmt.order_by(self.model_class.started_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_failed(
        self,
        *,
        limit: int = 100,
    ) -> Sequence[NormalizationRunORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.status == "FAILED")
            .order_by(self.model_class.started_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_pending(
        self,
        *,
        limit: int = 200,
    ) -> Sequence[NormalizationRunORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.status == "PENDING")
            .order_by(self.model_class.created_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
