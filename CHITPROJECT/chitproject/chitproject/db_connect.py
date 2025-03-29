import psycopg2

# Database connection parameters
DB_NAME = "your_database"
DB_USER = "your_username"
DB_PASSWORD = "your_password"
DB_HOST = "localhost"  # Change if using a remote server
DB_PORT = "5432"

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    # Create a cursor object
    cur = conn.cursor()

    # Execute a test query
    cur.execute("SELECT version();")
    db_version = cur.fetchone()

    print("Connected to PostgreSQL:", db_version)

    # Close the cursor and connection
    cur.close()
    conn.close()

except Exception as e:
    print("Error connecting to PostgreSQL:", e)
