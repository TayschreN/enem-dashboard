import time
import sqlite3
import pandas as pd
from config import DB_PATH

def create_agg_table(conn, name, query):
    conn.execute(f"DROP TABLE IF EXISTS {name}")
    conn.execute(f"CREATE TABLE {name} AS {query}")
    cursor = conn.execute(f"SELECT COUNT(*) FROM {name}")
    count = cursor.fetchone()[0]
    print(f"  {name}: {count} rows")

def precompute():
    start = time.time()
    conn = sqlite3.connect(DB_PATH)

    print("Pre-computando agregacoes...")

    create_agg_table(conn, "agg_ano", """
        SELECT NU_ANO,
               ROUND(AVG(NU_NOTA_CN), 1) AS MEDIA_CN,
               ROUND(AVG(NU_NOTA_CH), 1) AS MEDIA_CH,
               ROUND(AVG(NU_NOTA_LC), 1) AS MEDIA_LC,
               ROUND(AVG(NU_NOTA_MT), 1) AS MEDIA_MT,
               ROUND(AVG(NU_NOTA_REDACAO), 1) AS MEDIA_REDACAO,
               ROUND(AVG(MEDIA_GERAL), 1) AS MEDIA_GERAL,
               COUNT(*) AS QTD
        FROM enem GROUP BY NU_ANO ORDER BY NU_ANO
    """)

    create_agg_table(conn, "agg_ano_escola", """
        SELECT NU_ANO, DS_ESCOLA,
               ROUND(AVG(MEDIA_GERAL), 1) AS MEDIA_GERAL,
               COUNT(*) AS QTD
        FROM enem
        WHERE DS_ESCOLA IN ('Publica', 'Privada')
        GROUP BY NU_ANO, DS_ESCOLA ORDER BY NU_ANO, DS_ESCOLA
    """)

    create_agg_table(conn, "agg_uf", """
        SELECT SG_UF_PROVA,
               ROUND(AVG(MEDIA_GERAL), 1) AS MEDIA_GERAL,
               COUNT(*) AS QTD
        FROM enem GROUP BY SG_UF_PROVA ORDER BY MEDIA_GERAL DESC
    """)

    create_agg_table(conn, "agg_ano_uf", """
        SELECT SG_UF_PROVA, NU_ANO,
               ROUND(AVG(MEDIA_GERAL), 1) AS MEDIA_GERAL,
               COUNT(*) AS QTD
        FROM enem GROUP BY SG_UF_PROVA, NU_ANO ORDER BY SG_UF_PROVA, NU_ANO
    """)

    create_agg_table(conn, "agg_regiao", """
        SELECT DS_REGIAO, NU_ANO,
               ROUND(AVG(MEDIA_GERAL), 1) AS MEDIA_GERAL,
               COUNT(*) AS QTD
        FROM enem
        WHERE DS_REGIAO != 'Desconhecido'
        GROUP BY DS_REGIAO, NU_ANO ORDER BY DS_REGIAO, NU_ANO
    """)

    create_agg_table(conn, "agg_renda", """
        SELECT Q006, DS_RENDA, DS_RENDA_ORDEM,
               ROUND(AVG(MEDIA_GERAL), 1) AS MEDIA_GERAL,
               COUNT(*) AS QTD
        FROM enem
        WHERE DS_RENDA_ORDEM IS NOT NULL AND DS_RENDA_ORDEM >= 0
        GROUP BY Q006, DS_RENDA, DS_RENDA_ORDEM ORDER BY DS_RENDA_ORDEM
    """)

    create_agg_table(conn, "agg_cor_raca", """
        SELECT NU_ANO, DS_COR_RACA,
               ROUND(AVG(MEDIA_GERAL), 1) AS MEDIA_GERAL,
               COUNT(*) AS QTD
        FROM enem GROUP BY NU_ANO, DS_COR_RACA ORDER BY NU_ANO, DS_COR_RACA
    """)

    create_agg_table(conn, "agg_sexo", """
        SELECT NU_ANO, DS_SEXO,
               ROUND(AVG(MEDIA_GERAL), 1) AS MEDIA_GERAL,
               COUNT(*) AS QTD
        FROM enem GROUP BY NU_ANO, DS_SEXO ORDER BY NU_ANO, DS_SEXO
    """)

    create_agg_table(conn, "agg_raca_escola", """
        SELECT DS_COR_RACA, DS_ESCOLA,
               ROUND(AVG(MEDIA_GERAL), 1) AS MEDIA_GERAL,
               COUNT(*) AS QTD
        FROM enem
        WHERE DS_ESCOLA IN ('Publica', 'Privada')
          AND DS_COR_RACA IN ('Branca', 'Preta', 'Parda')
        GROUP BY DS_COR_RACA, DS_ESCOLA ORDER BY DS_COR_RACA, DS_ESCOLA
    """)

    create_agg_table(conn, "agg_insights", """
        SELECT
            ROUND(AVG(MEDIA_GERAL), 1) AS MEDIA_GERAL,
            ROUND(AVG(NU_NOTA_CN), 1) AS MEDIA_CN,
            ROUND(AVG(NU_NOTA_CH), 1) AS MEDIA_CH,
            ROUND(AVG(NU_NOTA_LC), 1) AS MEDIA_LC,
            ROUND(AVG(NU_NOTA_MT), 1) AS MEDIA_MT,
            ROUND(AVG(NU_NOTA_REDACAO), 1) AS MEDIA_REDACAO,
            ROUND(AVG(CASE WHEN DS_ESCOLA = 'Privada' THEN MEDIA_GERAL END), 1) AS MEDIA_PRIVADA,
            ROUND(AVG(CASE WHEN DS_ESCOLA = 'Publica' THEN MEDIA_GERAL END), 1) AS MEDIA_PUBLICA,
            COUNT(*) AS TOTAL,
            COUNT(DISTINCT SG_UF_PROVA) AS ESTADOS,
            COUNT(DISTINCT NU_ANO) AS ANOS
        FROM enem
    """)

    create_agg_table(conn, "agg_escola_simple", """
        SELECT DS_ESCOLA,
               ROUND(AVG(MEDIA_GERAL), 1) AS MEDIA_GERAL,
               COUNT(*) AS QTD
        FROM enem
        WHERE DS_ESCOLA IN ('Publica', 'Privada')
        GROUP BY DS_ESCOLA
    """)

    create_agg_table(conn, "agg_distribuicao", """
        SELECT NU_ANO, FAIXA_NOTA, COUNT(*) AS QTD
        FROM enem
        WHERE FAIXA_NOTA IS NOT NULL
        GROUP BY NU_ANO, FAIXA_NOTA
        ORDER BY NU_ANO, FAIXA_NOTA
    """)

    conn.commit()
    conn.close()
    elapsed = time.time() - start
    print(f"\nPre-computacao concluida em {elapsed:.1f}s!")


if __name__ == "__main__":
    precompute()
