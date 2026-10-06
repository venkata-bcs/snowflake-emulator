"""
Snowpipe continuous ingestion demonstration with REST API.
"""

import httpx
import snowflake.connector

def main():
    conn = snowflake.connector.connect(
        user="ADMIN",
        password="password123",
        account="emulator",
        host="localhost",
        port=8080,
        protocol="http",
        disable_ocsp_checks=True,
    )
    cur = conn.cursor()

    print("--- 1. Create Snowpipe via SQL ---")
    cur.execute("CREATE PIPE IF NOT EXISTS sales_pipe AS COPY INTO sales_table FROM @sales_stage")
    print("Pipe created.")

    cur.execute("SHOW PIPES")
    for pipe in cur.fetchall():
        print("Pipe:", pipe[1], "| Definition:", pipe[4])

    cur.close()
    conn.close()

    print("\n--- 2. Trigger Snowpipe REST Ingest Notification ---")
    with httpx.Client(base_url="http://localhost:8080") as client:
        resp = client.post(
            "/v1/data/pipes/SALES_PIPE/insertFiles",
            json={"files": [{"path": "incoming_batch_001.csv"}, {"path": "incoming_batch_002.csv"}]}
        )
        print("InsertFiles response:", resp.status_code, resp.json())

        print("\n--- 3. Query Ingestion Report ---")
        rep = client.get("/v1/data/pipes/SALES_PIPE/insertReport")
        print("InsertReport:", rep.json())

        print("\n--- 4. Query Load History ---")
        hist = client.get("/v1/data/pipes/SALES_PIPE/loadHistoryScan")
        print("LoadHistory:", hist.json())

if __name__ == "__main__":
    main()
