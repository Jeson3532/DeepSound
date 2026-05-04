from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func, String, Integer, String, Float, Boolean, DateTime, ForeignKey, func
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


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = mapped_column(Integer, primary_key=True, index=True)
    username = mapped_column(String, nullable=False, index=True)
    file_name = mapped_column(String, nullable=False)
    label = mapped_column(Integer, nullable=False)
    confidence = mapped_column(Float, nullable=False)
    is_defect = mapped_column(Boolean, nullable=False)
    sample_rate = mapped_column(Integer, nullable=True)
    duration_sec = mapped_column(Float, nullable=True)
    rms_level = mapped_column(Float, nullable=True)
    peak_level = mapped_column(Float, nullable=True)
    spectral_bandwidth = mapped_column(Float, nullable=True)
    spectral_rolloff = mapped_column(Float, nullable=True)
    zcr = mapped_column(Float, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
