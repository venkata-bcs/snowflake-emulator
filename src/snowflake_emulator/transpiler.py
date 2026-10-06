"""
SQL transpilation and command parsing for Snowflake Emulator.
"""

import re
from typing import Any, Dict, Optional, Tuple
import sqlglot


def clean_sql(sql: str) -> str:
    """Removes single-line and multi-line comments and trailing semicolons."""
    # Remove single line comments
    sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    # Remove block comments
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql.strip().rstrip(";")


def parse_command(sql: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parses Snowflake command and determines if it is a special command or standard SQL.
    Returns (command_type, details).
    """
    normalized = clean_sql(sql).strip()
    upper = normalized.upper()

    # 1. USE statements
    m = re.match(r"^USE\s+ROLE\s+([a-zA-Z0-9_\"\'$]+)", upper)
    if m:
        return "USE_ROLE", {"role": m.group(1).strip("\"'")}

    m = re.match(r"^USE\s+WAREHOUSE\s+([a-zA-Z0-9_\"\'$]+)", upper)
    if m:
        return "USE_WAREHOUSE", {"warehouse": m.group(1).strip("\"'")}

    m = re.match(r"^USE\s+DATABASE\s+([a-zA-Z0-9_\"\'$]+)", upper)
    if m:
        return "USE_DATABASE", {"database": m.group(1).strip("\"'")}

    m = re.match(r"^USE\s+SCHEMA\s+([a-zA-Z0-9_\"\'$]+)", upper)
    if m:
        raw = m.group(1).strip("\"'")
        if "." in raw:
            parts = raw.split(".", 1)
            return "USE_SCHEMA", {"database": parts[0], "schema": parts[1]}
        return "USE_SCHEMA", {"schema": raw}

    m = re.match(r"^USE\s+([a-zA-Z0-9_\"\'$]+)\.([a-zA-Z0-9_\"\'$]+)", upper)
    if m:
        return "USE_SCHEMA", {"database": m.group(1).strip("\"'"), "schema": m.group(2).strip("\"'")}

    # 2. SHOW statements
    if upper.startswith("SHOW DATABASES"):
        return "SHOW_DATABASES", {}

    if upper.startswith("SHOW SCHEMAS"):
        return "SHOW_SCHEMAS", {}

    if upper.startswith("SHOW TABLES"):
        return "SHOW_TABLES", {}

    if upper.startswith("SHOW VIEWS"):
        return "SHOW_VIEWS", {}

    if upper.startswith("SHOW STAGES"):
        return "SHOW_STAGES", {}

    if upper.startswith("SHOW PIPES"):
        return "SHOW_PIPES", {}

    if upper.startswith("SHOW WAREHOUSES"):
        return "SHOW_WAREHOUSES", {}

    if upper.startswith("SHOW ROLES"):
        return "SHOW_ROLES", {}

    if upper.startswith("SHOW PARAMETERS"):
        return "SHOW_PARAMETERS", {}

    if upper.startswith("SHOW GRANTS"):
        return "SHOW_GRANTS", {}

    # 3. DESCRIBE / DESC statements
    m = re.match(r"^DESC(?:RIBE)?\s+TABLE\s+([a-zA-Z0-9_\"\'$\.]+)", upper)
    if m:
        return "DESCRIBE_TABLE", {"name": m.group(1).strip("\"'")}

    m = re.match(r"^DESC(?:RIBE)?\s+STAGE\s+([a-zA-Z0-9_\"\'$@\.]+)", upper)
    if m:
        return "DESCRIBE_STAGE", {"name": m.group(1).strip("\"'@")}

    m = re.match(r"^DESC(?:RIBE)?\s+PIPE\s+([a-zA-Z0-9_\"\'$\.]+)", upper)
    if m:
        return "DESCRIBE_PIPE", {"name": m.group(1).strip("\"'")}

    # 4. Stages & Storage
    m = re.match(
        r"^CREATE(?:\s+OR\s+REPLACE)?(?:\s+TEMPORARY)?\s+STAGE(?:\s+IF\s+NOT\s+EXISTS)?\s+([a-zA-Z0-9_\"\'$@\.]+)(.*)$",
        upper,
        re.DOTALL
    )
    if m:
        stage_name = m.group(1).strip("\"'@")
        remainder = m.group(2)
        url_match = re.search(r"URL\s*=\s*['\"]([^'\"]+)['\"]", remainder)
        url = url_match.group(1) if url_match else f"local://{stage_name}"
        return "CREATE_STAGE", {"name": stage_name, "url": url}

    m = re.match(r"^DROP\s+STAGE(?:\s+IF\s+EXISTS)?\s+([a-zA-Z0-9_\"\'$@\.]+)", upper)
    if m:
        return "DROP_STAGE", {"name": m.group(1).strip("\"'@")}

    m = re.match(r"^LIST\s+@([a-zA-Z0-9_\"\'$\.\/]+)", upper)
    if m:
        return "LIST_STAGE", {"stage": m.group(1).strip("\"'")}

    # 5. COPY INTO
    if upper.startswith("COPY INTO"):
        # Check if unloading to stage: COPY INTO @stage FROM ...
        m_unload = re.match(r"^COPY\s+INTO\s+@([a-zA-Z0-9_\"\'$\.\/]+)\s+FROM\s+(.*)$", upper, re.DOTALL)
        if m_unload:
            return "COPY_INTO_STAGE", {"stage": m_unload.group(1).strip("\"'"), "query": m_unload.group(2)}

        # Ingest: COPY INTO <table> FROM @<stage> ...
        m_load = re.match(r"^COPY\s+INTO\s+([a-zA-Z0-9_\"\'$\.]+)\s+FROM\s+@([a-zA-Z0-9_\"\'$\.\/]+)(.*)$", upper, re.DOTALL)
        if m_load:
            table_name = m_load.group(1).strip("\"'")
            stage_target = m_load.group(2).strip("\"'")
            rest = m_load.group(3)
            
            # Extract optional FILES = (...)
            files_match = re.search(r"FILES\s*=\s*\((.*?)\)", rest)
            files = []
            if files_match:
                files = [f.strip().strip("'\"") for f in files_match.group(1).split(",")]

            # Extract FILE_FORMAT = (TYPE = CSV/PARQUET/JSON ...)
            fmt_type = "CSV"
            fmt_match = re.search(r"TYPE\s*=\s*([A-Za-z0-9_]+)", rest)
            if fmt_match:
                fmt_type = fmt_match.group(1).upper()
            elif "PARQUET" in rest:
                fmt_type = "PARQUET"
            elif "JSON" in rest:
                fmt_type = "JSON"

            return "COPY_INTO_TABLE", {
                "table": table_name,
                "stage": stage_target,
                "files": files,
                "format": fmt_type
            }

    # 6. Pipes
    m = re.match(
        r"^CREATE(?:\s+OR\s+REPLACE)?\s+PIPE(?:\s+IF\s+NOT\s+EXISTS)?\s+([a-zA-Z0-9_\"\'$\.]+)(?:\s+AUTO_INGEST\s*=\s*(TRUE|FALSE))?\s+AS\s+(COPY\s+INTO.*)$",
        upper,
        re.DOTALL
    )
    if m:
        pipe_name = m.group(1).strip("\"'")
        auto_ingest = m.group(2) == "TRUE" if m.group(2) else False
        definition = m.group(3).strip()
        return "CREATE_PIPE", {"name": pipe_name, "auto_ingest": auto_ingest, "definition": definition}

    m = re.match(r"^DROP\s+PIPE(?:\s+IF\s+EXISTS)?\s+([a-zA-Z0-9_\"\'$\.]+)", upper)
    if m:
        return "DROP_PIPE", {"name": m.group(1).strip("\"'")}

    # 7. Governance: Masking Policy & Row Access Policy
    m = re.match(r"^CREATE(?:\s+OR\s+REPLACE)?\s+MASKING\s+POLICY\s+([a-zA-Z0-9_\"\'$\.]+)\s+AS\s+\((.*?)\)\s+RETURNS\s+([A-Za-z0-9_]+)\s*->\s*(.*)$", upper, re.DOTALL)
    if m:
        return "CREATE_MASKING_POLICY", {
            "name": m.group(1).strip("\"'"),
            "signature": m.group(2).strip(),
            "return_type": m.group(3).strip(),
            "body": m.group(4).strip()
        }

    m = re.match(r"^CREATE(?:\s+OR\s+REPLACE)?\s+ROW\s+ACCESS\s+POLICY\s+([a-zA-Z0-9_\"\'$\.]+)\s+AS\s+\((.*?)\)\s+RETURNS\s+BOOLEAN\s*->\s*(.*)$", upper, re.DOTALL)
    if m:
        return "CREATE_ROW_ACCESS_POLICY", {
            "name": m.group(1).strip("\"'"),
            "signature": m.group(2).strip(),
            "body": m.group(3).strip()
        }

    m = re.match(r"^CREATE(?:\s+OR\s+REPLACE)?\s+TAG\s+([a-zA-Z0-9_\"\'$\.]+)", upper)
    if m:
        return "CREATE_TAG", {"name": m.group(1).strip("\"'")}

    return "STANDARD_SQL", {"sql": normalized}


def transpile_snowflake_to_duckdb(sql: str) -> str:
    """
    Translates Snowflake SQL query into DuckDB dialect.
    """
    cleaned = clean_sql(sql)
    
    # Pre-processing Snowflake specifics:
    # 1. TRANSIENT / TEMPORARY tables
    cleaned = re.sub(r"\bCREATE\s+(?:OR\s+REPLACE\s+)?TRANSIENT\s+TABLE\b", "CREATE TABLE", cleaned, flags=re.IGNORECASE)
    
    # 2. VARIANT data types to JSON
    cleaned = re.sub(r"\bVARIANT\b", "JSON", cleaned, flags=re.IGNORECASE)

    # 3. TIMESTAMP_NTZ / LTZ / TZ to TIMESTAMP
    cleaned = re.sub(r"\bTIMESTAMP_(?:NTZ|LTZ|TZ)\b", "TIMESTAMP", cleaned, flags=re.IGNORECASE)

    # 4. OBJECT_CONSTRUCT(...) -> json_object(...)
    cleaned = re.sub(r"\bOBJECT_CONSTRUCT\b", "json_object", cleaned, flags=re.IGNORECASE)

    # 5. ARRAY_CONSTRUCT(...) -> list_value(...)
    cleaned = re.sub(r"\bARRAY_CONSTRUCT\b", "list_value", cleaned, flags=re.IGNORECASE)

    # Use SQLGlot to transpile dialect
    try:
        transpiled = sqlglot.transpile(cleaned, read="snowflake", write="duckdb")[0]
        # In DuckDB, -> returns JSON with quotes, while ->> unquotes text
        transpiled = re.sub(
            r"CAST\((.*?)\s+->\s+'\$\.([^']+)'\s+AS\s+TEXT\)",
            r"(\1 ->> '\2')",
            transpiled,
            flags=re.IGNORECASE
        )
        return transpiled
    except Exception:
        # If sqlglot parsing fails on custom Snowflake syntax, fallback to preprocessed query
        return cleaned
