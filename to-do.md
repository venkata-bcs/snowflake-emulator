# ❄️ snowflake-emulator To-Do & Roadmap 🚀

## 📋 Comprehensive Implementation Checklist ✅

- [x] ✅ 🐳 **Dockerization & Container Runtime**
  - [x] ✅ 📦 Lightweight standalone `Dockerfile` for local development
  - [x] ✅ 🐙 Complete `docker-compose.yml` bundling Emulator + MinIO local S3 storage
  - [x] ✅ 🩺 Built-in container healthcheck (`GET /health`) and status probes
  - [x] ✅ 💾 Persistent volume mounting (`/app/data`, `/app/stage_storage`)

- [x] ✅ 🗄️ **Snowflake DB Core Features & Engine**
  - [x] ✅ 🔄 **Session & Context Switching**: `USE ROLE`, `USE DATABASE`, `USE SCHEMA`, `USE WAREHOUSE`
  - [x] ✅ 🔍 **Context Introspection Functions**: `CURRENT_DATABASE()`, `CURRENT_SCHEMA()`, `CURRENT_ROLE()`, `CURRENT_USER()`, `CURRENT_WAREHOUSE()`, `CURRENT_TIMESTAMP()`, `VERSION()`
  - [x] ✅ 🏗️ **DDL Operations**: `CREATE TABLE`, `CREATE TRANSIENT TABLE`, `CREATE TEMPORARY TABLE`, `CREATE SCHEMA`, `CREATE DATABASE`, `DROP TABLE`, `ALTER TABLE`
  - [x] ✅ ✍️ **DML Operations**: `INSERT INTO`, `SELECT`, `UPDATE`, `DELETE`, `MERGE INTO`, `TRUNCATE TABLE`
  - [x] ✅ 🧩 **Semi-Structured Data (`VARIANT`)**: Native `VARIANT`, `ARRAY`, `OBJECT`, `PARSE_JSON()`, `TO_JSON()`, colon notation `col:field::string`
  - [x] ✅ ⚙️ **Snowflake Built-In Functions**: `IFF()`, `NVL()`, `NVL2()`, `ZEROIFNULL()`, `DATEADD()`, `DATEDIFF()`, `DATE_TRUNC()`, `TRY_CAST()`, `SPLIT()`
  - [x] ✅ 🔀 **SQL Dialect Transpiler**: Snowflake dialect transpiled to DuckDB vectorized OLAP engine via SQLGlot

- [x] ✅ 📊 **Metadata & Information Schema**
  - [x] ✅ 🗂️ **System Catalog Views**: `INFORMATION_SCHEMA.DATABASES`, `INFORMATION_SCHEMA.SCHEMATA`, `INFORMATION_SCHEMA.TABLES`, `INFORMATION_SCHEMA.COLUMNS`, `INFORMATION_SCHEMA.STAGES`, `INFORMATION_SCHEMA.PIPES`, `INFORMATION_SCHEMA.VIEWS`
  - [x] ✅ 👁️ **Snowflake SHOW Commands**: `SHOW DATABASES`, `SHOW SCHEMAS`, `SHOW TABLES`, `SHOW STAGES`, `SHOW PIPES`, `SHOW WAREHOUSES`, `SHOW ROLES`, `SHOW PARAMETERS`, `SHOW GRANTS`
  - [x] ✅ 📝 **DESCRIBE Commands**: `DESCRIBE TABLE <name>`, `DESCRIBE STAGE <name>`, `DESCRIBE PIPE <name>`

- [x] ✅ 🚀 **Snowpipe Continuous Ingestion**
  - [x] ✅ 🚰 **`CREATE PIPE` DDL**: `CREATE PIPE <pipe_name> AS COPY INTO <table> FROM @<stage>`
  - [x] ✅ 📡 **Snowpipe REST Ingest API**: `POST /v1/data/pipes/{pipe}/insertFiles` batch file queueing
  - [x] ✅ 📊 **Snowpipe Ingestion Reporting**: `GET /v1/data/pipes/{pipe}/insertReport`
  - [x] ✅ 📜 **Load History Inspection**: `GET /v1/data/pipes/{pipe}/loadHistoryScan`
  - [x] ✅ ⚡ **Auto-Ingest Pipeline Simulation**: Automatic file discovery and ingestion

- [x] ✅ 🐍 **Snowpark & DataFrame Compatibility**
  - [x] ✅ 🤝 **Session Handshake**: Full authentication handshake via `Session.builder.configs({...}).create()`
  - [x] ✅ 🧮 **DataFrame SQL Query Translation**: DataFrame transformations, filters, and aggregations executed locally
  - [x] ✅ 💾 **DataFrame Writers**: Direct table materialization via `write.save_as_table`

- [x] ✅ 🛡️ **Data Governance & Security**
  - [x] ✅ 👑 **Standard RBAC Roles**: Pre-seeded `ACCOUNTADMIN`, `SYSADMIN`, `SECURITYADMIN`, `USERADMIN`, `PUBLIC`
  - [x] ✅ 🎭 **Role Switching & Hierarchy**: `USE ROLE <role>` with validation
  - [x] ✅ 🔑 **Privilege Grants**: `GRANT <privilege> ON <object> TO ROLE <role>`, `SHOW GRANTS`
  - [x] ✅ 🎭 **Column Masking Policies**: `CREATE MASKING POLICY`, policy storage, and column binding
  - [x] ✅ 🛡️ **Row Access Policies**: `CREATE ROW ACCESS POLICY`, row filtering simulation
  - [x] ✅ 🏷️ **Object Tagging**: `CREATE TAG`, `ALTER ... SET TAG <name> = '<value>'`

