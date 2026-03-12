import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.utils.datetime import utcnow
from app.models.base_model import Base


class Payment(Base):

    uuid = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True
        )
    created = Column(DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    user_id = Column(
        Integer(), ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    description = Column(String, nullable=True)
    amount = Column(Integer, nullable=False, server_default="1")
    pay_link = Column(String, nullable=True)
    payment_id = Column(String, nullable=True)
    is_pay = Column(Boolean, server_default="false")
    pay_date = Column(DateTime(timezone=True), nullable=True, index=True)
    ofd_url = Column(String, nullable=True)
    return_url = Column(String, nullable=True)
    os = Column(String, nullable=True)

    user = relationship("User", lazy='joined')
