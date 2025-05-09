from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLAEnum, Float
from sqlalchemy.orm import relationship



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





class RepoStatus(str, Enum):    
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
    description = Column(Text, nullable=True)
    default_branch = Column(String)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    size = Column(Integer)
    status = Column(SQLAEnum(RepoStatus), default=RepoStatus.NOT_INDEXED)
    checkout_session_id = Column(String, nullable=True)
    indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = relationship("RepositoryFile", back_populates="repository", cascade="all, delete-orphan")
    code_units = relationship("CodeUnit", back_populates="repository", cascade="all, delete-orphan")


class RepositoryFile(Base):
    __tablename__ = "repository_files"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), index=True)
    path = Column(String, index=True)
    type = Column(String)  # "file" or "directory"
    size = Column(Integer, nullable=True)
    language = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repository = relationship("Repository", back_populates="files")
    code_units = relationship("CodeUnit", back_populates="file", cascade="all, delete-orphan")


class CodeUnit(Base):
    __tablename__ = "code_units"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), index=True)
    file_id = Column(Integer, ForeignKey("repository_files.id", ondelete="CASCADE"), index=True)
    name = Column(String, index=True)
    type = Column(String)  # "function", "class", "method", etc.
    start_line = Column(Integer)
    end_line = Column(Integer)
    content = Column(Text)
    description = Column(Text, nullable=True)
    embedding_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repository = relationship("Repository", back_populates="code_units")
    file = relationship("RepositoryFile", back_populates="code_units") 