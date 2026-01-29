from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, text
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int = Field(
        sa_column=Column(BigInteger, primary_key=True, autoincrement=False),
    )
    first_name: str = Field(sa_column=Column(String, nullable=False))
    last_name: str | None = Field(default=None, sa_column=Column(String))
    username: str | None = Field(default=None, sa_column=Column(String))
    language_code: str | None = Field(default=None, sa_column=Column(String))
    is_premium: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default=text("false")),
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=text("now()")),
    )
