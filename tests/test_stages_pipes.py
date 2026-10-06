"""
Tests for Stages, COPY INTO, and Snowpipe ingestion.
"""

from pathlib import Path
import pytest
from snowflake_emulator.engine import SnowflakeEngine


@pytest.fixture
def engine(tmp_path):
    eng = SnowflakeEngine()
    eng.stage_manager.local_root = tmp_path
    return eng


def test_stage_lifecycle_and_copy(engine):
    session = engine.create_session()

    # 1. Create Stage
    engine.execute("CREATE STAGE my_csv_stage", session)
    _, rows, total = engine.execute("SHOW STAGES", session)
    assert total >= 1
    assert any(r[1] == "MY_CSV_STAGE" for r in rows)

    # 2. Put a test CSV file in the stage
    csv_content = b"id,val\n10,foo\n20,bar\n"
    engine.stage_manager.save_staged_file("MY_CSV_STAGE", "data.csv", csv_content)

    # 3. LIST @stage
    _, rows, total = engine.execute("LIST @my_csv_stage", session)
    assert total == 1
    assert "data.csv" in rows[0][0]

    # 4. Create target table and COPY INTO
    engine.execute("CREATE TABLE target_data (id INT, val STRING)", session)
    _, rows, total = engine.execute("COPY INTO target_data FROM @my_csv_stage FILES=('data.csv')", session)
    assert total == 1
    assert rows[0][1] == "LOADED"

    # 5. Verify loaded data
    _, rows, total = engine.execute("SELECT id, val FROM target_data ORDER BY id", session)
    assert total == 2
    assert rows[0] == ["10", "foo"]
    assert rows[1] == ["20", "bar"]


def test_snowpipe_creation_and_history(engine):
    session = engine.create_session()

    # Create Pipe
    engine.execute("CREATE PIPE ingest_pipe AS COPY INTO target_tbl FROM @stg", session)
    _, rows, total = engine.execute("SHOW PIPES", session)
    assert total >= 1
    assert any(r[1] == "INGEST_PIPE" for r in rows)

    # Record load and verify report
    engine.pipe_manager.record_load("INGEST_PIPE", "file1.csv", "LOADED", rows_loaded=10)
    report = engine.pipe_manager.get_insert_report("INGEST_PIPE")
    assert report["pipe"] == "INGEST_PIPE"
    assert len(report["files"]) == 1
    assert report["files"][0]["rowsLoaded"] == 10
