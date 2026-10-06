"""
Stage and COPY INTO demonstration with Snowflake Emulator.
"""

from pathlib import Path
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
        database="DEMO_DB",
        schema="PUBLIC",
    )
    cur = conn.cursor()

    print("--- 1. Create Stage ---")
    cur.execute("CREATE STAGE IF NOT EXISTS my_stage")
    print("Stage created.")

    # Create local file in the stage folder
    stage_dir = Path("./stage_storage/my_stage")
    stage_dir.mkdir(parents=True, exist_ok=True)
    sample_file = stage_dir / "sample_sales.csv"
    sample_file.write_text("id,region,sales\n101,US-EAST,5400\n102,US-WEST,3200\n103,EU-CENTRAL,8900\n")
    print(f"Sample data written to {sample_file}")

    print("\n--- 2. LIST @my_stage ---")
    cur.execute("LIST @my_stage")
    for file_info in cur.fetchall():
        print("File:", file_info)

    print("\n--- 3. Create Target Table ---")
    cur.execute("CREATE TABLE IF NOT EXISTS regional_sales (id INT, region STRING, sales INT)")

    print("\n--- 4. COPY INTO Table FROM @my_stage ---")
    cur.execute("COPY INTO regional_sales FROM @my_stage FILES=('sample_sales.csv')")
    for load_stat in cur.fetchall():
        print("Load Result:", load_stat)

    print("\n--- 5. Query Loaded Data ---")
    cur.execute("SELECT region, SUM(sales) AS total_sales FROM regional_sales GROUP BY region ORDER BY total_sales DESC")
    for r in cur.fetchall():
        print(r)

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
