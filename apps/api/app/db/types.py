"""Cross-database column type helpers."""

import uuid
from enum import Enum as PyEnum

from sqlalchemy import JSON, Enum, Uuid
from sqlalchemy.orm import Mapped, mapped_column


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)


def uuid_fk(nullable: bool = False) -> Mapped[uuid.UUID]:
    return mapped_column(Uuid(as_uuid=True), nullable=nullable)


def json_column(default=None):
    if default is None:
        return mapped_column(JSON, default=dict)
    if default is list:
        return mapped_column(JSON, default=list)
    return mapped_column(JSON, default=default)


def str_enum_column(enum_cls: type[PyEnum], name: str, default=None):
    kwargs = {
        "values_callable": lambda x: [e.value for e in x],
        "native_enum": False,
    }
    if default is not None:
        kwargs["default"] = default
    return mapped_column(Enum(enum_cls, name=name, **kwargs))
