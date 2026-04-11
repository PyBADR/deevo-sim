"""Source Truth Registry repository — domain-specific queries."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.reality_tables import SourceTruthRegistryORM
from src.data_foundation.repositories.base import BaseRepository


class SourceTruthRepository(BaseRepository[SourceTruthRegistryORM]):
    model_class = SourceTruthRegistryORM
    pk_field = "source_id"

    async def find_active(
        self,
        *,
        source_type: Optional[str] = None,
        limit: int = 100,
    ) -> Sequence[SourceTruthRegistryORM]:
        stmt = select(self.model_class).where(self.model_class.is_active.is_(True))
        if source_type:
            stmt = stmt.where(self.model_class.source_type == source_type)
        stmt = stmt.order_by(self.model_class.source_name).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_reliability(
        self,
        reliability: str,
        *,
        limit: int = 100,
    ) -> Sequence[SourceTruthRegistryORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.reliability == reliability)
            .where(self.model_class.is_active.is_(True))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_failing(
        self,
        min_failures: int = 3,
    ) -> Sequence[SourceTruthRegistryORM]:
        """Sources with consecutive failures >= threshold."""
        stmt = (
            select(self.model_class)
            .where(self.model_class.consecutive_failures >= min_failures)
            .where(self.model_class.is_active.is_(True))
            .order_by(self.model_class.consecutive_failures.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_country(
        self,
        country: str,
        *,
        limit: int = 100,
    ) -> Sequence[SourceTruthRegistryORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.provider_country == country)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
