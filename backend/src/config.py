"""
Impact Observatory | مرصد الأثر
Convenience re-export: src.config → src.core.config
"""
from src.core.config import settings  # noqa: F401

__all__ = ["settings"]
