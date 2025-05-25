from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime
import enum


class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTableUUID, Base):
    items = relationship("Item", back_populates="user", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)

    user = relationship("User", back_populates="items")


class RepoStatus(enum.Enum):
    NOT_INDEXED = "not_indexed"
    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(Integer, unique=True, index=True)
    owner = Column(String, index=True)
    name = Column(String, index=True)
    full_name = Column(String, unique=True, index=True)
    description = Column(Text)
    default_branch = Column(String)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    size = Column(Integer, default=0)
    status = Column(Enum(RepoStatus), default=RepoStatus.NOT_INDEXED)
    
    # Single JSON field containing all indexed data
    # Structure: {
    #   "documentation": [...],      # Code files with docstrings
    #   "documentation_md": [...],   # Markdown files
    #   "config": [...],            # Configuration files
    #   "summary": {...}            # Optional summary metadata
    # }
    indexed_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    indexed_at = Column(DateTime) 