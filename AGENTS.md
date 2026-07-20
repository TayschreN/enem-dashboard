# AGENTS.md - Guia para IA neste projeto

## Visao Geral

Dashboard interativo com analise dos microdados do ENEM (2019-2024). Processa ~14.4M registros com 11 tabelas agregadas pre-computadas para consultas instantaneas. Stack: Python + Pandas + SQLite + Dash/Plotly.

## Arquivos Principais

### Core
- **app.py** — Dashboard Dash com 5 abas (geral, escola, geo, demo, insights) + 6 builders + KPIs
- **queries.py** — 15 funcoes de consulta ao SQLite (leem das tabelas `agg_*`)
- **config.py** — Caminhos, `SEXO_MAP`, `YEARS`, `DISCIPLINAS_MAP`
- **transform.py** — Limpeza e transformacao dos dados brutos
- **load.py** — Carga no SQLite com chunking
- **precompute.py** — Gera as 11 tabelas agregadas (`agg_*`)

### Pipeline
- **pipeline.py** — Script que executa tudo em sequencia
- **download.py** — Download dos microdados do site do INEP
- **extract.py** — Extracao dos arquivos ZIP
- **process_2024.py** — Tratamento especial para o formato RESULTADOS de 2024

### Extras
- **test_pipeline.py** — Testes unitarios
- **requirements.txt** — Dependencias
- **check_url.py** — Utilitario para verificar URLs do INEP

## Banco de Dados (`data/enem.db`)

### Tabela principal
- **enem** — ~14.4M linhas, colunas: `NU_ANO`, `MEDIA_GERAL`, `MEDIA_CN`, `MEDIA_CH`, `MEDIA_LC`, `MEDIA_MT`, `MEDIA_REDACAO`, `NU_NOTA_CN`, `NU_NOTA_CH`, `NU_NOTA_LC`, `NU_NOTA_MT`, `NU_NOTA_REDACAO`, `TP_SEXO`, `TP_COR_RACA`, `Q006`, `SG_UF_PROVA`, `DS_ESCOLA` (Publica/Privada), `DS_RENDA`, `DS_COR_RACA`, `DS_REGIAO`, `IN_TREINEIRO`, `TP_PRESENCA`

### Tabelas agregadas (11)
- `agg_ano` — Medias por ano (MEDIA_CN, MEDIA_CH, MEDIA_LC, MEDIA_MT, MEDIA_REDACAO, MEDIA_GERAL, QTD)
- `agg_distribuicao` — Distribuicao por faixa de nota (NU_ANO, FAIXA_NOTA, QTD)
- `agg_uf` — Media por UF (ordenado por MEDIA_GERAL desc)
- `agg_ano_uf` — Cross ano x UF
- `agg_regiao` — Media por regiao x ano
- `agg_ano_escola` — Media por tipo de escola x ano
- `agg_renda` — Media por faixa de renda (com DS_RENDA_ORDEM)
- `agg_cor_raca` — Media por cor/raca x ano
- `agg_sexo` — Media por sexo x ano (2019-2023 apenas)
- `agg_raca_escola` — Intersecao raca x tipo de escola
- `agg_escola_simple` — Agregado simples de escola
- `agg_insights` — Linha unica com totais e medias globais

## Convencoes de Codigo

- Nao adicionar comentarios a menos que seja estritamente necessario
- Strings em portugues (interface do dashboard, nomes de colunas)
- Nomes de variaveis/funcoes em ingles
- Usar `try/except` em todos os builders e callbacks do Dash
- Graficos usam Plotly `go.Figure` ou `px.*`
- Layout com `dash_bootstrap_components` (dbc)

## Regras Importantes

1. **TP_SEXO** usa strings `'F'`/`'M'` nos anos 2019-2023 (NAO sao 0/1). O `SEXO_MAP` em `config.py` mapeia ambos os formatos para `'Feminino'`/`'Masculino'`.
2. **2024** usa um formato diferente (arquivo RESULTADOS) e NAO tem colunas `TP_SEXO`, `TP_COR_RACA`, `Q006`, `IN_TREINEIRO`. Todas as analises de sexo/cor/renda excluem 2024.
3. **Nao usar `locationmode="Brazil"`** no Plotly — use GeoJSON do `brazil-states.geojson`.
4. **Nao consultar a tabela `enem` diretamente** em queries de dashboard — sempre usar as tabelas `agg_*` para performance.
5. **`get_violin_sample()`** esta deprecated (substituido por `agg_distribuicao` + heatmap).
6. Toda callback do Dash deve ter `try/except` retornando `dbc.Alert`.
7. Slider de anos filtra via `_filter_by_years()` que usa `NU_ANO`.

## Comandos

```bash
# Iniciar o dashboard
python app.py                # http://127.0.0.1:8051

# Pipeline completo
python pipeline.py

# Pre-computar agregacoes (apos carga)
python precompute.py

# Testes
python test_pipeline.py
```

## Dados

- Filtros aplicados: `IN_TREINEIRO != 1`, `TP_PRESENCA = 1` (todas 4 provas), notas nao nulas
- Anos 2014-2018 removidos (performance)
- ~14.4M registros de 2019-2024
- Precisao: medias batem com INEP oficial com diferencas < 5 pts (exceto Redacao ~16 pts devido aos filtros)
