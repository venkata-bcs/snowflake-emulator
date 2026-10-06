"""
FastAPI application implementing Snowflake REST API Wire Protocol and Snowpipe endpoints.
"""

from contextlib import asynccontextmanager
import gzip
import json
import logging
from typing import Any, Dict, List, Optional
import uuid
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from snowflake_emulator.config import settings
from snowflake_emulator.engine import SnowflakeEngine
from snowflake_emulator.protocol import (
    QueryResponseData,
    SnowflakeColumnType,
    SnowflakeParameter,
    SnowflakeResponse,
    create_error_response,
    create_success_response,
)

logger = logging.getLogger("snowflake_emulator")

# Shared Engine Instance
engine = SnowflakeEngine()


class QueryRequestPayload(BaseModel):
    sqlText: str
    bindings: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    queryId: Optional[str] = None


class InsertFilesPayload(BaseModel):
    files: List[Dict[str, Any]]


app = FastAPI(
    title="Snowflake Emulator",
    description="Clean-room local Snowflake Data Cloud emulator with REST wire protocol",
    version="0.1.0"
)


async def get_request_body_json(request: Request) -> Dict[str, Any]:
    raw_body = await request.body()
    if not raw_body:
        return {}
    encoding = request.headers.get("content-encoding", "").lower()
    if "gzip" in encoding or raw_body.startswith(b"\x1f\x8b"):
        try:
            decompressed = gzip.decompress(raw_body)
            return json.loads(decompressed.decode("utf-8"))
        except Exception:
            pass
    try:
        return json.loads(raw_body.decode("utf-8"))
    except Exception:
        return {}


def extract_session_token(request: Request, authorization: Optional[str] = None) -> Optional[str]:
    # Check Authorization header: 'Snowflake Token="<token>"'
    if authorization:
        if 'Snowflake Token="' in authorization:
            return authorization.split('Snowflake Token="')[1].rstrip('"')
        parts = authorization.split()
        if len(parts) == 2:
            return parts[1].strip('"')
    return request.query_params.get("token") or "default-session"


@app.post("/session/v1/login-request")
async def login_request(
    request: Request,
    databaseName: Optional[str] = Query(None, alias="databaseName"),
    schemaName: Optional[str] = Query(None, alias="schemaName"),
    warehouse: Optional[str] = Query(None, alias="warehouse"),
    roleName: Optional[str] = Query(None, alias="roleName"),
):
    body = await get_request_body_json(request)
    data = body.get("data", {})

    user = data.get("LOGIN_NAME") or settings.default_user
    db = databaseName or data.get("databaseName") or settings.default_database
    schema = schemaName or data.get("schemaName") or settings.default_schema
    wh = warehouse or data.get("warehouse") or settings.default_warehouse
    role = roleName or data.get("roleName") or settings.default_role

    session = engine.create_session(
        user=user,
        database=db,
        schema=schema,
        warehouse=wh,
        role=role
    )

    token_val = session.session_id
    master_token = f"master-{token_val}"

    session_params = [
        {"name": "AUTOCOMMIT", "value": True},
        {"name": "TIMEZONE", "value": "UTC"},
        {"name": "CLIENT_SESSION_KEEP_ALIVE", "value": False},
        {"name": "QUERY_TIMEOUT_IN_SECONDS", "value": 3600},
        {"name": "CURRENT_CLIENT_BUILD_ID", "value": "emulator-0.1.0"},
        {"name": "DATE_OUTPUT_FORMAT", "value": "YYYY-MM-DD"},
        {"name": "TIMESTAMP_OUTPUT_FORMAT", "value": "YYYY-MM-DD HH24:MI:SS.FF3"},
        {"name": "TIMESTAMP_NTZ_OUTPUT_FORMAT", "value": "YYYY-MM-DD HH24:MI:SS.FF3"},
        {"name": "CLIENT_PREFETCH_THREADS", "value": 1},
        {"name": "CLIENT_RESULT_PREFETCH_SLOTS", "value": 2},
        {"name": "CLIENT_RESULT_PREFETCH_THREADS", "value": 1},
        {"name": "CLIENT_HONOR_CLIENT_TZ_FOR_TIMESTAMP_NTZ", "value": True},
        {"name": "TIMESTAMP_TYPE_MAPPING", "value": "TIMESTAMP_NTZ"},
        {"name": "BINARY_OUTPUT_FORMAT", "value": "HEX"},
    ]

    response_payload = {
        "data": {
            "masterToken": master_token,
            "token": token_val,
            "validityInSeconds": 86400,
            "masterValidityInSeconds": 86400,
            "displayId": user.lower(),
            "parameters": session_params,
            "sessionInfo": {
                "databaseName": session.database,
                "schemaName": session.schema,
                "warehouseName": session.warehouse,
                "roleName": session.role
            },
            "idToken": token_val
        },
        "code": None,
        "message": None,
        "success": True
    }

    return JSONResponse(content=response_payload)


@app.post("/queries/v1/abort-request")
async def abort_request():
    return JSONResponse(content={"data": None, "code": None, "message": None, "success": True})


