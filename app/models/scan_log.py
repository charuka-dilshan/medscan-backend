from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.user_id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    scan_type = Column(
        String(50),
        nullable=False,
    )

    predicted_label = Column(
        String(255),
        nullable=True,
    )

    confidence = Column(
        Float,
        nullable=True,
    )

    allow_ai_processing = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    status = Column(
        String(50),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
    )

    user = relationship(
        "User",
        back_populates="scan_logs",
    )