import numpy as np
import pandas as pd
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import YEARS
from transform import transform
from load import load
from queries import check_data_exists, get_media_por_ano, get_insights_data

np.random.seed(42)
print(f"Gerando dados de teste para {len(YEARS)} anos ({YEARS[0]}-{YEARS[-1]})...")

rows_per_year = 2000
frames = []
ufs = ["SP", "RJ", "MG", "RS", "PR", "BA", "PE", "CE", "DF", "GO", "AM", "PA", "SC", "ES", "MT"]

for year in YEARS:
    df = pd.DataFrame({
        "NU_INSCRICAO": range(year * 1000000, year * 1000000 + rows_per_year),
        "NU_ANO": year,
        "TP_SEXO": np.random.choice([0, 1], rows_per_year),
        "TP_COR_RACA": np.random.choice([0, 1, 2, 3, 4, 5, 6], rows_per_year,
                                        p=[0.02, 0.45, 0.10, 0.35, 0.03, 0.03, 0.02]),
        "TP_ESCOLA": np.random.choice([1, 2, 3, 4], rows_per_year, p=[0.02, 0.55, 0.38, 0.05]),
        "TP_ST_CONCLUSAO": np.random.choice([1, 2, 3], rows_per_year, p=[0.6, 0.3, 0.1]),
        "SG_UF_PROVA": np.random.choice(ufs, rows_per_year),
        "NO_MUNICIPIO_PROVA": "CIDADE",
        "NU_NOTA_CN": np.random.normal(500, 100, rows_per_year).clip(0, 1000).round(1),
        "NU_NOTA_CH": np.random.normal(520, 95, rows_per_year).clip(0, 1000).round(1),
        "NU_NOTA_LC": np.random.normal(530, 90, rows_per_year).clip(0, 1000).round(1),
        "NU_NOTA_MT": np.random.normal(510, 110, rows_per_year).clip(0, 1000).round(1),
        "NU_NOTA_REDACAO": np.random.normal(600, 150, rows_per_year).clip(0, 1000).round(1),
        "Q006": np.random.choice(["A", "B", "C", "D", "E", "F", "G", "H"], rows_per_year,
                                 p=[0.02, 0.08, 0.15, 0.15, 0.30, 0.15, 0.10, 0.05]),
        "TP_PRESENCA_CN": 1,
        "TP_PRESENCA_CH": 1,
        "TP_PRESENCA_LC": 1,
        "TP_PRESENCA_MT": 1,
        "TP_LINGUA": np.random.choice([0, 1], rows_per_year),
        "IN_TREINEIRO": np.random.choice([0, 1], rows_per_year, p=[0.97, 0.03]),
    })
    frames.append(df)

df_full = pd.concat(frames, ignore_index=True)
print(f"Dados gerados: {len(df_full):,} registros ({len(YEARS)} anos)")

# clean up old test data
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "enem.db")
if os.path.exists(db_path):
    os.remove(db_path)
    print("Banco anterior removido.")

print("\nExecutando transformacao...")
df_t = transform(df_full)
print(f"Apos transformacao: {len(df_t):,} registros")

print("\nCarregando no SQLite...")
load(df_t)

exists, count = check_data_exists()
print(f"\nVerificacao: dados={exists}, registros={count:,}")

print("\nMedias por ano:")
print(get_media_por_ano().to_string(index=False))

insights = get_insights_data()
if insights is not None:
    print(f"\nInsights: Media geral={insights['MEDIA_GERAL']}, "
          f"Estados={insights['ESTADOS']}, Anos={insights['ANOS']}")

print("\n" + "=" * 50)
print("  TESTE CONCLUIDO COM SUCESSO!")
print("  Execute 'python app.py' para abrir o dashboard")
print("=" * 50)
