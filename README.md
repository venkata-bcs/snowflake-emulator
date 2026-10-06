# ❄️ Snowflake Emulator

> by Venkata Bhattaram


[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](Dockerfile)
[![Clean Room](https://img.shields.io/badge/Design-Clean--Room-orange.svg)](#-legal-disclosures-disclaimers--clean-room-compliance)
[![Tests](https://img.shields.io/badge/Tests-Passing-success.svg)](#-testing)

An open-source, **clean-room, zero-cloud-cost local Snowflake emulator** container designed for local development, integration testing, and CI/CD pipelines.

Test and debug your **Snowflake SQL queries, Snowpark DataFrames, Snowpipe ingestion pipelines, external stages (S3 / MinIO / Azure), and Data Governance policies** locally—without incurring cloud warehouse costs or managing live Snowflake credentials.

---

## 📑 Table of Contents

- [⚖️ Legal Disclosures, Disclaimers & Clean-Room Compliance](#️-legal-disclosures-disclaimers--clean-room-compliance)
- [✨ Feature Implementation Checklist](#-feature-implementation-checklist)
  - [🗄️ Snowflake SQL Engine & Dialect](#️-snowflake-sql-engine--dialect)
  - [📊 Information Schema & Metadata Catalog](#-information-schema--metadata-catalog)
  - [🚀 Snowpipe Continuous Ingestion](#-snowpipe-continuous-ingestion)
  - [🐍 Snowpark & DataFrame Compatibility](#-snowpark--dataframe-compatibility)
  - [🛡️ Data Governance, RBAC & Security Policies](#️-data-governance-rbac--security-policies)
  - [☁️ Storage Integrations & Stages (S3, MinIO, Azure, Local)](#️-storage-integrations--stages-s3-minio-azure-local)
  - [🔌 Wire Protocol & Client Drivers](#-wire-protocol--client-drivers)
  - [🐳 Containerization & Developer Experience](#-containerization--developer-experience)
- [🏛️ Architecture](#️-architecture)
- [🚀 Quick Start](#-quick-start)
  - [Option A: Docker Compose (Recommended)](#option-a-docker-compose-recommended)
  - [Option B: Standalone Docker](#option-b-standalone-docker)
  - [Option C: Local Python Environment](#option-c-local-python-environment)
- [🔌 Connecting with Clients & Drivers](#-connecting-with-clients--drivers)
  - [1. Snowflake Python Connector](#1-snowflake-python-connector)
  - [2. SQLAlchemy & SnowSQL](#2-sqlalchemy--snowsql)
  - [3. Direct REST API / Curl](#3-direct-rest-api--curl)
- [⚙️ Configuration Options](#️-configuration-options)
- [🗺️ Project Roadmap](#️-project-roadmap)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ⚖️ Legal Disclosures, Disclaimers & Clean-Room Compliance

### **IMPORTANT**
> **Please read these legal notices and disclaimers carefully prior to using, distributing, or contributing to this repository.**

### 1. Trademark Disclaimer
* **Snowflake®**, **Snowpark®**, **Snowpipe®**, and related names, logos, and marks are registered trademarks or trademarks of **Snowflake Inc.** in the United States and other jurisdictions.
* This project is an **independent, community-driven, open-source project** and is **NOT affiliated with, sponsored by, endorsed by, maintained by, or in any way officially associated with Snowflake Inc.**
* All references to "Snowflake" within this repository are solely for identification, descriptive compatibility, and interoperability purposes under fair use.

### 2. Clean-Room Implementation & Interoperability
* **Clean-Room Specification**: This emulator is constructed exclusively via **clean-room reverse-engineering principles** relying solely on publicly available reference documentation, syntax definitions, public REST API schemas, and standard SQL specifications.
* **No Proprietary Code**: This repository contains **NO proprietary code, internal binaries, decompiled source code, or assets extracted from Snowflake Inc. systems or proprietary distributions**.
* **Interoperability Right**: Development adheres to established legal doctrines governing software interoperability under U.S. (e.g., *Sega v. Accolade*, *Sony v. Connectix*, *Google LLC v. Oracle America, Inc.*) and European Union (Directive 2009/24/EC on legal protection of computer programs) copyright laws protecting interface implementation.

### 3. SaaS Terms of Service & EULA Compliance
* The authors and contributors have **not** violated Snowflake's Terms of Service, EULAs, or Acceptable Use Policies to produce this software.
* No live Snowflake cloud infrastructure was subjected to unauthorized penetration, packet tampering, or decompilation to build this engine.

### 4. Non-Circumvention & GitHub Terms of Service Compliance
* This software is intended strictly for **local integration testing, CI/CD verification, and educational prototyping**.
* It is **not** an exploit, bypass tool, or copyright infringement vehicle under the Digital Millennium Copyright Act (DMCA) or GitHub Community Guidelines.

---

## ✨ Feature Implementation Checklist

Key:
- `[x] ✅ 🟢` **Implemented / Ready**
- `[ ] ⏳ 🟡` **In Progress / Roadmap**
- `[ ] ⚪ 🔜` **Future Consideration**

### 🗄️ Snowflake SQL Engine & Dialect

| Status | Feature | Icon | Description |
|:---:|:---|:---:|:---|
| [x] ✅ | **Session & Context Management** | 🔄 | `USE ROLE`, `USE WAREHOUSE`, `USE DATABASE`, `USE SCHEMA` |
| [x] ✅ | **Session Context Functions** | 🔍 | `CURRENT_USER()`, `CURRENT_ROLE()`, `CURRENT_DATABASE()`, `CURRENT_SCHEMA()`, `CURRENT_WAREHOUSE()`, `CURRENT_TIMESTAMP()`, `VERSION()` |
| [x] ✅ | **DDL Operations** | 🏗️ | `CREATE / DROP / ALTER DATABASE`, `SCHEMA`, `TABLE` (`TEMPORARY`, `TRANSIENT`), `VIEW` |
| [x] ✅ | **DML Operations** | ✍️ | `INSERT INTO`, `SELECT`, `UPDATE`, `DELETE`, `MERGE INTO`, `TRUNCATE TABLE` |
| [x] ✅ | **Semi-Structured Data (`VARIANT`)** | 🧩 | Native `VARIANT`, `ARRAY`, `OBJECT`, colon notation (`v:key::string`, `v['key']`), `PARSE_JSON()`, `TO_JSON()`, `OBJECT_CONSTRUCT()` |
| [x] ✅ | **Flattening & Lateral Projections** | 📐 | `FLATTEN(input => ...)` and `LATERAL FLATTEN` table functions |
| [x] ✅ | **Snowflake Built-in Functions** | ⚙️ | `IFF()`, `NVL()`, `NVL2()`, `ZEROIFNULL()`, `DATEADD()`, `DATEDIFF()`, `DATE_TRUNC()`, `TRY_CAST()`, `SPLIT()`, `GET_PATH()` |
| [x] ✅ | **SQL Dialect Transpiler** | 🔀 | SQLGlot-powered engine transpiling Snowflake dialect to DuckDB vectorized OLAP engine |
| [ ] ⏳ | **Time Travel Emulation** | ⏳ | Syntax simulation for `SELECT ... AT(TIMESTAMP => ...)` and `BEFORE(OFFSET => ...)` |
| [ ] ⏳ | **Multi-Statement Transactions** | 🔒 | `BEGIN`, `COMMIT`, `ROLLBACK` transaction blocks |

---

### 📊 Information Schema & Metadata Catalog

| Status | Feature | Icon | Description |
|:---:|:---|:---:|:---|
| [x] ✅ | **`INFORMATION_SCHEMA.DATABASES`** | 🗂️ | Metadata view listing all available databases |
| [x] ✅ | **`INFORMATION_SCHEMA.SCHEMATA`** | 🗂️ | Metadata view of schemas in current/specified database |
| [x] ✅ | **`INFORMATION_SCHEMA.TABLES`** | 📋 | Metadata view of user and system tables and views |
| [x] ✅ | **`INFORMATION_SCHEMA.COLUMNS`** | 📑 | Column names, data types, nullability, ordinal positions |
| [x] ✅ | **`INFORMATION_SCHEMA.STAGES`** | 📦 | Stage locations, credentials metadata, stage types |
| [x] ✅ | **`INFORMATION_SCHEMA.PIPES`** | 🚰 | Snowpipe definitions, stages, and notification status |
| [x] ✅ | **`SHOW DATABASES / SCHEMAS / TABLES`** | 👁️ | Snowflake `SHOW` command format returning standard column sets |
| [x] ✅ | **`SHOW STAGES / PIPES / WAREHOUSES`** | 👁️ | Snowflake `SHOW` inspection for infrastructure objects |
| [x] ✅ | **`DESCRIBE TABLE / STAGE / PIPE`** | 📝 | `DESC TABLE <name>` and `DESC STAGE <name>` metadata schemas |
| [ ] ⏳ | **`ACCOUNT_USAGE` Views** | 📈 | Extended usage and history views (e.g. `QUERY_HISTORY`, `STORAGE_USAGE`) |

---

### 🚀 Snowpipe Continuous Ingestion

| Status | Feature | Icon | Description |
|:---:|:---|:---:|:---|
| [x] ✅ | **`CREATE PIPE` DDL** | 🚰 | Syntax parser for `CREATE PIPE <pipe_name> AS COPY INTO <table> FROM @<stage>` |
| [x] ✅ | **Snowpipe REST API (`insertFiles`)** | 📡 | `POST /v1/data/pipes/{pipeName}/insertFiles` endpoint to queue files |
| [x] ✅ | **Snowpipe Status (`insertReport`)** | 📊 | `GET /v1/data/pipes/{pipeName}/insertReport` query report of file ingest |
| [x] ✅ | **Load History (`loadHistoryScan`)** | 📜 | `GET /v1/data/pipes/{pipeName}/loadHistoryScan` load history window inspection |
| [x] ✅ | **Simulated Auto-Ingest Engine** | ⚡ | Immediate background ingestion of staged files into destination tables |
| [ ] ⏳ | **Cloud Storage Event Triggers** | 🔔 | MinIO / AWS S3 SQS / SNS webhook notifications to trigger pipe ingest |
| [ ] ⏳ | **`SYSTEM$PIPE_STATUS`** | 🩺 | Built-in system function for inspecting execution health of a pipe |

---

### 🐍 Snowpark & DataFrame Compatibility

| Status | Feature | Icon | Description |
|:---:|:---|:---:|:---|
| [x] ✅ | **Snowpark Session Connection Handshake** | 🤝 | Connect via `Session.builder.configs({...}).create()` |
| [x] ✅ | **DataFrame SQL Translation** | 🧮 | DataFrame queries, filtering, aggregations executed over local engine |
| [x] ✅ | **DataFrame `write.save_as_table`** | 💾 | Direct creation and population of tables via DataFrame writers |
| [ ] ⏳ | **Python Stored Procedures** | 🐍 | `CREATE PROCEDURE ... LANGUAGE PYTHON` execution sandbox |
| [ ] ⏳ | **Python UDF Registration** | 🧪 | `@udf` decorator registration and vectorized function execution |
| [ ] ⏳ | **Snowpark Stored Procedure File Uploads**| 📁 | Stage-based Python dependency imports |

---

### 🛡️ Data Governance, RBAC & Security Policies

| Status | Feature | Icon | Description |
|:---:|:---|:---:|:---|
| [x] ✅ | **Standard Role System** | 👑 | Pre-configured `ACCOUNTADMIN`, `SYSADMIN`, `SECURITYADMIN`, `USERADMIN`, `PUBLIC` |
| [x] ✅ | **Role Switching** | 🎭 | `USE ROLE <role_name>` validation and session role tracking |
| [x] ✅ | **Grant & Revoke Simulation** | 🔑 | `GRANT <privilege> ON <object> TO ROLE <role>` tracking and `SHOW GRANTS` |
| [x] ✅ | **Column Masking Policies** | 🎭 | `CREATE MASKING POLICY`, column masking rule storage and projection masking |
| [x] ✅ | **Row Access Policies** | 🛡️ | `CREATE ROW ACCESS POLICY`, row filtering enforcement simulation |
| [x] ✅ | **Object Tagging** | 🏷️ | `CREATE TAG`, `ALTER ... SET TAG <name> = '<value>'`, tag inspection |

---

### ☁️ Storage Integrations & Stages (S3, MinIO, Azure, Local)

| Status | Feature | Icon | Description |
|:---:|:---|:---:|:---|
| [x] ✅ | **Local Internal Stages** | 💻 | `@~` user stages, `@%table` table stages, and named local stages (`@my_stage`) |
| [x] ✅ | **MinIO / AWS S3 External Stages** | 🪣 | `CREATE STAGE <name> URL='s3://bucket/path'` with S3/MinIO endpoint integration |
| [x] ✅ | **Azure Blob / ADLS Gen2 Stages** | 🔷 | `CREATE STAGE <name> URL='azure://container/path'` emulation |
| [x] ✅ | **`LIST @<stage>`** | 📂 | List files, sizes, md5 hashes, and last modified timestamps |
| [x] ✅ | **`COPY INTO <table> FROM @<stage>`** | 📥 | Ingest CSV, JSON, Parquet from stages with options (`FILES`, `FILE_FORMAT`, `PATTERN`) |
| [x] ✅ | **`COPY INTO @<stage> FROM <table>`** | 📤 | Unload query results to files in stages |
| [x] ✅ | **`REMOVE @<stage>/<file>`** | 🗑️ | Delete staged files from local or cloud stage storage |
| [ ] ⏳ | **`PUT` & `GET` Wire Commands** | ⬆️ | Wire-level stage file upload/download protocol support |

---

### 🔌 Wire Protocol & Client Drivers

| Status | Feature | Icon | Description |
|:---:|:---|:---:|:---|
| [x] ✅ | **Login & Authentication Endpoint** | 🔐 | `POST /session/v1/login-request` handling session token issuance |
| [x] ✅ | **Query Execution Endpoint** | ⚡ | `POST /queries/v1/query-request` returning Snowflake JSON chunk result schema |
| [x] ✅ | **Session Keepalive & Teardown** | 💓 | `POST /session/v1/heartbeat`, `POST /session/v1/close-session` |
| [x] ✅ | **`snowflake-connector-python` Support** | 🐍 | First-class compatibility with official Python connector |
| [x] ✅ | **SQLAlchemy Dialect Compatibility** | 🗄️ | Works with `snowflake-sqlalchemy` driver |
| [ ] ⏳ | **Arrow Result Format** | 🏹 | Base64 Arrow stream chunking for ultra-large query results |
| [ ] ⏳ | **DBeaver / JDBC Driver Emulation** | ☕ | Extended wire protocol support for generic JDBC/ODBC client drivers |

---

### 🐳 Containerization & Developer Experience

| Status | Feature | Icon | Description |
|:---:|:---|:---:|:---|
| [x] ✅ | **Standalone Docker Image** | 🐳 | Compact, single-layer Docker container with zero external SaaS dependencies |
| [x] ✅ | **Docker Compose Environment** | 🐙 | One-command start with MinIO S3 bucket, Web UI, and emulator services |
| [x] ✅ | **In-Memory & Persistent Modes** | 💾 | Run ephemeral in-memory or persist data to a local DuckDB file volume |
| [x] ✅ | **Healthcheck & REST Endpoints** | 🩺 | `GET /health` and `GET /status` monitoring |
| [x] ✅ | **Web UI Explorer** | 🖥️ | Simple built-in dashboard to test queries and inspect stages |

---

## 🏛️ Architecture

The emulator sits transparently between your applications/drivers and a local high-performance columnar engine:

```mermaid
flowchart TD
    subgraph Clients["Clients & Tools"]
        PC["snowflake-connector-python"]
        SP["Snowpark Python"]
        DB["DBeaver / BI Tools"]
        CURL["cURL / REST Clients"]
    end

    subgraph Emulator["Snowflake Emulator Container (:8080)"]
        subgraph Wire["Snowflake REST Protocol Layer"]
            AUTH["/session/v1/login-request"]
            QUERY["/queries/v1/query-request"]
            PIPE["/v1/data/pipes/..."]
        end

        subgraph Core["Emulation Core"]
            SESS["Session & Context Manager"]
            TRANS["SQLGlot Dialect Transpiler\n(Snowflake -> DuckDB)"]
            CAT["Catalog & Information Schema\n(Databases, Schemas, Tables)"]
            GOV["Data Governance & RBAC"]
        end

        subgraph StorageMgr["Storage & Staging Engine"]
            STAGE["Stage Manager (@stage)"]
            PIPE_ENG["Snowpipe Continuous Ingest"]
        end

        subgraph Engine["Local Engine"]
            DUCK["Vectorized Columnar Engine\n(DuckDB OLAP)"]
        end
    end

    subgraph Storage["Object Storage"]
        MINIO["MinIO (Local S3)"]
        LOCAL["Local Filesystem"]
        S3["AWS S3 / Azure Blob"]
    end

    PC --> AUTH
    PC --> QUERY
    SP --> QUERY
    DB --> QUERY
    CURL --> PIPE

    AUTH --> SESS
    QUERY --> TRANS
    TRANS --> CAT
    TRANS --> GOV
    TRANS --> STAGE
    STAGE --> DUCK
    PIPE --> PIPE_ENG
    PIPE_ENG --> STAGE
    CAT --> DUCK

    STAGE --> MINIO
    STAGE --> LOCAL
    STAGE --> S3
```

---

## 🚀 Quick Start

### Option A: Docker Compose (Recommended)

Spins up the Snowflake Emulator alongside MinIO (for local S3 storage):

```bash
# Clone the repository
git clone https://github.com/venkata-bcs/snowflake-emulator.git
cd snowflake-emulator

# Launch emulator and MinIO S3 store
docker compose up -d
```

* **Snowflake Emulator API**: `http://localhost:8080`
* **MinIO Console**: `http://localhost:9001` (user: `minioadmin`, pass: `minioadmin`)
* **MinIO S3 Endpoint**: `http://localhost:9000`

---

### Option B: Standalone Docker

Run just the emulator container:

```bash
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  --name snowflake-emulator \
  snowflake-emulator:latest
```

---

### Option C: Local Python Environment

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the emulator
python -m snowflake_emulator.app
```

The emulator is now listening on `http://127.0.0.1:8080`!

---

## 🔌 Connecting with Clients & Drivers

### 1. Snowflake Python Connector

Configure `snowflake-connector-python` to point to the local emulator:

```python
import snowflake.connector

# Connect to local Snowflake Emulator
conn = snowflake.connector.connect(
    user="ADMIN",
    password="password123",
    account="emulator",
    host="localhost",
    port=8080,
    protocol="http",
    insecure_mode=True,
    database="DEMO_DB",
    schema="PUBLIC",
    warehouse="COMPUTE_WH",
    role="ACCOUNTADMIN",
)

cursor = conn.cursor()

# Run Snowflake queries locally
cursor.execute("CREATE TABLE IF NOT EXISTS customers (id INT, name STRING, profile VARIANT)")
cursor.execute("INSERT INTO customers VALUES (1, 'Alice', PARSE_JSON('{\"tier\": \"gold\"}'))")

cursor.execute("SELECT id, name, profile:tier::string AS tier FROM customers")
for row in cursor.fetchall():
    print(row)
# Output: (1, 'Alice', 'gold')

cursor.close()
conn.close()
```

---

### 2. SQLAlchemy & SnowSQL

Using SQLAlchemy connection string:

```python
from sqlalchemy import create_engine

engine = create_engine(
    "snowflake://ADMIN:password@localhost:8080/DEMO_DB/PUBLIC?warehouse=COMPUTE_WH&role=ACCOUNTADMIN&protocol=http&insecure_mode=true"
)
```

---

### 3. Direct REST API / Curl

#### Health Check
```bash
curl http://localhost:8080/health
```

#### Snowpipe Ingest File Notification
```bash
curl -X POST http://localhost:8080/v1/data/pipes/MY_PIPE/insertFiles \
  -H "Content-Type: application/json" \
  -d '{"files": [{"path": "sales_2026_10_06.csv"}]}'
```

---

## ⚙️ Configuration Options

Configuration is managed via environment variables:

| Variable | Default | Description |
|:---|:---|:---|
| `EMULATOR_HOST` | `0.0.0.0` | Host IP interface to bind server |
| `EMULATOR_PORT` | `8080` | Port for the Snowflake REST wire protocol |
| `EMULATOR_DB_PATH` | `:memory:` | Local DuckDB path (or `:memory:` for ephemeral mode) |
| `DEFAULT_DATABASE` | `DEMO_DB` | Initial database name |
| `DEFAULT_SCHEMA` | `PUBLIC` | Initial schema name |
| `DEFAULT_ROLE` | `ACCOUNTADMIN` | Default active RBAC role |
| `DEFAULT_WAREHOUSE`| `COMPUTE_WH` | Default virtual warehouse |
| `S3_ENDPOINT_URL` | `http://localhost:9000` | S3 / MinIO storage endpoint |
| `AWS_ACCESS_KEY_ID` | `minioadmin` | S3 / MinIO access key |
| `AWS_SECRET_ACCESS_KEY` | `minioadmin` | S3 / MinIO secret key |
| `AWS_DEFAULT_REGION`| `us-east-1` | S3 region |

---

## 🗺️ Project Roadmap

- [x] ✅ 🏆 **Milestone 1: Wire Protocol & SQL Core**
  - [x] ✅ Implement `/session/v1/login-request` and `/queries/v1/query-request`
  - [x] ✅ Snowflake SQL dialect translation via SQLGlot to DuckDB
  - [x] ✅ Metadata `INFORMATION_SCHEMA` and `SHOW` commands
- [x] ✅ 🪣 **Milestone 2: Stages & Ingestion**
  - [x] ✅ Local and MinIO/S3 stage support (`CREATE STAGE`, `LIST @stage`)
  - [x] ✅ `COPY INTO <table> FROM @stage`
  - [x] ✅ Snowpipe REST API (`/v1/data/pipes/{pipe}/insertFiles`)
- [x] ✅ 🛡️ **Milestone 3: Data Governance & Security Mock**
  - [x] ✅ Roles, grants, masking policies, row access policies
- [ ] ⏳ 🐍 **Milestone 4: Extended Snowpark & Native Stored Procedures**
  - [ ] ⏳ Sandboxed Python stored procedure and UDF execution
- [ ] ⏳ 🏹 **Milestone 5: Arrow Stream Chunk Wire Optimization**
  - [ ] ⏳ Multi-gigabyte query result streaming via Arrow IPC chunks

---

## 🤝 Contributing

Contributions are warmly welcomed! Please ensure that:
1. All contributions follow **clean-room principles** (no decompiled or proprietary Snowflake assets).
2. All new features include unit tests in `tests/`.
3. Code follows PEP 8 style standards and includes type hints.

---

## 📄 License

This project is licensed under the **Apache License, Version 2.0**.
See the [LICENSE](LICENSE) file for complete terms and copyright notices.
