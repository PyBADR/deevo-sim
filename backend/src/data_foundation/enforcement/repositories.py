"""Decision Enforcement — Typed async repositories.

Four repositories extending BaseRepository with domain-specific queries.
"""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.enforcement.orm_models import (
    ApprovalRequestORM,
    EnforcementDecisionORM,
    EnforcementPolicyORM,
    ExecutionGateResultORM,
)
from src.data_foundation.repositories.base import BaseRepository


class EnforcementPolicyRepository(BaseRepository[EnforcementPolicyORM]):
    model_class = EnforcementPolicyORM
    pk_field = "policy_id"

    async def find_active(self) -> Sequence[EnforcementPolicyORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_active == True)  # noqa: E712
            .order_by(self.model_class.priority.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_active_by_scope(
        self, scope_type: str, scope_ref: Optional[str] = None,
    ) -> Sequence[EnforcementPolicyORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_active == True)  # noqa: E712
            .where(self.model_class.scope_type == scope_type)
        )
        if scope_ref is not None:
            stmt = stmt.where(self.model_class.scope_ref == scope_ref)
        stmt = stmt.order_by(self.model_class.priority.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_type(self, policy_type: str) -> Sequence[EnforcementPolicyORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.policy_type == policy_type)
            .where(self.model_class.is_active == True)  # noqa: E712
            .order_by(self.model_class.priority.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class EnforcementDecisionRepository(BaseRepository[EnforcementDecisionORM]):
    model_class = EnforcementDecisionORM
    pk_field = "enforcement_id"

    async def list_for_decision(
        self, decision_log_id: str, *, limit: int = 50,
    ) -> Sequence[EnforcementDecisionORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.decision_log_id == decision_log_id)
            .order_by(self.model_class.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_for_decision(
        self, decision_log_id: str,
    ) -> Optional[EnforcementDecisionORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.decision_log_id == decision_log_id)
            .order_by(self.model_class.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_status(
        self, status: str, *, limit: int = 100,
    ) -> Sequence[EnforcementDecisionORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.enforcement_status == status)
            .order_by(self.model_class.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_by_rule(
        self, decision_rule_id: str, *, limit: int = 100,
    ) -> Sequence[EnforcementDecisionORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.decision_rule_id == decision_rule_id)
            .order_by(self.model_class.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ExecutionGateRepository(BaseRepository[ExecutionGateResultORM]):
    model_class = ExecutionGateResultORM
    pk_field = "gate_id"

    async def list_for_decision(
        self, decision_log_id: str,
    ) -> Sequence[ExecutionGateResultORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.decision_log_id == decision_log_id)
            .order_by(self.model_class.checked_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_for_enforcement(
        self, enforcement_id: str,
    ) -> Sequence[ExecutionGateResultORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.enforcement_id == enforcement_id)
            .order_by(self.model_class.checked_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ApprovalRequestRepository(BaseRepository[ApprovalRequestORM]):
    model_class = ApprovalRequestORM
    pk_field = "approval_id"

    async def get_pending_approvals(
        self, *, limit: int = 100,
    ) -> Sequence[ApprovalRequestORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.approval_status == "PENDING")
            .order_by(self.model_class.requested_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_for_decision(
        self, decision_log_id: str,
    ) -> Sequence[ApprovalRequestORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.decision_log_id == decision_log_id)
            .order_by(self.model_class.requested_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_for_enforcement(
        self, enforcement_id: str,
    ) -> Sequence[ApprovalRequestORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.enforcement_id == enforcement_id)
            .order_by(self.model_class.requested_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_by_status(
        self, status: str, *, limit: int = 100,
    ) -> Sequence[ApprovalRequestORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.approval_status == status)
            .order_by(self.model_class.requested_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
