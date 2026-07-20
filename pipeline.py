import sys
import time
from config import YEARS
from download import download_enem
from extract import extract_year
from transform import transform
from load import load


def run_pipeline(years=None):
    if years is None:
        years = YEARS

    start = time.time()

    print("=" * 60)
    print("  PIPELINE ENEM - Iniciando")
    print("=" * 60)

    for year in years:
        print(f"\n--- Ano {year} ---")

        print("[1/3] Download...")
        download_enem(year)

        print("[2/3] Extração...")
        df = extract_year(year)

        if df.empty:
            print(f"[{year}] Nenhum dado extraído, pulando.")
            continue

        print(f"[3/3] Transformação e carga...")
        df_transformed = transform(df)
        load(df_transformed)

    elapsed = time.time() - start
    print(f"\nPipeline concluída em {elapsed // 60:.0f}m {elapsed % 60:.0f}s!")
    print(f"Dados salvos no SQLite. Execute 'python app.py' para abrir o dashboard.")


if __name__ == "__main__":
    run_pipeline()
