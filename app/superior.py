import psycopg2
import json

conn = psycopg2.connect(
    host="localhost",
    port="5433",
    database="pagila",
    user="postgres",
    password="example",
)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements;")