@app.post("/queries/v1/query-request")
async def query_request(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    body = await get_request_body_json(request)
    sql_text = body.get("sqlText", "").strip()
    session_id = extract_session_token(request, authorization)
    session = engine.get_session(session_id)

    if not sql_text:
        return JSONResponse(
            content=create_error_response("SQL statement cannot be empty").model_dump(),
            status_code=400
        )

    try:
        rowtypes, rowset, total = engine.execute(sql_text, session)
        q_id = body.get("queryId") or str(uuid.uuid4())

        data = QueryResponseData(
            parameters=[
                SnowflakeParameter(name="AUTOCOMMIT", value=session.autocommit),
                SnowflakeParameter(name="TIMEZONE", value=session.timezone)
            ],
            rowtype=rowtypes,
            rowset=rowset,
            total=total,
            returned=len(rowset),
            queryId=q_id,
            finalDatabaseName=session.database,
            finalSchemaName=session.schema,
            finalWarehouseName=session.warehouse,
            finalRoleName=session.role,
            sqlState="00000"
        )

        return JSONResponse(content=create_success_response(data.model_dump()).model_dump())

    except Exception as e:
        logger.exception("Error executing query: %s", sql_text)
        return JSONResponse(
            content=create_error_response(f"SQL execution error: {str(e)}").model_dump(),
            status_code=200  # Snowflake returns 200 with success=false in JSON
        )


@app.post("/session/v1/heartbeat")
async def heartbeat():
    return JSONResponse(content={"data": None, "code": None, "message": None, "success": True})


@app.post("/session/v1/close-session")
async def close_session():
    return JSONResponse(content={"data": None, "code": None, "message": None, "success": True})


# --- Snowpipe REST Endpoints ---

@app.post("/v1/data/pipes/{pipe_name}/insertFiles")
async def insert_files(pipe_name: str, payload: InsertFilesPayload):
    """Snowpipe ingestion endpoint to queue and load files."""
    clean_pipe = pipe_name.upper()
    pipe_meta = None
    for k, p in engine.catalog.pipes.items():
        if p.name == clean_pipe:
            pipe_meta = p
            break

    # If pipe doesn't exist yet, create default metadata
    if not pipe_meta:
        pipe_meta = engine.catalog.add_pipe(
            engine.get_session(None).database,
            engine.get_session(None).schema,
            clean_pipe,
            f"COPY INTO {clean_pipe}_TABLE FROM @{clean_pipe}_STAGE"
        )

    files_to_load = [f.get("path") for f in payload.files if f.get("path")]
    for f in files_to_load:
        engine.pipe_manager.record_load(clean_pipe, f, "LOADED", rows_loaded=1)

    return JSONResponse(content={"pipe": clean_pipe, "completeResult": True})


@app.get("/v1/data/pipes/{pipe_name}/insertReport")
async def insert_report(pipe_name: str):
    return JSONResponse(content=engine.pipe_manager.get_insert_report(pipe_name))


@app.get("/v1/data/pipes/{pipe_name}/loadHistoryScan")
async def load_history_scan(pipe_name: str):
    return JSONResponse(content=engine.pipe_manager.get_load_history(pipe_name))


# --- Health & Web Status ---

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "snowflake-emulator",
        "version": "0.1.0",
        "engine": "duckdb",
        "default_database": settings.default_database,
        "default_schema": settings.default_schema
    }


@app.get("/", response_class=HTMLResponse)
async def root_dashboard():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Snowflake Emulator</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px; }}
            .container {{ max-width: 900px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            h1 {{ color: #38bdf8; display: flex; align-items: center; gap: 12px; margin-top: 0; }}
            .badge {{ background: #0284c7; color: white; padding: 4px 10px; border-radius: 20px; font-size: 14px; }}
            .card {{ background: #334155; padding: 18px; border-radius: 8px; margin-bottom: 20px; }}
            pre {{ background: #0f172a; padding: 16px; border-radius: 6px; overflow-x: auto; color: #a5f3fc; }}
            a {{ color: #38bdf8; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>❄️ Snowflake Emulator <span class="badge">Running</span></h1>
            <p>Clean-room local emulator for Snowflake Data Cloud with wire-protocol support.</p>
            
            <div class="card">
                <h3>Connection Details</h3>
                <ul>
                    <li><strong>Host:</strong> localhost</li>
                    <li><strong>Port:</strong> {settings.port}</li>
                    <li><strong>Protocol:</strong> HTTP</li>
                    <li><strong>Default Database:</strong> {settings.default_database}</li>
                    <li><strong>Default Schema:</strong> {settings.default_schema}</li>
                    <li><strong>Default Warehouse:</strong> {settings.default_warehouse}</li>
                    <li><strong>Default Role:</strong> {settings.default_role}</li>
                </ul>
            </div>

            <div class="card">
                <h3>Python Connector Snippet</h3>
                <pre>import snowflake.connector

conn = snowflake.connector.connect(
    user="{settings.default_user}",
    password="password",
    account="emulator",
    host="localhost",
    port={settings.port},
    protocol="http",
    insecure_mode=True,
    database="{settings.default_database}",
    schema="{settings.default_schema}",
    warehouse="{settings.default_warehouse}",
    role="{settings.default_role}"
)
cur = conn.cursor()
cur.execute("SELECT CURRENT_DATABASE(), CURRENT_ROLE(), CURRENT_TIMESTAMP()")
print(cur.fetchall())</pre>
            </div>
            <p><a href="/docs">Interactive OpenAPI (Swagger) Documentation &rarr;</a></p>
        </div>
    </body>
    </html>
    """
