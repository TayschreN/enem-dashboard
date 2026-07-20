import urllib3
urllib3.disable_warnings()
import requests

url = 'https://download.inep.gov.br/microdados/microdados_enem_2024.zip'
try:
    r = requests.get(url, stream=True, timeout=30, verify=False)
    print(f'Status: {r.status_code}')
    length = int(r.headers.get("content-length", 0))
    print(f'Content-Length: {length / (1024*1024):.1f} MB')
    print(f'Content-Type: {r.headers.get("content-type")}')
    if length > 0:
        print('URL valida! Download possivel.')
    r.close()
except Exception as e:
    print(f'ERRO: {e}')
