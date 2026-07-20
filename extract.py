import os
import zipfile
import pandas as pd
from config import RAW_DIR

COLUNAS_RESULTADOS = [
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO",
    "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
    "SG_UF_PROVA", "NO_MUNICIPIO_PROVA",
    "TP_LINGUA", "NU_ANO",
    "TP_DEPENDENCIA_ADM_ESC", "SG_UF_ESC", "CO_MUNICIPIO_PROVA", "CO_UF_PROVA",
]

COLUNAS_MICRODADOS = [
    "NU_INSCRICAO", "NU_ANO",
    "TP_SEXO", "TP_COR_RACA", "TP_ESCOLA", "TP_ST_CONCLUSAO",
    "SG_UF_PROVA", "NO_MUNICIPIO_PROVA",
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO",
    "Q006", "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
    "TP_LINGUA", "IN_TREINEIRO",
]


def get_csv_files(zip_path):
    with zipfile.ZipFile(zip_path, "r") as zf:
        return [f for f in zf.namelist() if f.lower().endswith(".csv")]


def extract_old_format(zip_path, csv_name, year):
    with zipfile.ZipFile(zip_path, "r") as zf:
        with zf.open(csv_name) as f:
            header = pd.read_csv(f, sep=";", encoding="latin1", nrows=0, low_memory=True)
            available = [c for c in header.columns if c in COLUNAS_MICRODADOS]

        chunks = []
        total = 0
        with zf.open(csv_name) as f:
            for chunk in pd.read_csv(f, sep=";", encoding="latin1", usecols=available,
                                      chunksize=100000, low_memory=True):
                chunk["NU_ANO"] = year
                chunks.append(chunk)
                total += len(chunk)
                print(f"\r  Lidas {total:,} linhas...", end="")

    print(f"\n  Formato antigo: {total:,} linhas, {len(available)} colunas")
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()


def extract_new_format(zip_path, year):
    csv_files = get_csv_files(zip_path)
    csv_basenames = {f.split("/")[-1].upper(): f for f in csv_files}

    res_key = next((k for k in csv_basenames if "RESULTADOS" in k), None)
    if res_key is None:
        print("  RESULTADOS nao encontrado!")
        return pd.DataFrame()

    res_path = csv_basenames[res_key]
    print(f"  Lendo {res_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        with zf.open(res_path) as f:
            header = pd.read_csv(f, sep=";", encoding="latin1", nrows=0, low_memory=True)
            available = [c for c in header.columns if c in COLUNAS_RESULTADOS]

        chunks = []
        total = 0
        with zf.open(res_path) as f:
            for chunk in pd.read_csv(f, sep=";", encoding="latin1", usecols=available,
                                      chunksize=100000, low_memory=True):
                chunk["NU_ANO"] = year
                chunks.append(chunk)
                total += len(chunk)
                print(f"\r  Lidas {total:,} linhas...", end="")

    result = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

    if not result.empty and "TP_DEPENDENCIA_ADM_ESC" in result.columns:
        result["TP_ESCOLA"] = result["TP_DEPENDENCIA_ADM_ESC"].map(
            {1: 2, 2: 2, 3: 2, 4: 3}
        ).fillna(1)

    cov = len(result.columns)
    print(f"\n  Formato novo: {len(result):,} linhas, {cov} colunas")
    return result


def extract_year(year):
    zip_path = os.path.join(RAW_DIR, f"microdados_enem_{year}.zip")

    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Arquivo nao encontrado: {zip_path}")

    csv_files = get_csv_files(zip_path)
    csv_basenames = [f.split("/")[-1].upper() for f in csv_files]

    print(f"\n[{year}] CSVs: {csv_basenames}")

    has_old = any("MICRODADOS" in b for b in csv_basenames)
    has_new = any("RESULTADOS" in b for b in csv_basenames)

    if has_old:
        csv_name = [f for f in csv_files if "MICRODADOS" in f.split("/")[-1].upper()][0]
        print(f"[{year}] Formato antigo: {csv_name.split('/')[-1]}")
        return extract_old_format(zip_path, csv_name, year)
    elif has_new:
        print(f"[{year}] Formato novo (RESULTADOS)")
        return extract_new_format(zip_path, year)
    else:
        print(f"[{year}] Formato desconhecido, lendo primeiro CSV")
        return extract_old_format(zip_path, csv_files[0], year)


if __name__ == "__main__":
    from config import YEARS
    for year in YEARS:
        df = extract_year(year)
        if not df.empty:
            print(f"[{year}] Shape: {df.shape}")