- [x] ✅ ☁️ **Cloud Storage & Staging Integrations**
  - [x] ✅ 💻 **Internal Directory Stages**: `@~` user stages, `@%table` table stages, `@my_stage` named stages
  - [x] ✅ 🪣 **Amazon S3 & MinIO External Stages**: `CREATE STAGE <name> URL='s3://bucket/path'` with S3/MinIO endpoint integration
  - [x] ✅ 🔷 **Azure Blob & ADLS Gen2 Stages**: `CREATE STAGE <name> URL='azure://container/path'` emulation
  - [x] ✅ 📂 **`LIST @stage`**: File listing returning name, size, md5, and last modified timestamps
  - [x] ✅ 📥 **`COPY INTO <table> FROM @stage`**: Ingest CSV, JSON, Parquet from stages with options (`FILES`, `FILE_FORMAT`)
  - [x] ✅ 📤 **`COPY INTO @stage FROM <table>`**: Data unloading to stage files
  - [x] ✅ 🗑️ **`REMOVE @stage/<file>`**: Deleting staged files

- [x] ✅ 🔌 **Client Drivers & Wire Protocol**
  - [x] ✅ 🔐 **Login & Authentication**: `POST /session/v1/login-request` handling session tokens and parameters
  - [x] ✅ ⚡ **Query Execution**: `POST /queries/v1/query-request` returning Snowflake JSON chunk result schema
  - [x] ✅ 🛑 **Query Cancellation**: `POST /queries/v1/abort-request`
  - [x] ✅ 💓 **Session Lifecycle**: `POST /session/v1/heartbeat`, `POST /session/v1/close-session`
  - [x] ✅ 🐍 **Official Python Connector Compatibility**: Tested and verified with `snowflake-connector-python`
  - [x] ✅ 🗄️ **SQLAlchemy Support**: Verified with `snowflake-sqlalchemy`

- [x] ✅ ⚖️ **Legal, Copyright & Clean-Room Compliance**
  - [x] ✅ 📜 **Apache License 2.0**: Full [LICENSE](LICENSE) terms included
  - [x] ✅ 🏷️ **Trademark Disclaimers**: Explicit notice regarding Snowflake Inc. marks
  - [x] ✅ 🛡️ **Clean-Room Design Declaration**: 100% public documentation, zero proprietary binaries
  - [x] ✅ 🤝 **SaaS Terms of Service Compliance**: No scraping, probing, or decompiling of Snowflake SaaS
  - [x] ✅ 🌐 **GitHub Terms of Service Compliance**: Full compliance with GitHub Community Guidelines

---

## 🔮 Future Enhancements & Roadmap

- [ ] ⏳ 🐍 **Python Stored Procedures & UDF Sandbox**: `@udf` decorator execution inside container
- [ ] ⏳ 🏹 **Arrow Result Format**: Arrow stream chunking for multi-gigabyte queries
- [ ] ⏳ 🔔 **Cloud Storage Webhooks**: S3 / MinIO SQS / SNS webhook notifications triggering pipes
- [ ] ⏳ ⌛ **Time Travel Engine**: `AT(TIMESTAMP => ...)` historical state snapshots

---

## ⚖️ Key Legal Guardrails Reference

1. **Copyright Law: Emulating vs. Copying**
   - ✅ *Allowed*: Implementing a clean-room design. Under U.S. and EU copyright frameworks, software functionality, syntax, and APIs themselves are generally not copyrightable. Building your own code (e.g., in Python or Go) that intercepts Snowflake API endpoints and returns expected SQL formats is legal.
   - 🚫 *Forbidden*: You cannot copy any proprietary code, extract libraries from Snowflake drivers, or redistribute any of Snowflake's underlying systems.
2. **Contract Law: SaaS Terms of Service & EULAs**
   - ⚠️ *The Risk*: While copyright law often protects reverse engineering for interoperability under "Fair Use", contract law can override this. If you log into a real Snowflake account, you agree to their Terms of Service, which explicitly prohibit reverse-engineering or decompiling their platform to protect their trade secrets.
   - 🛡️ *Best Practice*: Ensure your emulator is built entirely by studying publicly available documentation (like SQL reference sheets and API descriptions) rather than decompiling, sniffing, or cracking the proprietary server software.
3. **Trademark Infringement**
   - ⚠️ *The Risk*: You cannot name or market your project in a way that tricks users into believing it is an official Snowflake product or that you are affiliated with Snowflake Inc.
   - 🛡️ *Best Practice*: Clearly state in your GitHub README that the project is an unofficial, independent emulator created solely for educational and local testing purposes. Avoid using the official Snowflake logo.
4. **GitHub Terms of Service**
   - 🌐 GitHub allows the hosting of educational emulators and developer tools. As long as your repository doesn't distribute cracked proprietary software or tools explicitly designed to bypass security authentication systems (malware/exploits), it adheres to GitHub's Community Guidelines.
