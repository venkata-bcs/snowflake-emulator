"""
Snowflake wire protocol models and serialization helpers.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class SnowflakeParameter(BaseModel):
    name: str
    value: Any


class SnowflakeColumnType(BaseModel):
    name: str
    database: Optional[str] = ""
    schema_name: Optional[str] = Field(default="", serialization_alias="schema")
    table: Optional[str] = ""
    type: str  # 'text', 'fixed', 'real', 'boolean', 'date', 'timestamp_ntz', 'variant', etc.
    scale: Optional[int] = None
    precision: Optional[int] = None
    nullable: bool = True
    byteLength: Optional[int] = None
    length: Optional[int] = None


class QueryResponseData(BaseModel):
    parameters: List[SnowflakeParameter] = Field(default_factory=list)
    rowtype: List[SnowflakeColumnType] = Field(default_factory=list)
    rowset: List[List[Any]] = Field(default_factory=list)
    total: int = 0
    returned: int = 0
    queryId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    databaseProvider: Optional[str] = None
    finalDatabaseName: str = "DEMO_DB"
    finalSchemaName: str = "PUBLIC"
    finalWarehouseName: str = "COMPUTE_WH"
    finalRoleName: str = "ACCOUNTADMIN"
    numberOfBinds: int = 0
    statementTypeId: int = 4096
    version: int = 1
    sqlState: str = "00000"
    queryResultFormat: str = "json"


class SnowflakeResponse(BaseModel):
    data: Optional[Any] = None
    code: Optional[str] = None
    message: Optional[str] = None
    success: bool = True
    headers: Optional[Dict[str, Any]] = None


def create_success_response(data: Any) -> SnowflakeResponse:
    return SnowflakeResponse(
        data=data,
        code=None,
        message=None,
        success=True
    )


def create_error_response(message: str, code: str = "002003", sql_state: str = "42000") -> SnowflakeResponse:
    return SnowflakeResponse(
        data={
            "sqlState": sql_state,
            "queryId": str(uuid.uuid4()),
        },
        code=code,
        message=message,
        success=False
    )
