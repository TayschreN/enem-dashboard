import os
import sys

db = os.path.join("data", "enem.db")
if os.path.exists(db):
    os.remove(db)

from extract import extract_year
from transform import transform
from load import load

df = extract_year(2024)
if df.empty:
    print("ERRO: nenhum dado extraido")
    sys.exit(1)

print(f"Extraido: {len(df):,} registros")
print(f"Colunas: {list(df.columns)}")

df_t = transform(df)
print(f"Transformado: {len(df_t):,} registros")
print(f"Colunas finais: {list(df_t.columns)}")
print(f"\nAmostra:")
print(df_t[["MEDIA_GERAL", "DS_ESCOLA", "DS_REGIAO", "FAIXA_NOTA"]].head(5))

load(df_t)

print("\nOK! Dados reais do ENEM 2024 carregados com sucesso.")
