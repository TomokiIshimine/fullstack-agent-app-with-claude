"""Database configuration constants."""

# Connection pool defaults
DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10

# Cloud SQL IP types
CLOUD_SQL_IP_TYPE_PRIVATE = "PRIVATE"
CLOUD_SQL_IP_TYPE_PUBLIC = "PUBLIC"

__all__ = [
    "DEFAULT_POOL_SIZE",
    "DEFAULT_MAX_OVERFLOW",
    "CLOUD_SQL_IP_TYPE_PRIVATE",
    "CLOUD_SQL_IP_TYPE_PUBLIC",
]
