import os
from contextlib import contextmanager

@contextmanager
def connection():
    import psycopg
    from psycopg.rows import dict_row
    dsn = os.environ.get('DATABASE_URL', '')
    if not dsn or not dsn.startswith('postgresql://'):
        raise RuntimeError('DATABASE_URL must point to private PostgreSQL')
    with psycopg.connect(dsn, row_factory=dict_row, connect_timeout=5) as conn:
        yield conn

def one(conn, query, params=()):
    return conn.execute(query, params).fetchone()

def all_rows(conn, query, params=()):
    return conn.execute(query, params).fetchall()
