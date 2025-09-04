import uuid
import os
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# Detect if we're using Postgres
USING_POSTGRES = os.getenv("DATABASE_URL", "").startswith("postgresql")

class GUID(TypeDecorator):
    """Platform-independent UUID type: uses PostgreSQL UUID or CHAR(36) for SQLite."""
    impl = CHAR if not USING_POSTGRES else PG_UUID

    def load_dialect_impl(self, dialect):
        if USING_POSTGRES:
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return str(value) if not USING_POSTGRES else value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(value)
