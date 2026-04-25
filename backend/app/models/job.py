from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey, Float, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base
import uuid
import enum


class SearchInterval(str, enum.Enum):
    four_hours = "4h"
    two_hours = "2h"


class SearchConfig(Base):
    __tablename__ = "search_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    keywords = Column(JSON, nullable=False)  # list of keywords
    location = Column(String(255), nullable=True)
    interval = Column(Enum(SearchInterval), default=SearchInterval.four_hours)
    is_active = Column(Boolean, default=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    search_config_id = Column(UUID(as_uuid=True), ForeignKey("search_configs.id"), nullable=True)
    linkedin_job_id = Column(String(100), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    company = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String(1000), nullable=True)
    posted_at = Column(String(100), nullable=True)
    is_new = Column(Boolean, default=True)
    ai_match_score = Column(Float, nullable=True)  # 0-100
    ai_analysis = Column(Text, nullable=True)
    raw_data = Column(JSON, nullable=True)
    found_at = Column(DateTime(timezone=True), server_default=func.now())


class TokenTransaction(Base):
    __tablename__ = "token_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    amount = Column(Integer, nullable=False)  # positive = credit, negative = debit
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TokenSettings(Base):
    __tablename__ = "token_settings"

    id = Column(Integer, primary_key=True, default=1)
    cost_residential_ip = Column(Integer, default=20)
    cost_search_2h = Column(Integer, default=100)
    cost_ai_evaluation = Column(Integer, default=50)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
