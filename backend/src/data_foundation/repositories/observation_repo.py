"""Canonical Observations repository — domain-specific queries."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.reality_tables import CanonicalObservationORM
from src.data_foundation.repositories.base import BaseRepository


class CanonicalObservationRepository(BaseRepository[CanonicalObservationORM]):
    model_class = CanonicalObservationORM
    pk_field = "observation_id"

    async def find_by_indicator(
        self,
        indicator_code: str,
        *,
        country: Optional[str] = None,
        limit: int = 100,
    ) -> Sequence[CanonicalObservationORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.indicator_code == indicator_code)
        )
        if country:
            stmt = stmt.where(self.model_class.country == country)
        stmt = stmt.order_by(self.model_class.period_start.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_latest_by_indicator(
        self,
        indicator_code: str,
        country: str,
    ) -> Optional[CanonicalObservationORM]:
        """Get the most recent observation for an indicator+country."""
        stmt = (
            select(self.model_class)
            .where(self.model_class.indicator_code == indicator_code)
            .where(self.model_class.country == country)
            .order_by(self.model_class.period_start.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_country(
        self,
        country: str,
        *,
        limit: int = 200,
    ) -> Sequence[CanonicalObservationORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.country == country)
            .order_by(self.model_class.observation_date.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_source(
        self,
        source_id: str,
        *,
        limit: int = 200,
    ) -> Sequence[CanonicalObservationORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.source_id == source_id)
            .order_by(self.model_class.fetch_timestamp.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_provisional(
        self,
        *,
        country: Optional[str] = None,
        limit: int = 100,
    ) -> Sequence[CanonicalObservationORM]:
        """Observations still marked as provisional (pending revision)."""
        stmt = select(self.model_class).where(self.model_class.is_provisional.is_(True))
        if country:
            stmt = stmt.where(self.model_class.country == country)
        stmt = stmt.order_by(self.model_class.observation_date.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
