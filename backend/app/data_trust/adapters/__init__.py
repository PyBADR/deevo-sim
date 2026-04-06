from .base import BaseAdapter, AdapterFetchError, AdapterNormalizeError
from .government import GovernmentAdapter
from .real_estate import RealEstateAdapter

__all__ = [
    "BaseAdapter",
    "AdapterFetchError",
    "AdapterNormalizeError",
    "GovernmentAdapter",
    "RealEstateAdapter",
]
