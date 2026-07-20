import os
import requests
import urllib3
from config import URLS, RAW_DIR, YEARS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def download_enem(year):
    url = URLS[year]
    filename = f"microdados_enem_{year}.zip"
    filepath = os.path.join(RAW_DIR, filename)

    if os.path.exists(filepath):
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"[{year}] Arquivo já existe ({size_mb:.1f} MB). Pulando.")
        return filepath

    os.makedirs(RAW_DIR, exist_ok=True)

    print(f"[{year}] Baixando {url}")
    response = requests.get(url, stream=True, timeout=120, verify=False)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(filepath, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = downloaded / total * 100
                print(f"\r[{year}] Progresso: {pct:.1f}% ({downloaded // (1024*1024)} MB / {total // (1024*1024)} MB)", end="")
            elif downloaded % (1024 * 1024) < 8192:
                print(f"\r[{year}] Baixados {downloaded // (1024*1024)} MB...", end="")

    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"\n[{year}] Download concluído! ({size_mb:.1f} MB)")
    return filepath


if __name__ == "__main__":
    for year in YEARS:
        download_enem(year)
    print("\nTodos os downloads finalizados!")
