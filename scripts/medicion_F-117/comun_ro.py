# Conexiones de solo lectura para la medición F-117.
import os
import psycopg
import httpx


def pg():
    c = psycopg.connect(
        host=os.environ["F117_PG_HOST"], user=os.environ["F117_PG_USER"],
        password=os.environ["F117_PG_PASS"], dbname=os.environ["F117_PG_DB"],
        sslmode="require", options="-c default_transaction_read_only=on",
    )
    with c.cursor() as cur:
        cur.execute("SHOW transaction_read_only")
        v = cur.fetchone()[0]
    assert v == "on", f"transaction_read_only={v}"
    return c


def sigrid(sql, params, max_rows=500000):
    assert sql.lstrip().upper().startswith("SELECT")
    r = httpx.post(
        os.environ["F117_SIGRID_URL"].rstrip("/") + "/api/sql/read",
        headers={"x-functions-key": os.environ["F117_SIGRID_KEY"]},
        json={"database": "ruesma", "sql": sql, "parameters": params,
              "max_rows": max_rows, "timeout_seconds": 200},
        timeout=240,
    )
    r.raise_for_status()
    d = r.json()
    if d.get("truncated"):
        raise SystemExit("respuesta truncada: se para")
    return d["columns"], d["rows"]
