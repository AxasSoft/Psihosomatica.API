from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base_model import Base

class Settings(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    price_premium: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")