"""
Tests for Snowflake REST Wire Protocol API endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from snowflake_emulator.app import app


@pytest.mark.anyio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["engine"] == "duckdb"


@pytest.mark.anyio
async def test_login_and_query_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Login Request
        login_resp = await client.post(
            "/session/v1/login-request",
            json={"data": {"LOGIN_NAME": "admin", "PASSWORD": "password123"}},
            params={"databaseName": "DEMO_DB", "schemaName": "PUBLIC"}
        )
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        assert login_data["success"] is True
        token = login_data["data"]["token"]
        assert token is not None

        # 2. Query Request
        query_resp = await client.post(
            "/queries/v1/query-request",
            headers={"Authorization": f'Snowflake Token="{token}"'},
            json={"sqlText": "SELECT 1 AS num, 'hello' AS greeting"}
        )
        assert query_resp.status_code == 200
        q_data = query_resp.json()
        assert q_data["success"] is True
        assert q_data["data"]["total"] == 1
        assert q_data["data"]["rowset"] == [["1", "hello"]]


@pytest.mark.anyio
async def test_snowpipe_rest_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Insert files notification
        pipe_resp = await client.post(
            "/v1/data/pipes/TEST_PIPE/insertFiles",
            json={"files": [{"path": "events_batch_1.csv"}]}
        )
        assert pipe_resp.status_code == 200
        assert pipe_resp.json()["completeResult"] is True

        # 2. Ingest report
        report_resp = await client.get("/v1/data/pipes/TEST_PIPE/insertReport")
        assert report_resp.status_code == 200
        report = report_resp.json()
        assert report["pipe"] == "TEST_PIPE"
        assert len(report["files"]) >= 1
        assert report["files"][0]["status"] == "LOADED"
