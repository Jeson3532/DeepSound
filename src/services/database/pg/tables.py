from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func, String
from datetime import datetime


class Base(DeclarativeBase):
    ...


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(nullable=True, unique=True)
    hash_password: Mapped[str] = mapped_column(nullable=False, comment="Хеш пароля")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
