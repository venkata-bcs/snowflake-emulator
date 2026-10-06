"""
Basic queries demonstration with Snowflake Emulator.
Requires running emulator on http://localhost:8080.
"""

import snowflake.connector

def main():
    print("Connecting to local Snowflake Emulator...")
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
        warehouse="COMPUTE_WH",
        role="ACCOUNTADMIN",
    )
    cur = conn.cursor()

    # 1. Inspect session context
    print("\n--- 1. Session Context ---")
    cur.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE(), VERSION()")
    print("Context:", cur.fetchone())

    # 2. Create Table
    print("\n--- 2. Create Table ---")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS customer_orders (
        id INT,
        customer_name STRING,
        order_details VARIANT,
        total_amount NUMBER(10, 2)
    )
    """)
    print("Table created.")

    # 3. Insert Semi-Structured Data
    print("\n--- 3. Insert Semi-Structured Data ---")
    cur.execute("""
    INSERT INTO customer_orders VALUES 
        (1, 'Alice Smith', PARSE_JSON('{"tier": "platinum", "items": 3}'), 149.99),
        (2, 'Bob Jones', PARSE_JSON('{"tier": "silver", "items": 1}'), 29.50)
    """)
    print("Data inserted.")

    # 4. Query with Snowflake Colon Path Syntax
    print("\n--- 4. Query Colon Notation ---")
    cur.execute("""
    SELECT 
        id,
        customer_name,
        order_details:tier::string AS membership_tier,
        total_amount,
        IFF(total_amount > 100, 'HIGH', 'STANDARD') AS order_category
    FROM customer_orders
    ORDER BY id
    """)
    for row in cur.fetchall():
        print(row)

    # 5. Metadata SHOW and DESCRIBE
    print("\n--- 5. SHOW TABLES ---")
    cur.execute("SHOW TABLES")
    for tbl in cur.fetchall():
        print(f"Table: {tbl[1]} | DB: {tbl[2]} | Schema: {tbl[3]}")

    cur.close()
    conn.close()
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    main()
