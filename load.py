import sqlite3
from config import DB_PATH


def load(df, table_name="enem", if_exists="replace"):
    conn = sqlite3.connect(DB_PATH)

    df.to_sql(table_name, conn, if_exists=if_exists, index=False, chunksize=1000)

    idx_cols = ["NU_ANO", "SG_UF_PROVA", "DS_REGIAO", "DS_ESCOLA"]
    for col in idx_cols:
        if col in df.columns:
            try:
                conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{col.lower()} ON {table_name}({col})")
            except Exception:
                pass

    conn.commit()
    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    conn.close()

    print(f"Carregados {count:,} registros em {DB_PATH}")
    return count
