"""
SQLAlchemy ORM Data Models and Database Configuration.
Module 3 - Johns Hopkins University Software Concepts (EN.605.601)

Defines the declarative 'Applicant' model representing the PostgreSQL 'applicants' table
and provides SQLAlchemy 2.0 Engine and Session factory helpers.
"""
from __future__ import annotations

import os
from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    """SQLAlchemy Declarative Base class."""
    pass


class Applicant(Base):
    """
    SQLAlchemy ORM representation of the 'applicants' table in PostgreSQL.
    """
    __tablename__ = "applicants"

    p_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_added: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    term: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    us_or_international: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gre: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gre_v: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gre_aw: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    degree: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    llm_generated_program: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    llm_generated_university: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Applicant(p_id={self.p_id}, program={self.program!r}, status={self.status!r})>"


def get_database_uri() -> str:
    """
    Build SQLAlchemy database URI from environment variables with safe defaults.
    """
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        # Normalize postgres:// to postgresql+psycopg:// if needed
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return database_url

    dbname = os.environ.get("POSTGRES_DB", "gradcafe_db")
    user = os.environ.get("POSTGRES_USER", os.environ.get("USER", "postgres"))
    password = os.environ.get("POSTGRES_PASSWORD", "")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")

    if user and password:
        auth = f"{user}:{password}@"
    elif user:
        auth = f"{user}@"
    else:
        auth = ""

    return f"postgresql+psycopg://{auth}{host}:{port}/{dbname}"


def get_engine():
    """
    Create and return a SQLAlchemy Engine instance.
    """
    uri = get_database_uri()
    return create_engine(uri, echo=False, pool_pre_ping=True)


# Global session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db_session() -> Session:
    """
    Provide a transactional database session scope.
    """
    return SessionLocal()
