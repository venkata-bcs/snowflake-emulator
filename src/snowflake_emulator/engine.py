"""
Execution engine for Snowflake Emulator using DuckDB.
"""

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid
import duckdb

from snowflake_emulator.catalog import Catalog, ColumnMeta
from snowflake_emulator.config import settings
from snowflake_emulator.governance import GovernanceManager
from snowflake_emulator.pipes import PipeManager
from snowflake_emulator.protocol import SnowflakeColumnType
from snowflake_emulator.stages import StageManager
from snowflake_emulator.transpiler import parse_command, transpile_snowflake_to_duckdb


@dataclass
class SessionState:
    session_id: str
    user: str = settings.default_user
    database: str = settings.default_database
    schema: str = settings.default_schema
    warehouse: str = settings.default_warehouse
    role: str = settings.default_role
    autocommit: bool = True
    timezone: str = "UTC"


class SnowflakeEngine:
    def __init__(self):
        self.catalog = Catalog(settings.default_database, settings.default_schema)
        self.stage_manager = StageManager()
        self.pipe_manager = PipeManager()
        self.governance = GovernanceManager()
        self.sessions: Dict[str, SessionState] = {}
        
        # Initialize DuckDB connection
        self.con = duckdb.connect(database=settings.db_path)
        self._init_duckdb()

    def _init_duckdb(self):
        # Enable JSON support
        try:
            self.con.execute("INSTALL json; LOAD json;")
        except Exception:
            pass

        # Try to enable httpfs for S3 access
        try:
            self.con.execute("INSTALL httpfs; LOAD httpfs;")
            if settings.s3_endpoint_url:
                endpoint = settings.s3_endpoint_url.replace("http://", "").replace("https://", "")
                self.con.execute(f"SET s3_endpoint='{endpoint}';")
                self.con.execute("SET s3_use_ssl=false;")
                self.con.execute(f"SET s3_access_key_id='{settings.aws_access_key_id}';")
                self.con.execute(f"SET s3_secret_access_key='{settings.aws_secret_access_key}';")
                self.con.execute("SET s3_url_style='path';")
        except Exception:
            pass

        # Setup standard macros
        self.con.execute("CREATE OR REPLACE MACRO parse_json(s) AS CAST(s AS JSON)")
        self.con.execute("CREATE OR REPLACE MACRO zeroifnull(s) AS COALESCE(s, 0)")
        self.con.execute("CREATE OR REPLACE MACRO nvl(a, b) AS COALESCE(a, b)")
        self.con.execute("CREATE OR REPLACE MACRO nvl2(a, b, c) AS CASE WHEN a IS NOT NULL THEN b ELSE c END")
        self.con.execute("CREATE OR REPLACE MACRO iff(c, a, b) AS CASE WHEN c THEN a ELSE b END")
        self.con.execute("CREATE OR REPLACE MACRO to_date(s) AS CAST(s AS DATE)")
        self.con.execute("CREATE OR REPLACE MACRO to_timestamp_ntz(s) AS CAST(s AS TIMESTAMP)")

        # Create default schema and information_schema views
        self._sync_information_schema()

    def _sync_session_macros(self, session: SessionState):
        self.con.execute(f"CREATE OR REPLACE MACRO current_database() AS '{session.database}'")
        self.con.execute(f"CREATE OR REPLACE MACRO current_schema() AS '{session.schema}'")
        self.con.execute(f"CREATE OR REPLACE MACRO current_warehouse() AS '{session.warehouse}'")
        self.con.execute(f"CREATE OR REPLACE MACRO current_role() AS '{session.role}'")
        self.con.execute(f"CREATE OR REPLACE MACRO current_user() AS '{session.user}'")
        self.con.execute("CREATE OR REPLACE MACRO version() AS '8.45.0'")

    def _sync_information_schema(self):
        # Create schema if not exists
        try:
            self.con.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.default_schema}")
            self.con.execute("CREATE SCHEMA IF NOT EXISTS INFORMATION_SCHEMA")
            
            # Create INFORMATION_SCHEMA.TABLES view
            self.con.execute("""
            CREATE OR REPLACE VIEW INFORMATION_SCHEMA.TABLES AS
            SELECT 
                table_catalog AS table_database,
                table_schema,
                table_name,
                table_type,
                'N' AS is_transient,
                '' AS comment
            FROM information_schema.tables
            """)

            # Create INFORMATION_SCHEMA.COLUMNS view
            self.con.execute("""
            CREATE OR REPLACE VIEW INFORMATION_SCHEMA.COLUMNS AS
            SELECT 
                table_catalog AS table_database,
                table_schema,
                table_name,
                column_name,
                ordinal_position,
                is_nullable,
                data_type,
                '' AS comment
            FROM information_schema.columns
            """)
        except Exception:
            pass

    def create_session(
        self,
        user: Optional[str] = None,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        warehouse: Optional[str] = None,
        role: Optional[str] = None,
    ) -> SessionState:
        session_id = str(uuid.uuid4())
        session = SessionState(
            session_id=session_id,
            user=user or settings.default_user,
            database=(database or settings.default_database).upper(),
            schema=(schema or settings.default_schema).upper(),
            warehouse=(warehouse or settings.default_warehouse).upper(),
            role=(role or settings.default_role).upper()
        )
        self.sessions[session_id] = session
        self.catalog.add_database(session.database)
        self.catalog.add_schema(session.database, session.schema)
        return session

    def get_session(self, session_id: Optional[str]) -> SessionState:
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        # Return default session
        default_id = "default-session"
        if default_id not in self.sessions:
            self.sessions[default_id] = self.create_session()
        return self.sessions[default_id]

    def _map_column_type(self, duck_type_str: str, col_name: str, db: str, schema: str, table: str = "") -> SnowflakeColumnType:
        dt = duck_type_str.upper()
        
        if "INT" in dt or dt in ["BIGINT", "SMALLINT", "TINYINT", "HUGEINT"]:
            return SnowflakeColumnType(name=col_name, database=db, schema=schema, table=table, type="fixed", precision=38, scale=0)
        elif "DECIMAL" in dt or "NUMERIC" in dt:
            m = re.search(r"DECIMAL\((\d+),(\d+)\)", dt)
            p = int(m.group(1)) if m else 38
            s = int(m.group(2)) if m else 2
            return SnowflakeColumnType(name=col_name, database=db, schema=schema, table=table, type="fixed", precision=p, scale=s)
        elif dt in ["DOUBLE", "FLOAT", "REAL"]:
            return SnowflakeColumnType(name=col_name, database=db, schema=schema, table=table, type="real")
        elif dt == "BOOLEAN":
            return SnowflakeColumnType(name=col_name, database=db, schema=schema, table=table, type="boolean")
        elif dt == "DATE":
            return SnowflakeColumnType(name=col_name, database=db, schema=schema, table=table, type="date")
        elif dt == "TIME":
            return SnowflakeColumnType(name=col_name, database=db, schema=schema, table=table, type="time")
        elif "TIMESTAMP" in dt:
            return SnowflakeColumnType(name=col_name, database=db, schema=schema, table=table, type="timestamp_ntz")
        elif "JSON" in dt or "VARIANT" in dt or "STRUCT" in dt or "MAP" in dt:
            return SnowflakeColumnType(name=col_name, database=db, schema=schema, table=table, type="variant")
        elif "LIST" in dt or "[]" in dt:
            return SnowflakeColumnType(name=col_name, database=db, schema=schema, table=table, type="array")
        else:
            return SnowflakeColumnType(name=col_name, database=db, schema=schema, table=table, type="text", length=16777216, byteLength=16777216)

    def _format_cell(self, val: Any) -> Any:
        if val is None:
            return None
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, (datetime,)):
            return val.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        if isinstance(val, (dict, list)):
            return json.dumps(val)
        return str(val)

    def execute(self, sql: str, session: Optional[SessionState] = None) -> Tuple[List[SnowflakeColumnType], List[List[Any]], int]:
        if session is None:
            session = self.get_session(None)

        self._sync_session_macros(session)
        cmd_type, details = parse_command(sql)

        # 1. USE Commands
        if cmd_type == "USE_ROLE":
            session.role = details["role"].upper()
            return [SnowflakeColumnType(name="status", type="text")], [["Statement executed successfully."]], 1

        if cmd_type == "USE_WAREHOUSE":
            session.warehouse = details["warehouse"].upper()
            return [SnowflakeColumnType(name="status", type="text")], [["Statement executed successfully."]], 1

        if cmd_type == "USE_DATABASE":
            session.database = details["database"].upper()
            self.catalog.add_database(session.database)
            return [SnowflakeColumnType(name="status", type="text")], [["Statement executed successfully."]], 1

        if cmd_type == "USE_SCHEMA":
            if "database" in details:
                session.database = details["database"].upper()
                self.catalog.add_database(session.database)
            session.schema = details["schema"].upper()
            self.catalog.add_schema(session.database, session.schema)
            return [SnowflakeColumnType(name="status", type="text")], [["Statement executed successfully."]], 1

        # 2. SHOW Commands
        if cmd_type == "SHOW_DATABASES":
            col_defs, rows = self.catalog.show_databases(session.database)
            rowtypes = [SnowflakeColumnType(name=c["name"], type=c["type"]) for c in col_defs]
            formatted_rows = [[self._format_cell(v) for v in r] for r in rows]
            return rowtypes, formatted_rows, len(rows)

        if cmd_type == "SHOW_SCHEMAS":
            col_defs, rows = self.catalog.show_schemas(session.database, session.schema)
            rowtypes = [SnowflakeColumnType(name=c["name"], type=c["type"]) for c in col_defs]
            formatted_rows = [[self._format_cell(v) for v in r] for r in rows]
            return rowtypes, formatted_rows, len(rows)

        if cmd_type == "SHOW_TABLES":
            # Sync any tables created directly in DuckDB
            try:
                tables_res = self.con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog')").fetchall()
                for (t_name,) in tables_res:
                    self.catalog.add_table(session.database, session.schema, t_name, [])
            except Exception:
                pass
            col_defs, rows = self.catalog.show_tables(session.database, session.schema)
            rowtypes = [SnowflakeColumnType(name=c["name"], type=c["type"]) for c in col_defs]
            formatted_rows = [[self._format_cell(v) for v in r] for r in rows]
            return rowtypes, formatted_rows, len(rows)

        if cmd_type == "SHOW_STAGES":
            col_defs, rows = self.catalog.show_stages(session.database, session.schema)
            rowtypes = [SnowflakeColumnType(name=c["name"], type=c["type"]) for c in col_defs]
            formatted_rows = [[self._format_cell(v) for v in r] for r in rows]
            return rowtypes, formatted_rows, len(rows)

        if cmd_type == "SHOW_PIPES":
            col_defs, rows = self.catalog.show_pipes(session.database, session.schema)
            rowtypes = [SnowflakeColumnType(name=c["name"], type=c["type"]) for c in col_defs]
            formatted_rows = [[self._format_cell(v) for v in r] for r in rows]
            return rowtypes, formatted_rows, len(rows)

        if cmd_type == "SHOW_WAREHOUSES":
            col_defs, rows = self.catalog.show_warehouses(session.warehouse)
            rowtypes = [SnowflakeColumnType(name=c["name"], type=c["type"]) for c in col_defs]
            formatted_rows = [[self._format_cell(v) for v in r] for r in rows]
            return rowtypes, formatted_rows, len(rows)

        if cmd_type == "SHOW_ROLES":
            col_defs, rows = self.catalog.show_roles(session.role)
            rowtypes = [SnowflakeColumnType(name=c["name"], type=c["type"]) for c in col_defs]
            formatted_rows = [[self._format_cell(v) for v in r] for r in rows]
            return rowtypes, formatted_rows, len(rows)

        if cmd_type == "SHOW_PARAMETERS":
            rowtypes = [
                SnowflakeColumnType(name="key", type="text"),
                SnowflakeColumnType(name="value", type="text"),
                SnowflakeColumnType(name="default", type="text"),
                SnowflakeColumnType(name="level", type="text"),
                SnowflakeColumnType(name="description", type="text"),
                SnowflakeColumnType(name="type", type="text")
            ]
            rows = [
                ["TIMEZONE", session.timezone, "UTC", "SESSION", "Timezone for session", "STRING"],
                ["AUTOCOMMIT", "true" if session.autocommit else "false", "true", "SESSION", "Autocommit mode", "BOOLEAN"],
                ["QUERY_TIMEOUT_IN_SECONDS", "3600", "3600", "SESSION", "Query timeout", "NUMBER"]
            ]
            return rowtypes, rows, len(rows)

        # 3. DESCRIBE Commands
        if cmd_type == "DESCRIBE_TABLE":
            tbl_name = details["name"]
            cur = self.con.execute(f"DESCRIBE {tbl_name}")
            desc_rows = cur.fetchall()
            rowtypes = [
                SnowflakeColumnType(name="name", type="text"),
                SnowflakeColumnType(name="type", type="text"),
                SnowflakeColumnType(name="kind", type="text"),
                SnowflakeColumnType(name="null?", type="text"),
                SnowflakeColumnType(name="default", type="text"),
                SnowflakeColumnType(name="primary key", type="text"),
                SnowflakeColumnType(name="unique key", type="text"),
                SnowflakeColumnType(name="check", type="text"),
                SnowflakeColumnType(name="expression", type="text"),
                SnowflakeColumnType(name="comment", type="text"),
                SnowflakeColumnType(name="policy name", type="text")
            ]
            rows = []
            for r in desc_rows:
                col_name, col_type, col_null = r[0], r[1], r[2]
                rows.append([
                    col_name.upper(),
                    col_type.upper(),
                    "COLUMN",
                    "Y" if col_null == "YES" else "N",
                    None,
                    "N",
                    "N",
                    None,
                    None,
                    None,
                    None
                ])
            return rowtypes, rows, len(rows)

        # 4. Stage & Storage Commands
        if cmd_type == "CREATE_STAGE":
            stg_name = details["name"]
            url = details["url"]
            self.catalog.add_stage(session.database, session.schema, stg_name, url)
            return [SnowflakeColumnType(name="status", type="text")], [[f"Stage {stg_name} successfully created."]], 1

        if cmd_type == "DROP_STAGE":
            stg_name = details["name"]
            self.catalog.drop_stage(session.database, session.schema, stg_name)
            return [SnowflakeColumnType(name="status", type="text")], [[f"{stg_name} successfully dropped."]], 1

        if cmd_type == "LIST_STAGE":
            stg_name = details["stage"]
            # Lookup stage metadata if registered
            stg_key = self.catalog.stage_key(session.database, session.schema, stg_name)
            stg_meta = self.catalog.stages.get(stg_key)
            stg_url = stg_meta.url if stg_meta else None
            
            files = self.stage_manager.list_stage_files(stg_name, stg_url)
            rowtypes = [
                SnowflakeColumnType(name="name", type="text"),
                SnowflakeColumnType(name="size", type="fixed"),
                SnowflakeColumnType(name="md5", type="text"),
                SnowflakeColumnType(name="last_modified", type="text")
            ]
            rows = [
                [f["name"], str(f["size"]), f["md5"], f["last_modified"]]
                for f in files
            ]
            return rowtypes, rows, len(rows)

        # 5. COPY INTO
        if cmd_type == "COPY_INTO_TABLE":
            tbl_name = details["table"]
            stg_name = details["stage"]
            files = details["files"]
            fmt = details["format"]
            
            # Lookup stage
            stg_key = self.catalog.stage_key(session.database, session.schema, stg_name)
            stg_meta = self.catalog.stages.get(stg_key)
            stg_url = stg_meta.url if stg_meta else None

            if not files:
                stg_files = self.stage_manager.list_stage_files(stg_name, stg_url)
                files = [Path(f["name"]).name for f in stg_files]

            rowtypes = [
                SnowflakeColumnType(name="file", type="text"),
                SnowflakeColumnType(name="status", type="text"),
                SnowflakeColumnType(name="rows_parsed", type="fixed"),
                SnowflakeColumnType(name="rows_loaded", type="fixed"),
                SnowflakeColumnType(name="error_limit", type="fixed"),
                SnowflakeColumnType(name="errors_seen", type="fixed"),
                SnowflakeColumnType(name="first_error", type="text"),
                SnowflakeColumnType(name="first_error_line", type="fixed"),
                SnowflakeColumnType(name="first_error_character", type="fixed"),
                SnowflakeColumnType(name="first_error_column_name", type="text"),
            ]
            rows = []

            for f_name in files:
                try:
                    file_path = self.stage_manager.get_file_for_ingest(stg_name, f_name, stg_url)
                    # Load file into DuckDB
                    posix_path = str(file_path).replace("\\", "/")
                    if fmt == "CSV":
                        self.con.execute(f"COPY {tbl_name} FROM '{posix_path}' (HEADER true, AUTO_DETECT true)")
                    elif fmt == "PARQUET":
                        self.con.execute(f"INSERT INTO {tbl_name} SELECT * FROM read_parquet('{posix_path}')")
                    elif fmt == "JSON":
                        self.con.execute(f"INSERT INTO {tbl_name} SELECT * FROM read_json_auto('{posix_path}')")
                    else:
                        self.con.execute(f"COPY {tbl_name} FROM '{posix_path}' (AUTO_DETECT true)")

                    # Count loaded
                    cnt_res = self.con.execute(f"SELECT COUNT(*) FROM {tbl_name}").fetchone()
                    loaded_count = cnt_res[0] if cnt_res else 1

                    rows.append([f_name, "LOADED", str(loaded_count), str(loaded_count), "1", "0", None, None, None, None])
                except Exception as e:
                    rows.append([f_name, "LOAD_FAILED", "0", "0", "1", "1", str(e), "1", "1", None])

            return rowtypes, rows, len(rows)

        # 6. Pipes
        if cmd_type == "CREATE_PIPE":
            pipe_name = details["name"]
            auto_ingest = details["auto_ingest"]
            definition = details["definition"]
            self.catalog.add_pipe(session.database, session.schema, pipe_name, definition, auto_ingest)
            return [SnowflakeColumnType(name="status", type="text")], [[f"Pipe {pipe_name} successfully created."]], 1

        if cmd_type == "DROP_PIPE":
            pipe_name = details["name"]
            self.catalog.drop_pipe(session.database, session.schema, pipe_name)
            return [SnowflakeColumnType(name="status", type="text")], [[f"{pipe_name} successfully dropped."]], 1

        # 7. Governance
        if cmd_type == "CREATE_MASKING_POLICY":
            self.governance.add_masking_policy(session.database, session.schema, details["name"], details["body"], details["return_type"])
            return [SnowflakeColumnType(name="status", type="text")], [[f"Masking Policy {details['name']} successfully created."]], 1

        if cmd_type == "CREATE_ROW_ACCESS_POLICY":
            self.governance.add_row_access_policy(session.database, session.schema, details["name"], details["body"])
            return [SnowflakeColumnType(name="status", type="text")], [[f"Row Access Policy {details['name']} successfully created."]], 1

        if cmd_type == "CREATE_TAG":
            self.governance.add_tag(session.database, session.schema, details["name"])
            return [SnowflakeColumnType(name="status", type="text")], [[f"Tag {details['name']} successfully created."]], 1

        # 8. Standard SQL Execution
        transpiled = transpile_snowflake_to_duckdb(sql)
        cur = self.con.execute(transpiled)

        if cur.description:
            # Query returned result set
            rowtypes = [
                self._map_column_type(str(col[1]), col[0].upper(), session.database, session.schema)
                for col in cur.description
            ]
            raw_rows = cur.fetchall()
            formatted_rows = [[self._format_cell(val) for val in r] for r in raw_rows]
            return rowtypes, formatted_rows, len(formatted_rows)
        else:
            # DDL / DML command
            upper_sql = sql.upper().strip()
            # Register created tables in catalog
            m_create_tbl = re.search(r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:TRANSIENT\s+|TEMPORARY\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z0-9_]+)", upper_sql)
            if m_create_tbl:
                tbl_name = m_create_tbl.group(1)
                self.catalog.add_table(session.database, session.schema, tbl_name, [])

            return (
                [SnowflakeColumnType(name="status", type="text")],
                [["Statement executed successfully."]],
                1
            )
