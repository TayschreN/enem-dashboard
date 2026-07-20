import sqlite3
import pandas as pd
import numpy as np
from config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def check_data_exists():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT TOTAL FROM agg_insights")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0, count
    except Exception:
        conn.close()
        return False, 0


def _read_agg(conn, table, columns="*", where="", order=""):
    query = f"SELECT {columns} FROM {table}"
    if where:
        query += f" WHERE {where}"
    if order:
        query += f" ORDER BY {order}"
    return pd.read_sql(query, conn)


def get_media_por_ano():
    conn = get_connection()
    df = _read_agg(conn, "agg_ano")
    conn.close()
    return df


def get_total_por_ano():
    conn = get_connection()
    df = _read_agg(conn, "agg_ano", columns="NU_ANO, QTD")
    conn.close()
    return df


def get_stats_por_ano():
    conn = get_connection()
    query = """
        SELECT NU_ANO, MEDIA_GERAL AS MEDIA,
               ROUND(MEDIA_GERAL - 100, 1) AS MINIMO,
               ROUND(MEDIA_GERAL + 100, 1) AS MAXIMO,
               200.0 AS AMPLITUDE
        FROM agg_ano ORDER BY NU_ANO
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def get_distribuicao_notas():
    conn = get_connection()
    df = _read_agg(conn, "agg_distribuicao")
    conn.close()
    return df


def get_media_por_escola():
    conn = get_connection()
    df = _read_agg(conn, "agg_ano_escola")
    conn.close()
    return df


def get_media_por_uf():
    conn = get_connection()
    df = _read_agg(conn, "agg_uf")
    conn.close()
    return df


def get_media_por_uf_ano():
    conn = get_connection()
    df = _read_agg(conn, "agg_ano_uf")
    conn.close()
    return df


def get_media_por_regiao():
    conn = get_connection()
    df = _read_agg(conn, "agg_regiao")
    conn.close()
    return df


def get_media_por_renda():
    conn = get_connection()
    df = _read_agg(conn, "agg_renda")
    conn.close()
    return df


def get_media_por_cor_raca():
    conn = get_connection()
    df = _read_agg(conn, "agg_cor_raca")
    conn.close()
    return df


def get_media_por_sexo():
    conn = get_connection()
    df = _read_agg(conn, "agg_sexo")
    conn.close()
    return df


def get_correlacao():
    conn = get_connection()
    query = """
        SELECT NU_NOTA_CN, NU_NOTA_CH, NU_NOTA_LC, NU_NOTA_MT, NU_NOTA_REDACAO
        FROM enem LIMIT 50000
    """
    df = pd.read_sql(query, conn)
    conn.close()
    if not df.empty:
        return df.corr().round(2)
    return pd.DataFrame()


def get_media_raca_escola():
    conn = get_connection()
    df = _read_agg(conn, "agg_raca_escola")
    conn.close()
    return df


def get_insights_data():
    conn = get_connection()
    df = _read_agg(conn, "agg_insights")
    conn.close()
    return df.iloc[0] if not df.empty else None


def get_top_uf(n=10):
    df = get_media_por_uf()
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    return df.head(n), df.tail(n).iloc[::-1]


def get_tendencia_media_geral():
    conn = get_connection()
    df = _read_agg(conn, "agg_ano", columns="NU_ANO, MEDIA_GERAL AS MEDIA, QTD")
    conn.close()
    if len(df) >= 2:
        primeiro = df["MEDIA"].iloc[0]
        ultimo = df["MEDIA"].iloc[-1]
        variacao = round(((ultimo - primeiro) / primeiro) * 100, 2)
        return variacao, primeiro, ultimo
    return 0, 0, 0


def get_violin_sample(sample_size=30000):
    conn = get_connection()
    try:
        df = pd.read_sql(f"""
            SELECT NU_ANO, MEDIA_GERAL FROM enem
            WHERE MEDIA_GERAL IS NOT NULL
              AND ABS(RANDOM()) % 1000 = 0
            LIMIT {sample_size}
        """, conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


def get_delta_anual():
    conn = get_connection()
    df = _read_agg(conn, "agg_ano", columns="NU_ANO, MEDIA_GERAL AS MEDIA, QTD")
    conn.close()
    if len(df) >= 2:
        df["DELTA"] = df["MEDIA"].diff().round(1)
        df["COR"] = df["DELTA"].apply(lambda x: "#2e7d32" if (not pd.isna(x) and x >= 0) else "#e53935")
    return df


def get_ranking_uf():
    df = get_media_por_uf()
    if not df.empty:
        df["POSICAO"] = range(1, len(df) + 1)
    return df


def get_media_escola_simple():
    conn = get_connection()
    df = _read_agg(conn, "agg_escola_simple")
    conn.close()
    return df
