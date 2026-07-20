import os, sys, time, zipfile
import pandas as pd
import numpy as np

from extract import extract_year, get_csv_files
from transform import transform
from load import load
from config import RAW_DIR, YEARS

FULL_COLUMNS = [
    "NU_INSCRICAO", "NU_ANO",
    "TP_SEXO", "TP_COR_RACA", "TP_ESCOLA", "TP_ST_CONCLUSAO",
    "SG_UF_PROVA", "NO_MUNICIPIO_PROVA",
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO",
    "Q006", "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
    "TP_LINGUA", "IN_TREINEIRO",
    "TP_DEPENDENCIA_ADM_ESC", "SG_UF_ESC", "CO_MUNICIPIO_PROVA", "CO_UF_PROVA",
    "MEDIA_GERAL", "DS_SEXO", "DS_COR_RACA", "DS_ESCOLA",
    "DS_RENDA", "DS_RENDA_ORDEM", "DS_REGIAO",
    "MEDIA_LINGUAGENS", "MEDIA_EXATAS", "MEDIA_HUMANAS", "FAIXA_NOTA",
]

db = os.path.join("data", "enem.db")
if os.path.exists(db):
    os.remove(db)

ANOS_DISPONIVEIS = []
for year in YEARS:
    path = os.path.join(RAW_DIR, f"microdados_enem_{year}.zip")
    if os.path.exists(path) and os.path.getsize(path) > 1000000:
        ANOS_DISPONIVEIS.append(year)

print(f"Anos disponiveis: {ANOS_DISPONIVEIS}")
totais = {}
start = time.time()

for year in ANOS_DISPONIVEIS:
    print(f"\n{'='*50}")
    print(f"  Processando {year}")
    print(f"{'='*50}")

    try:
        df = extract_year(year)
        if df.empty:
            print(f"  [!] Nenhum dado extraido para {year}")
            continue

        print(f"  Extraido: {len(df):,} registros, {len(df.columns)} colunas")
        totais[year] = len(df)

        df_t = transform(df)
        print(f"  Transformado: {len(df_t):,} registros, {len(df_t.columns)} colunas")

        for col in FULL_COLUMNS:
            if col not in df_t.columns:
                df_t[col] = np.nan

        df_t = df_t[[c for c in FULL_COLUMNS if c in df_t.columns]]

        load(df_t, if_exists="append")

    except Exception as e:
        print(f"  [!] ERRO no ano {year}: {e}")
        import traceback
        traceback.print_exc()
        continue

elapsed = time.time() - start
total_geral = sum(totais.values())
print(f"\n{'='*50}")
print(f"  PIPELINE CONCLUIDA!")
print(f"  Anos processados: {len(totais)}/{len(ANOS_DISPONIVEIS)}")
print(f"  Total de registros: {total_geral:,}")
print(f"  Tempo: {elapsed/60:.1f} min")
print(f"{'='*50}")
print(f"\nExecute 'python app.py' para abrir o dashboard com dados reais!")
