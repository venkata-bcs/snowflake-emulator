"""
Tests for SnowflakeEngine core SQL execution and session context.
"""

import pytest
from snowflake_emulator.engine import SnowflakeEngine


@pytest.fixture
def engine():
    return SnowflakeEngine()


def test_context_functions(engine):
    session = engine.create_session(database="TEST_DB", schema="TEST_SCHEMA", role="SYSADMIN")
    rowtypes, rows, total = engine.execute(
        "SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE(), VERSION()",
        session
    )
    assert total == 1
    assert rows[0][0] == "TEST_DB"
    assert rows[0][1] == "TEST_SCHEMA"
    assert rows[0][2] == "SYSADMIN"
    assert rows[0][3] == "8.45.0"


def test_session_switching(engine):
    session = engine.create_session()
    engine.execute("USE ROLE SECURITYADMIN", session)
    assert session.role == "SECURITYADMIN"

    engine.execute("USE DATABASE ANALYTICS_DB", session)
    assert session.database == "ANALYTICS_DB"

    engine.execute("USE SCHEMA CORE", session)
    assert session.schema == "CORE"


def test_ddl_and_dml(engine):
    session = engine.create_session()
    engine.execute("CREATE TABLE users (id INT, name STRING, active BOOLEAN)", session)
    engine.execute("INSERT INTO users VALUES (1, 'Alice', true), (2, 'Bob', false)", session)

    rowtypes, rows, total = engine.execute("SELECT id, name, active FROM users ORDER BY id", session)
    assert total == 2
    assert rows[0] == ["1", "Alice", "true"]
    assert rows[1] == ["2", "Bob", "false"]

    # Test update and delete
    engine.execute("UPDATE users SET active = false WHERE id = 1", session)
    _, rows, _ = engine.execute("SELECT active FROM users WHERE id = 1", session)
    assert rows[0][0] == "false"

    engine.execute("DELETE FROM users WHERE id = 2", session)
    _, rows, total = engine.execute("SELECT * FROM users", session)
    assert total == 1


def test_semi_structured_variant(engine):
    session = engine.create_session()
    engine.execute("CREATE TABLE events (id INT, payload VARIANT)", session)
    engine.execute(
        "INSERT INTO events VALUES (101, PARSE_JSON('{\"event\": \"click\", \"tier\": \"gold\"}'))",
        session
    )

    rowtypes, rows, total = engine.execute("SELECT id, payload:tier::string FROM events", session)
    assert total == 1
    assert rows[0][0] == "101"
    assert rows[0][1] == "gold"


def test_snowflake_functions(engine):
    session = engine.create_session()
    # Test IFF and NVL
    _, rows, _ = engine.execute("SELECT IFF(10 > 5, 'YES', 'NO'), NVL(NULL, 'DEFAULT')", session)
    assert rows[0] == ["YES", "DEFAULT"]


def test_show_commands(engine):
    session = engine.create_session()
    engine.execute("CREATE TABLE products (sku STRING, price INT)", session)

    rowtypes, rows, total = engine.execute("SHOW TABLES", session)
    assert total >= 1
    table_names = [r[1] for r in rows]
    assert "PRODUCTS" in table_names

    _, rows, total = engine.execute("SHOW DATABASES", session)
    assert total >= 1

    _, rows, total = engine.execute("SHOW ROLES", session)
    role_names = [r[1] for r in rows]
    assert "ACCOUNTADMIN" in role_names
    assert "SYSADMIN" in role_names


def test_describe_table(engine):
    session = engine.create_session()
    engine.execute("CREATE TABLE items (id INT, description STRING)", session)
    rowtypes, rows, total = engine.execute("DESCRIBE TABLE items", session)
    assert total == 2
    col_names = [r[0] for r in rows]
    assert "ID" in col_names
    assert "DESCRIPTION" in col_names
