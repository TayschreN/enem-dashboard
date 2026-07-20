import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
DB_PATH = os.path.join(DATA_DIR, "enem.db")

YEARS = list(range(2014, 2025))

URLS = {
    year: f"https://download.inep.gov.br/microdados/microdados_enem_{year}.zip"
    for year in YEARS
}

CHUNK_SIZE = 50000

COLUNAS_KEEP = [
    "NU_INSCRICAO", "NU_ANO",
    "TP_SEXO", "TP_COR_RACA", "TP_ESCOLA", "TP_ST_CONCLUSAO",
    "SG_UF_PROVA", "NO_MUNICIPIO_PROVA",
    "NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO",
    "Q006", "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT",
    "TP_LINGUA", "IN_TREINEIRO",
]

SEXO_MAP = {0: "Feminino", 1: "Masculino", "F": "Feminino", "M": "Masculino"}

COR_RACA_MAP = {
    0: "Nao declarado", 1: "Branca", 2: "Preta",
    3: "Parda", 4: "Amarela", 5: "Indigena", 6: "Nao dispoe da informacao"
}

ESCOLA_MAP = {
    1: "Nao respondeu", 2: "Publica", 3: "Privada", 4: "Exterior"
}

RENDA_MAP = {
    "A": "Nenhuma renda",
    "B": "Ate 1 salario minimo",
    "C": "1 a 1,5 salarios minimos",
    "D": "1,5 a 2 salarios minimos",
    "E": "2 a 5 salarios minimos",
    "F": "5 a 10 salarios minimos",
    "G": "10 a 20 salarios minimos",
    "H": "Mais de 20 salarios minimos"
}

REGIOES = {
    "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Centro-Oeste": ["DF", "GO", "MT", "MS"],
    "Sudeste": ["ES", "MG", "RJ", "SP"],
    "Sul": ["PR", "RS", "SC"],
}
