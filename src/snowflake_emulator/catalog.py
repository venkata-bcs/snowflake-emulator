"""
Metadata catalog and Information Schema provider for Snowflake Emulator.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import time


def utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " +0000"


@dataclass
class ColumnMeta:
    name: str
    data_type: str
    nullable: bool = True
    ordinal_position: int = 1
    comment: Optional[str] = None


@dataclass
class TableMeta:
    database: str
    schema: str
    name: str
    kind: str = "TABLE"  # "TABLE", "VIEW", "TEMPORARY", "TRANSIENT"
    columns: List[ColumnMeta] = field(default_factory=list)
    rows: int = 0
    bytes: int = 0
    owner: str = "SYSADMIN"
    comment: Optional[str] = ""
    created_on: str = field(default_factory=utc_now_str)
    definition: Optional[str] = None  # for views


@dataclass
class StageMeta:
    database: str
    schema: str
    name: str
    url: str
    stage_type: str = "EXTERNAL"  # "EXTERNAL", "INTERNAL"
    owner: str = "SYSADMIN"
    comment: Optional[str] = ""
    created_on: str = field(default_factory=utc_now_str)


@dataclass
class PipeMeta:
    database: str
    schema: str
    name: str
    definition: str  # COPY INTO <table> FROM @<stage> ...
    auto_ingest: bool = False
    owner: str = "SYSADMIN"
    notification_channel: Optional[str] = None
    pattern: Optional[str] = None
    created_on: str = field(default_factory=utc_now_str)
    status: str = "RUNNING"  # "RUNNING", "STOPPED", "PAUSED"


@dataclass
class GrantMeta:
    privilege: str
    granted_on: str
    name: str
    granted_to: str
    grantee_name: str
    grant_option: str = "false"
    granted_by: str = "SECURITYADMIN"
    created_on: str = field(default_factory=utc_now_str)


class Catalog:
    def __init__(self, default_db: str = "DEMO_DB", default_schema: str = "PUBLIC"):
        self.default_db = default_db
        self.default_schema = default_schema
        
        self.databases: Dict[str, Dict[str, Any]] = {
            default_db: {
                "name": default_db,
                "owner": "SYSADMIN",
                "comment": "Default emulator database",
                "created_on": self._now_str()
            },
            "SNOWFLAKE": {
                "name": "SNOWFLAKE",
                "owner": "ACCOUNTADMIN",
                "comment": "System information database",
                "created_on": self._now_str()
            }
        }
        
        self.schemas: Dict[str, Dict[str, Dict[str, Any]]] = {
            default_db: {
                default_schema: {
                    "name": default_schema,
                    "database": default_db,
                    "owner": "SYSADMIN",
                    "comment": "Default public schema",
                    "created_on": self._now_str()
                },
                "INFORMATION_SCHEMA": {
                    "name": "INFORMATION_SCHEMA",
                    "database": default_db,
                    "owner": "ACCOUNTADMIN",
                    "comment": "Information schema views",
                    "created_on": self._now_str()
                }
            },
            "SNOWFLAKE": {
                "ACCOUNT_USAGE": {
                    "name": "ACCOUNT_USAGE",
                    "database": "SNOWFLAKE",
                    "owner": "ACCOUNTADMIN",
                    "comment": "Account usage historical metadata",
                    "created_on": self._now_str()
                }
            }
        }
        
        self.tables: Dict[str, TableMeta] = {}
        self.stages: Dict[str, StageMeta] = {}
        self.pipes: Dict[str, PipeMeta] = {}
        self.warehouses: List[str] = ["COMPUTE_WH", "DEV_WH"]
        self.roles: List[str] = ["ACCOUNTADMIN", "SYSADMIN", "SECURITYADMIN", "USERADMIN", "PUBLIC"]
        self.grants: List[GrantMeta] = [
            GrantMeta("USAGE", "WAREHOUSE", "COMPUTE_WH", "ROLE", "PUBLIC"),
            GrantMeta("USAGE", "DATABASE", default_db, "ROLE", "PUBLIC"),
            GrantMeta("USAGE", "SCHEMA", f"{default_db}.{default_schema}", "ROLE", "PUBLIC"),
        ]

    def _now_str(self) -> str:
        return utc_now_str()

    def table_key(self, db: str, schema: str, name: str) -> str:
        return f"{db.upper()}.{schema.upper()}.{name.upper()}"

    def stage_key(self, db: str, schema: str, name: str) -> str:
        return f"{db.upper()}.{schema.upper()}.{name.upper()}"

    def pipe_key(self, db: str, schema: str, name: str) -> str:
        return f"{db.upper()}.{schema.upper()}.{name.upper()}"

    def add_database(self, name: str, owner: str = "SYSADMIN", comment: str = ""):
        name = name.upper()
        self.databases[name] = {
            "name": name,
            "owner": owner,
            "comment": comment,
            "created_on": self._now_str()
        }
        if name not in self.schemas:
            self.schemas[name] = {
                "PUBLIC": {
                    "name": "PUBLIC",
                    "database": name,
                    "owner": owner,
                    "comment": "Default public schema",
                    "created_on": self._now_str()
                },
                "INFORMATION_SCHEMA": {
                    "name": "INFORMATION_SCHEMA",
                    "database": name,
                    "owner": "ACCOUNTADMIN",
                    "comment": "Information schema",
                    "created_on": self._now_str()
                }
            }

    def add_schema(self, db: str, name: str, owner: str = "SYSADMIN", comment: str = ""):
        db = db.upper()
        name = name.upper()
        if db not in self.schemas:
            self.add_database(db, owner)
        self.schemas[db][name] = {
            "name": name,
            "database": db,
            "owner": owner,
            "comment": comment,
            "created_on": self._now_str()
        }

    def add_table(self, db: str, schema: str, name: str, columns: List[ColumnMeta], kind: str = "TABLE", comment: str = "", definition: Optional[str] = None):
        key = self.table_key(db, schema, name)
        self.tables[key] = TableMeta(
            database=db.upper(),
            schema=schema.upper(),
            name=name.upper(),
            kind=kind.upper(),
            columns=columns,
            comment=comment,
            definition=definition
        )

    def drop_table(self, db: str, schema: str, name: str):
        key = self.table_key(db, schema, name)
        self.tables.pop(key, None)

    def add_stage(self, db: str, schema: str, name: str, url: str, stage_type: str = "EXTERNAL", comment: str = ""):
        key = self.stage_key(db, schema, name)
        self.stages[key] = StageMeta(
            database=db.upper(),
            schema=schema.upper(),
            name=name.upper(),
            url=url,
            stage_type=stage_type.upper(),
            comment=comment
        )

    def drop_stage(self, db: str, schema: str, name: str):
        key = self.stage_key(db, schema, name)
        self.stages.pop(key, None)

    def add_pipe(self, db: str, schema: str, name: str, definition: str, auto_ingest: bool = False, pattern: Optional[str] = None):
        key = self.pipe_key(db, schema, name)
        self.pipes[key] = PipeMeta(
            database=db.upper(),
            schema=schema.upper(),
            name=name.upper(),
            definition=definition,
            auto_ingest=auto_ingest,
            pattern=pattern,
            notification_channel=f"snowflake-emulator://pipes/{name.upper()}"
        )

    def drop_pipe(self, db: str, schema: str, name: str):
        key = self.pipe_key(db, schema, name)
        self.pipes.pop(key, None)

    # SHOW command response builders
    def show_databases(self, current_db: str) -> (List[Dict[str, Any]], List[List[Any]]):
        columns = [
            {"name": "created_on", "type": "timestamp_ltz"},
            {"name": "name", "type": "text"},
            {"name": "is_default", "type": "text"},
            {"name": "is_current", "type": "text"},
            {"name": "origin", "type": "text"},
            {"name": "owner", "type": "text"},
            {"name": "comment", "type": "text"},
            {"name": "options", "type": "text"},
            {"name": "retention_time", "type": "text"},
        ]
        rows = []
        for name, d in self.databases.items():
            rows.append([
                d["created_on"],
                name,
                "N",
                "Y" if name == current_db.upper() else "N",
                "",
                d["owner"],
                d.get("comment", ""),
                "",
                "1"
            ])
        return columns, rows

    def show_schemas(self, current_db: str, current_schema: str) -> (List[Dict[str, Any]], List[List[Any]]):
        columns = [
            {"name": "created_on", "type": "timestamp_ltz"},
            {"name": "name", "type": "text"},
            {"name": "is_default", "type": "text"},
            {"name": "is_current", "type": "text"},
            {"name": "database_name", "type": "text"},
            {"name": "owner", "type": "text"},
            {"name": "comment", "type": "text"},
            {"name": "options", "type": "text"},
            {"name": "retention_time", "type": "text"},
        ]
        rows = []
        db_schemas = self.schemas.get(current_db.upper(), {})
        for name, s in db_schemas.items():
            rows.append([
                s["created_on"],
                name,
                "N",
                "Y" if name == current_schema.upper() else "N",
                current_db.upper(),
                s["owner"],
                s.get("comment", ""),
                "",
                "1"
            ])
        return columns, rows

    def show_tables(self, current_db: str, current_schema: str) -> (List[Dict[str, Any]], List[List[Any]]):
        columns = [
            {"name": "created_on", "type": "timestamp_ltz"},
            {"name": "name", "type": "text"},
            {"name": "database_name", "type": "text"},
            {"name": "schema_name", "type": "text"},
            {"name": "kind", "type": "text"},
            {"name": "comment", "type": "text"},
            {"name": "cluster_by", "type": "text"},
            {"name": "rows", "type": "fixed"},
            {"name": "bytes", "type": "fixed"},
            {"name": "owner", "type": "text"},
            {"name": "retention_time", "type": "text"},
            {"name": "dropped_on", "type": "timestamp_ltz"},
            {"name": "automatic_clustering", "type": "text"},
            {"name": "change_tracking", "type": "text"},
            {"name": "is_external", "type": "text"},
        ]
        rows = []
        for key, t in self.tables.items():
            if t.database == current_db.upper() and (not current_schema or t.schema == current_schema.upper()):
                rows.append([
                    t.created_on,
                    t.name,
                    t.database,
                    t.schema,
                    t.kind,
                    t.comment or "",
                    "",
                    str(t.rows),
                    str(t.bytes),
                    t.owner,
                    "1",
                    None,
                    "OFF",
                    "OFF",
                    "N"
                ])
        return columns, rows

    def show_stages(self, current_db: str, current_schema: str) -> (List[Dict[str, Any]], List[List[Any]]):
        columns = [
            {"name": "created_on", "type": "timestamp_ltz"},
            {"name": "name", "type": "text"},
            {"name": "database_name", "type": "text"},
            {"name": "schema_name", "type": "text"},
            {"name": "url", "type": "text"},
            {"name": "has_credentials", "type": "text"},
            {"name": "has_encryption", "type": "text"},
            {"name": "owner", "type": "text"},
            {"name": "comment", "type": "text"},
            {"name": "region", "type": "text"},
            {"name": "type", "type": "text"},
        ]
        rows = []
        for key, s in self.stages.items():
            if s.database == current_db.upper() and (not current_schema or s.schema == current_schema.upper()):
                rows.append([
                    s.created_on,
                    s.name,
                    s.database,
                    s.schema,
                    s.url,
                    "Y",
                    "N",
                    s.owner,
                    s.comment or "",
                    "us-east-1",
                    s.stage_type
                ])
        return columns, rows

    def show_pipes(self, current_db: str, current_schema: str) -> (List[Dict[str, Any]], List[List[Any]]):
        columns = [
            {"name": "created_on", "type": "timestamp_ltz"},
            {"name": "name", "type": "text"},
            {"name": "database_name", "type": "text"},
            {"name": "schema_name", "type": "text"},
            {"name": "definition", "type": "text"},
            {"name": "owner", "type": "text"},
            {"name": "notification_channel", "type": "text"},
            {"name": "comment", "type": "text"},
            {"name": "pattern", "type": "text"},
        ]
        rows = []
        for key, p in self.pipes.items():
            if p.database == current_db.upper() and (not current_schema or p.schema == current_schema.upper()):
                rows.append([
                    p.created_on,
                    p.name,
                    p.database,
                    p.schema,
                    p.definition,
                    p.owner,
                    p.notification_channel or "",
                    "",
                    p.pattern or ""
                ])
        return columns, rows

    def show_warehouses(self, current_wh: str) -> (List[Dict[str, Any]], List[List[Any]]):
        columns = [
            {"name": "name", "type": "text"},
            {"name": "state", "type": "text"},
            {"name": "type", "type": "text"},
            {"name": "size", "type": "text"},
            {"name": "min_cluster_count", "type": "fixed"},
            {"name": "max_cluster_count", "type": "fixed"},
            {"name": "started_clusters", "type": "fixed"},
            {"name": "running", "type": "fixed"},
            {"name": "queued", "type": "fixed"},
            {"name": "is_default", "type": "text"},
            {"name": "is_current", "type": "text"},
            {"name": "auto_suspend", "type": "fixed"},
            {"name": "auto_resume", "type": "text"},
            {"name": "created_on", "type": "timestamp_ltz"},
            {"name": "owner", "type": "text"},
            {"name": "comment", "type": "text"},
        ]
        rows = []
        for wh in self.warehouses:
            rows.append([
                wh,
                "STARTED",
                "STANDARD",
                "X-Small",
                "1",
                "1",
                "1",
                "0",
                "0",
                "Y" if wh == current_wh.upper() else "N",
                "Y" if wh == current_wh.upper() else "N",
                "600",
                "true",
                self._now_str(),
                "SYSADMIN",
                "Emulator virtual warehouse"
            ])
        return columns, rows

    def show_roles(self, current_role: str) -> (List[Dict[str, Any]], List[List[Any]]):
        columns = [
            {"name": "created_on", "type": "timestamp_ltz"},
            {"name": "name", "type": "text"},
            {"name": "is_default", "type": "text"},
            {"name": "is_current", "type": "text"},
            {"name": "assigned_to_users", "type": "fixed"},
            {"name": "granted_to_roles", "type": "fixed"},
            {"name": "granted_roles", "type": "fixed"},
            {"name": "owner", "type": "text"},
            {"name": "comment", "type": "text"},
        ]
        rows = []
        for r in self.roles:
            rows.append([
                self._now_str(),
                r,
                "N",
                "Y" if r == current_role.upper() else "N",
                "1",
                "0",
                "0",
                "USERADMIN",
                f"Role {r}"
            ])
        return columns, rows
