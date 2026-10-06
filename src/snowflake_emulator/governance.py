"""
Data governance, RBAC, Masking policies, and Row Access policies for Snowflake Emulator.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " +0000"


@dataclass
class MaskingPolicyMeta:
    name: str
    database: str
    schema: str
    body: str  # expression / lambda
    return_type: str = "VARCHAR"
    created_on: str = field(default_factory=utc_now_str)


@dataclass
class RowAccessPolicyMeta:
    name: str
    database: str
    schema: str
    body: str
    created_on: str = field(default_factory=utc_now_str)


@dataclass
class TagMeta:
    name: str
    database: str
    schema: str
    allowed_values: List[str] = field(default_factory=list)
    created_on: str = field(default_factory=utc_now_str)


class GovernanceManager:
    def __init__(self):
        self.roles = ["ACCOUNTADMIN", "SYSADMIN", "SECURITYADMIN", "USERADMIN", "PUBLIC"]
        self.masking_policies: Dict[str, MaskingPolicyMeta] = {}
        self.row_access_policies: Dict[str, RowAccessPolicyMeta] = {}
        self.tags: Dict[str, TagMeta] = {}
        # (table, column) -> policy_name
        self.column_masking_bindings: Dict[str, str] = {}
        # table -> policy_name
        self.table_row_access_bindings: Dict[str, str] = {}
        # object_key -> Dict[tag_name, tag_value]
        self.object_tags: Dict[str, Dict[str, str]] = {}

    def add_masking_policy(self, db: str, schema: str, name: str, body: str, return_type: str = "VARCHAR"):
        key = f"{db.upper()}.{schema.upper()}.{name.upper()}"
        self.masking_policies[key] = MaskingPolicyMeta(
            name=name.upper(),
            database=db.upper(),
            schema=schema.upper(),
            body=body,
            return_type=return_type
        )

    def add_row_access_policy(self, db: str, schema: str, name: str, body: str):
        key = f"{db.upper()}.{schema.upper()}.{name.upper()}"
        self.row_access_policies[key] = RowAccessPolicyMeta(
            name=name.upper(),
            database=db.upper(),
            schema=schema.upper(),
            body=body
        )

    def add_tag(self, db: str, schema: str, name: str, allowed_values: Optional[List[str]] = None):
        key = f"{db.upper()}.{schema.upper()}.{name.upper()}"
        self.tags[key] = TagMeta(
            name=name.upper(),
            database=db.upper(),
            schema=schema.upper(),
            allowed_values=allowed_values or []
        )

    def bind_masking_policy(self, db: str, schema: str, table: str, column: str, policy_name: str):
        key = f"{db.upper()}.{schema.upper()}.{table.upper()}.{column.upper()}"
        self.column_masking_bindings[key] = policy_name.upper()

    def bind_row_access_policy(self, db: str, schema: str, table: str, policy_name: str):
        key = f"{db.upper()}.{schema.upper()}.{table.upper()}"
        self.table_row_access_bindings[key] = policy_name.upper()

    def set_tag(self, object_key: str, tag_name: str, tag_value: str):
        if object_key not in self.object_tags:
            self.object_tags[object_key] = {}
        self.object_tags[object_key][tag_name.upper()] = tag_value
