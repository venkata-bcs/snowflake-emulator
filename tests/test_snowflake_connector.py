"""
Integration test connecting with official snowflake-connector-python client.
"""

import subprocess
import sys
import time
import httpx
import pytest
import snowflake.connector

TEST_PORT = 8585


@pytest.fixture(scope="module")
def running_server():
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "snowflake_emulator.app:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(TEST_PORT),
        "--log-level",
        "warning",
    ]
    proc = subprocess.Popen(cmd)
    
    # Wait for server to respond to healthcheck
    ready = False
    for _ in range(30):
        try:
            r = httpx.get(f"http://127.0.0.1:{TEST_PORT}/health", timeout=1.0)
            if r.status_code == 200:
                ready = True
                break
        except Exception:
            pass
        time.sleep(0.2)

    assert ready, "Snowflake emulator failed to start in time"
    yield f"http://127.0.0.1:{TEST_PORT}"
    
    proc.terminate()
    proc.wait(timeout=5)


def test_snowflake_python_connector(running_server):
    conn = snowflake.connector.connect(
        user="test_user",
        password="test_password",
        account="emulator",
        host="127.0.0.1",
        port=TEST_PORT,
        protocol="http",
        disable_ocsp_checks=True,
        database="DEMO_DB",
        schema="PUBLIC",
        warehouse="COMPUTE_WH",
        role="ACCOUNTADMIN",
    )
    assert conn is not None

    cur = conn.cursor()

    # 1. Test context query
    cur.execute("SELECT CURRENT_DATABASE(), CURRENT_ROLE(), VERSION()")
    row = cur.fetchone()
    assert row[0] == "DEMO_DB"
    assert row[1] == "ACCOUNTADMIN"
    assert row[2] == "8.45.0"

    # 2. Test DDL and DML
    cur.execute("CREATE TABLE test_connector (id INT, label STRING)")
    cur.execute("INSERT INTO test_connector VALUES (1, 'Alpha'), (2, 'Beta')")

    cur.execute("SELECT id, label FROM test_connector ORDER BY id")
    rows = cur.fetchall()
    assert len(rows) == 2
    assert rows[0] == (1, "Alpha")
    assert rows[1] == (2, "Beta")

    cur.close()
    conn.close()
