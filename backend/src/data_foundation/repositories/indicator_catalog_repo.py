"""Indicator Catalog repository — domain-specific queries."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.reality_tables import IndicatorCatalogORM
from src.data_foundation.repositories.base import BaseRepository


class IndicatorCatalogRepository(BaseRepository[IndicatorCatalogORM]):
    model_class = IndicatorCatalogORM
    pk_field = "indicator_id"

    async def find_by_code(
        self,
        indicator_code: str,
    ) -> Optional[IndicatorCatalogORM]:
        stmt = select(self.model_class).where(self.model_class.indicator_code == indicator_code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_category(
        self,
        category: str,
        *,
        sector: Optional[str] = None,
        active_only: bool = True,
        limit: int = 100,
    ) -> Sequence[IndicatorCatalogORM]:
        stmt = select(self.model_class).where(self.model_class.category == category)
        if sector:
            stmt = stmt.where(self.model_class.sector == sector)
        if active_only:
            stmt = stmt.where(self.model_class.is_active.is_(True))
        stmt = stmt.order_by(self.model_class.indicator_code).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_source(
        self,
        source_id: str,
    ) -> Sequence[IndicatorCatalogORM]:
        """Find indicators fed by a specific source."""
        stmt = (
            select(self.model_class)
            .where(self.model_class.primary_source_id == source_id)
            .where(self.model_class.is_active.is_(True))
            .order_by(self.model_class.indicator_code)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_with_alerts(self) -> Sequence[IndicatorCatalogORM]:
        """Indicators that have alert thresholds configured."""
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_active.is_(True))
            .where(
                (self.model_class.alert_threshold_low.is_not(None))
                | (self.model_class.alert_threshold_high.is_not(None))
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
