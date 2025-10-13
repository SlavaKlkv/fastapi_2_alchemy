from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class RevokedToken(Base):
    """
    Таблица для хранения отозванных refresh-токенов.

    SQL:
    CREATE TABLE auth_revoked_tokens (
        jti TEXT PRIMARY KEY,
        revoked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """

    __tablename__ = 'auth_revoked_tokens'

    jti: Mapped[str] = mapped_column(String, primary_key=True)
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default='NOW()',
    )
