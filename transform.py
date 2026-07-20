import numpy as np
import pandas as pd
from config import SEXO_MAP, COR_RACA_MAP, ESCOLA_MAP, RENDA_MAP, REGIOES


def _map_regiao(uf):
    for regiao, ufs in REGIOES.items():
        if uf in ufs:
            return regiao
    return "Desconhecido"


def transform(df):
    print(f"Transformando {len(df):,} registros...")

    df = df.copy()

    if "IN_TREINEIRO" in df.columns:
        df = df[df["IN_TREINEIRO"] != 1]
        print(f"  Apos remover treineiros: {len(df):,}")

    presenca_cols = [c for c in ["TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT"] if c in df.columns]
    for col in presenca_cols:
        df = df[df[col] == 1]
    print(f"  Apos filtrar presenca: {len(df):,}")

    nota_cols = [c for c in ["NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO"] if c in df.columns]
    if len(nota_cols) < 5:
        print(f"  Aviso: apenas {len(nota_cols)} colunas de nota disponiveis")

    df = df.dropna(subset=nota_cols, how="any")
    print(f"  Apos remover notas nulas: {len(df):,}")

    df["MEDIA_GERAL"] = df[nota_cols].mean(axis=1).round(1)

    df["DS_SEXO"] = df["TP_SEXO"].map(SEXO_MAP).fillna("Desconhecido") if "TP_SEXO" in df.columns else "Desconhecido"
    df["DS_COR_RACA"] = df["TP_COR_RACA"].map(COR_RACA_MAP).fillna("Desconhecido") if "TP_COR_RACA" in df.columns else "Desconhecido"

    if "TP_ESCOLA" in df.columns:
        df["DS_ESCOLA"] = df["TP_ESCOLA"].map(ESCOLA_MAP).fillna("Desconhecido")
    else:
        df["DS_ESCOLA"] = "Desconhecido"

    if "Q006" in df.columns:
        df["DS_RENDA"] = df["Q006"].map(RENDA_MAP).fillna("Desconhecido")
        df["DS_RENDA_ORDEM"] = df["Q006"].map({k: i for i, k in enumerate(RENDA_MAP.keys())})
    else:
        df["DS_RENDA"] = "Desconhecido"
        df["DS_RENDA_ORDEM"] = -1

    if "SG_UF_PROVA" in df.columns:
        df["DS_REGIAO"] = df["SG_UF_PROVA"].apply(_map_regiao)
    else:
        df["DS_REGIAO"] = "Desconhecido"

    df["MEDIA_LINGUAGENS"] = df[["NU_NOTA_LC", "NU_NOTA_REDACAO"]].mean(axis=1).round(1) if all(c in df.columns for c in ["NU_NOTA_LC", "NU_NOTA_REDACAO"]) else 0
    df["MEDIA_EXATAS"] = df[["NU_NOTA_MT", "NU_NOTA_CN"]].mean(axis=1).round(1) if all(c in df.columns for c in ["NU_NOTA_MT", "NU_NOTA_CN"]) else 0
    df["MEDIA_HUMANAS"] = df["NU_NOTA_CH"] if "NU_NOTA_CH" in df.columns else 0

    df["FAIXA_NOTA"] = pd.cut(
        df["MEDIA_GERAL"],
        bins=[0, 300, 400, 500, 600, 700, 800, 1000],
        labels=["0-300", "300-400", "400-500", "500-600", "600-700", "700-800", "800-1000"]
    )

    for col in nota_cols:
        df[col] = df[col].astype(float)

    df = df.reset_index(drop=True)

    print(f"  Transformacao concluida: {len(df):,} registros finais")
    return df
