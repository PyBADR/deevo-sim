"""
Impact Observatory | مرصد الأثر — Backend Decision Authority Layer (DAL)

Backend-native authority lifecycle persistence, enforcement, and audit.
Sits ON TOP of existing OperatorDecision — never mutates its domain model.

Submodules:
  models  — SQLAlchemy ORM table definitions (shares signals.store engine)
  engine  — Transition engine: guards, atomic state+event writes, hash chain
"""
