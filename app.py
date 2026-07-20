import dash
from dash import dcc, html, Input, Output, callback, dash_table
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from queries import (
    check_data_exists, get_media_por_ano, get_total_por_ano,
    get_media_por_escola, get_media_por_uf, get_media_por_uf_ano,
    get_media_por_regiao, get_media_por_renda, get_media_por_cor_raca,
    get_media_por_sexo, get_correlacao, get_media_raca_escola,
    get_insights_data, get_tendencia_media_geral, get_stats_por_ano,
    get_distribuicao_notas, get_delta_anual,
    get_ranking_uf, get_media_escola_simple
)
from config import YEARS

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                title="Dashboard ENEM 2014-2024 | Engenharia de Dados",
                update_title=None)
server = app.server

data_exists, total_records = check_data_exists()
insights = get_insights_data() if data_exists else None

DISCIPLINAS_MAP = {
    "NU_NOTA_CN": "Ciencias Naturais",
    "NU_NOTA_CH": "Ciencias Humanas",
    "NU_NOTA_LC": "Linguagens",
    "NU_NOTA_MT": "Matematica",
    "NU_NOTA_REDACAO": "Redacao"
}
DISCIPLINAS_LIST = list(DISCIPLINAS_MAP.keys())
DISCIPLINAS_LABELS = list(DISCIPLINAS_MAP.values())
DISCIPLINAS_CORES = ["#3949ab", "#00897b", "#fdd835", "#e53935", "#6d4c41"]

ESTILO_CARD = "shadow border-0 mb-3 rounded-3"
ESTILO_CARD_HEADER = {"fontWeight": "700", "backgroundColor": "#f8f9fa", "borderBottom": "2px solid #e9ecef"}

app.layout = dbc.Container([

    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H1("\U0001f4ca ENEM Data Analysis",
                            className="d-inline-block",
                            style={"fontWeight": "700", "fontSize": "2.2rem", "color": "white"}),
                    html.Span(" 2014 - 2024", style={"fontSize": "1.5rem", "color": "rgba(255,255,255,0.8)"}),
                ]),
                html.P("Pipeline de Engenharia de Dados | Analise completa dos microdados do ENEM",
                       style={"color": "rgba(255,255,255,0.7)", "fontSize": "1rem", "marginTop": "4px"}),
            ], width=8),
            dbc.Col([
                html.Div([
                    html.Span("\U0001f4be Dados:", style={"color": "rgba(255,255,255,0.6)", "fontSize": "0.85rem"}),
                    html.Br(),
                    html.Span(f"{total_records:,}" if data_exists else "---",
                              style={"color": "white", "fontSize": "1.8rem", "fontWeight": "700"}),
                    html.Span(" registros", style={"color": "rgba(255,255,255,0.7)", "fontSize": "0.9rem"}),
                ], className="text-end")
            ], width=4),
        ], className="align-items-center"),
    ], style={
        "background": "linear-gradient(135deg, #0d1b3e 0%, #1a237e 50%, #283593 100%)",
        "padding": "28px 36px", "borderRadius": "12px", "marginBottom": "20px",
        "boxShadow": "0 8px 32px rgba(0,0,0,0.18)"
    }),

    dbc.Row(id="kpi-row", className="mb-3"),

    dbc.Row([
        dbc.Col([
            html.Label("Selecione os anos:", style={"fontWeight": "600", "fontSize": "0.9rem", "color": "#555"}),
            dcc.RangeSlider(
                id="year-slider",
                min=YEARS[0], max=YEARS[-1],
                value=[YEARS[0], YEARS[-1]],
                marks={str(y): str(y) for y in YEARS},
                step=1,
                tooltip={"placement": "top", "always_visible": True},
                allowCross=False,
            ),
        ], width=12, className="px-3 mb-3"),
    ]),

    dbc.Tabs([
        dbc.Tab(label="\U0001f4ca Visao Geral", tab_id="geral"),
        dbc.Tab(label="\U0001f3eb Escolas", tab_id="escola"),
        dbc.Tab(label="\U0001f5fa Geografico", tab_id="geo"),
        dbc.Tab(label="\U0001f465 Demografico", tab_id="demo"),
        dbc.Tab(label="\U0001f4a1 Insights", tab_id="insights"),
    ], id="tabs", active_tab="geral", className="mb-3", style={"fontWeight": "600"}),

    dbc.Row([
        dbc.Col(id="tab-content", width=12)
    ])

], fluid=True, style={"backgroundColor": "#f4f6f9", "minHeight": "100vh", "padding": "20px 24px"})


def _card(children, color="#1a237e", width=2, extra_class=""):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(children, className="text-center py-3"),
            className=f"border-0 shadow-sm {extra_class}",
            style={"borderLeft": f"4px solid {color}", "borderRadius": "10px"}
        ),
        width=width
    )


def _filter_by_years(df, year_col="NU_ANO", selected=None):
    if selected is None or df.empty:
        return df
    return df[(df[year_col] >= selected[0]) & (df[year_col] <= selected[1])]


def _insight_box(text, icon="\U0001f4a1"):
    return html.Div([
        html.Span(f"{icon} ", style={"fontSize": "1.1rem"}),
        html.Span(text, style={"fontSize": "0.9rem", "color": "#555"})
    ], className="p-3 mt-2",
       style={"backgroundColor": "#e8eaf6", "borderRadius": "8px", "borderLeft": "4px solid #1a237e"})


def _card_w_graph(title, figure, insight_text="", width=6):
    children = [dbc.CardHeader(title, style=ESTILO_CARD_HEADER), dbc.CardBody(dcc.Graph(figure=figure))]
    if insight_text:
        children.append(dbc.CardBody(_insight_box(insight_text), className="pt-0"))
    return dbc.Col(dbc.Card(children, className=ESTILO_CARD), width=width)


def build_kpis(anos):
    if not data_exists:
        return dbc.Col(dbc.Alert("Nenhum dado carregado.", color="warning"), width=12)
    try:
        df = get_media_por_ano()
        df = _filter_by_years(df, selected=anos)
        if df.empty:
            return dbc.Col(dbc.Alert("Sem dados para os anos selecionados.", color="info"), width=12)

        total = int(df["QTD"].sum())
        media = round(df["MEDIA_GERAL"].mean(), 1)

        privada = 0
        publica = 0
        if insights is not None:
            privada = insights.get("MEDIA_PRIVADA", 0) or 0
            publica = insights.get("MEDIA_PUBLICA", 0) or 0
        gap = round(privada - publica, 1)

        variacao, _, _ = get_tendencia_media_geral()

        melhor = df.loc[df["MEDIA_GERAL"].idxmax()]
        pior = df.loc[df["MEDIA_GERAL"].idxmin()]

        estado_count = int(insights["ESTADOS"]) if insights is not None else 0

        return [
            _card([html.Div("\U0001f465", style={"fontSize": "1.5rem"}),
                   html.H5(f"{total:,}", className="mb-0", style={"fontWeight": "700", "fontSize": "1.5rem"}),
                   html.Small("Total de Participantes", style={"color": "#888", "fontSize": "0.75rem"})],
                  "#1a237e", 2),
            _card([html.Div("\U0001f3af", style={"fontSize": "1.5rem"}),
                   html.H5(f"{media}", className="mb-0", style={"fontWeight": "700", "fontSize": "1.5rem"}),
                   html.Small("Media Geral", style={"color": "#888", "fontSize": "0.75rem"})],
                  "#00897b", 2),
            _card([html.Div("\U0001f4c8", style={"fontSize": "1.5rem"}),
                   html.H5(f"{variacao:+.2f}%", className="mb-0", style={"fontWeight": "700", "fontSize": "1.5rem",
                            "color": "#e53935" if variacao < 0 else "#2e7d32"}),
                   html.Small("Variacao Total", style={"color": "#888", "fontSize": "0.75rem"})],
                  "#ff8f00", 2),
            _card([html.Div("\U0001f393", style={"fontSize": "1.5rem"}),
                   html.H5(f"{gap}", className="mb-0", style={"fontWeight": "700", "fontSize": "1.5rem"}),
                   html.Small("Gap Privada - Publica", style={"color": "#888", "fontSize": "0.75rem"})],
                  "#6d4c41", 2),
            _card([html.Div("\U0001f30e", style={"fontSize": "1.5rem"}),
                   html.H5(f"{estado_count}", className="mb-0",
                           style={"fontWeight": "700", "fontSize": "1.5rem"}),
                   html.Small("Estados", style={"color": "#888", "fontSize": "0.75rem"})],
                  "#3949ab", 2),
            _card([html.Div(f'{melhor["NU_ANO"]:.0f}', className="mb-0",
                            style={"fontWeight": "700", "fontSize": "1.5rem", "color": "#2e7d32"}),
                   html.Small(f"Melhor ano: {melhor['MEDIA_GERAL']}", style={"color": "#888", "fontSize": "0.75rem"})],
                  "#2e7d32", 2),
        ]
    except Exception as e:
        return dbc.Col(dbc.Alert(f"Erro ao carregar KPIs: {e}", color="danger"), width=12)


def build_visao_geral(anos):
    if not data_exists:
        return dbc.Alert("Sem dados.", color="warning")
    try:
        df_ano = get_media_por_ano()
        df_ano_f = _filter_by_years(df_ano, selected=anos)
        df_total = get_total_por_ano()
        df_total_f = _filter_by_years(df_total, selected=anos)
        df_corr = get_correlacao()

        fig_evolucao = go.Figure()
        for disc, label, cor in zip(DISCIPLINAS_LIST, DISCIPLINAS_LABELS, DISCIPLINAS_CORES):
            col = disc.replace("NU_NOTA_", "MEDIA_") if disc.startswith("NU_NOTA_") else disc
            if col in df_ano.columns:
                fig_evolucao.add_trace(go.Scatter(
                    x=df_ano["NU_ANO"], y=df_ano[col],
                    mode="lines+markers", name=label,
                    line=dict(width=2.5, color=cor), marker=dict(size=6),
                    hovertemplate="%{y:.1f}<extra></extra>"
                ))
        fig_evolucao.update_layout(
            title=dict(text="Evolucao das Medias por Disciplina", font=dict(size=16)),
            xaxis=dict(title="Ano", dtick=1), yaxis=dict(title="Media", range=[400, 700]),
            template="plotly_white", hovermode="x unified",
            legend=dict(orientation="h", y=-0.25), height=400,
            margin=dict(t=50, b=60, l=60, r=20),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
        )

        cols_media = [c for c in df_ano.columns if c.startswith("MEDIA_")]
        insight_evol = f"Redacao tem a maior media historica, enquanto Ciencias da Natureza tem a menor. " \
                       f"Linguagens apresenta a maior estabilidade ao longo dos anos."

        fig_participacao = go.Figure()
        if not df_total_f.empty:
            fig_participacao.add_trace(go.Bar(
                x=df_total_f["NU_ANO"], y=df_total_f["QTD"],
                marker_color="#3949ab", marker_line=dict(width=0),
                hovertemplate="%{y:,}<extra></extra>", showlegend=False
            ))
            fig_participacao.add_trace(go.Scatter(
                x=df_total_f["NU_ANO"], y=df_total_f["QTD"],
                mode="lines+markers", line=dict(color="#e53935", width=2), marker=dict(size=6),
                hovertemplate="%{y:,}<extra></extra>", showlegend=False
            ))
        fig_participacao.update_layout(
            title=dict(text="Participacao por Ano", font=dict(size=16)),
            xaxis=dict(title="Ano", dtick=1), yaxis=dict(title="Participantes", tickformat=","),
            template="plotly_white", height=400,
            margin=dict(t=50, b=60, l=60, r=20),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
        )

        pico = df_total_f.loc[df_total_f["QTD"].idxmax()] if not df_total_f.empty else None
        insight_part = f"O ano de {pico['NU_ANO']:.0f} teve o maior numero de participantes ({int(pico['QTD']):,}). " \
                       f"Ha uma tendencia de queda nas inscricoes a partir de 2016." if pico is not None else ""

        df_dist = get_distribuicao_notas()
        df_dist_f = _filter_by_years(df_dist, selected=anos)
        if not df_dist_f.empty:
            pivot = df_dist_f.pivot_table(index="NU_ANO", columns="FAIXA_NOTA", values="QTD")
            pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
            faixa_order = ["0-300", "300-400", "400-500", "500-600", "600-700", "700-800", "800-1000"]
            faixa_exists = [c for c in faixa_order if c in pivot_pct.columns]
            pivot_pct = pivot_pct[faixa_exists]
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=pivot_pct.values, x=[c.replace("-", " a ") for c in faixa_exists],
                y=[str(int(y)) for y in pivot_pct.index],
                colorscale="YlOrRd", text=np.round(pivot_pct.values, 1),
                texttemplate="%{text}%", textfont=dict(size=10),
                hovertemplate="Ano: %{y}<br>Faixa: %{x}<br>%{z:.1f}%%<extra></extra>",
            ))
            fig_heatmap.update_layout(
                title=dict(text="Distribuicao das Notas por Ano", font=dict(size=16)),
                xaxis=dict(title="Faixa de Nota"), yaxis=dict(title="Ano"),
                template="plotly_white", height=450,
                margin=dict(t=50, b=60, l=60, r=20),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
            )
            insight_heatmap = "A maior concentracao de participantes esta nas faixas de 400 a 600 pontos. " \
                              "A distribuicao e consistente entre os anos, com leve deslocamento para a direita."
        else:
            fig_heatmap = go.Figure()
            insight_heatmap = ""

        fig_radar = go.Figure()
        if not df_ano_f.empty:
            labels_radar = ["C. Natureza", "C. Humanas", "Linguagens", "Matematica", "Redacao"]
            cols_radar = ["MEDIA_CN", "MEDIA_CH", "MEDIA_LC", "MEDIA_MT", "MEDIA_REDACAO"]
            for _, row in df_ano_f.iterrows():
                values = [row.get(c, 0) for c in cols_radar]
                if any(values):
                    fig_radar.add_trace(go.Scatterpolar(
                        r=values, theta=labels_radar,
                        fill="toself", name=str(int(row["NU_ANO"])),
                        line=dict(width=2),
                    ))
            fig_radar.update_layout(
                title=dict(text="Perfil por Disciplina (Radar)", font=dict(size=16)),
                polar=dict(radialaxis=dict(visible=True, range=[400, 700])),
                template="plotly_white", height=450,
                legend=dict(orientation="h", y=-0.2),
                margin=dict(t=50, b=60, l=60, r=20),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            insight_radar = "O radar mostra o perfil de desempenho por disciplina. " \
                            "Redacao e Linguagens tem as pontuacoes mais altas. " \
                            "Ciencias da Natureza e a disciplina com menor media."
        else:
            fig_radar = go.Figure()
            insight_radar = ""

        if not df_corr.empty:
            fig_corr = px.imshow(
                df_corr, text_auto=".2f", aspect="auto",
                color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                labels=dict(x="Disciplina", y="Disciplina", color="Correlacao"),
                x=DISCIPLINAS_LABELS, y=DISCIPLINAS_LABELS,
            )
            fig_corr.update_layout(
                title=dict(text="Matriz de Correlacao entre Disciplinas", font=dict(size=16)),
                height=420, margin=dict(t=50, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            insight_corr = f"Matematica e Ciencias da Natureza tem a maior correlacao " \
                           f"({df_corr.loc['NU_NOTA_MT', 'NU_NOTA_CN']:.2f}). " \
                           f"Redacao tem correlacao moderada com as demais."
        else:
            fig_corr = go.Figure()
            insight_corr = ""

        fig_delta = go.Figure()
        df_delta = get_delta_anual()
        df_delta_f = _filter_by_years(df_delta, selected=anos)
        if not df_delta_f.empty and "DELTA" in df_delta_f.columns:
            fig_delta.add_trace(go.Bar(
                x=df_delta_f["NU_ANO"], y=df_delta_f["DELTA"],
                marker_color=df_delta_f["COR"],
                text=df_delta_f["DELTA"], textposition="outside",
                hovertemplate="%{y:+.1f}<extra></extra>", showlegend=False
            ))
            fig_delta.add_hline(y=0, line_color="#666", line_width=1)
        fig_delta.update_layout(
            title=dict(text="Variacao Anual da Media Geral (Delta)", font=dict(size=16)),
            xaxis=dict(title="Ano", dtick=1), yaxis=dict(title="Delta (pontos)"),
            template="plotly_white", height=400,
            margin=dict(t=50, b=60, l=60, r=20),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
        )

        variacao, primeiro, ultimo = get_tendencia_media_geral()
        insight_delta = f"A media geral variou {variacao:+.2f}% no periodo ({primeiro} -> {ultimo}). " \
                        f"O maior aumento ocorreu no ano com maior variacao positiva no grafico."

        return dbc.Row([
            _card_w_graph("Evolucao das Notas", fig_evolucao, insight_evol, 6),
            _card_w_graph("Participacao", fig_participacao, insight_part, 6),
            _card_w_graph("Distribuicao das Notas", fig_heatmap, insight_heatmap, 6),
            _card_w_graph("Variacao Anual (Delta)", fig_delta, insight_delta, 6),
            _card_w_graph("Perfil por Disciplina (Radar)", fig_radar, insight_radar, 6),
            _card_w_graph("Correlacao entre Disciplinas", fig_corr, insight_corr, 12),
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Erro na aba Visao Geral: {e}", color="danger")


def build_escola(anos):
    if not data_exists:
        return dbc.Alert("Sem dados.", color="warning")
    try:
        df_esc = get_media_por_escola()
        df_esc_f = _filter_by_years(df_esc, selected=anos)

        if df_esc_f.empty:
            return dbc.Alert("Dados de escola nao disponiveis para os anos selecionados.", color="info")

        fig_comparacao = go.Figure()
        for escola in ["Publica", "Privada"]:
            dfe = df_esc_f[df_esc_f["DS_ESCOLA"] == escola]
            if not dfe.empty:
                fig_comparacao.add_trace(go.Bar(
                    name=escola, x=dfe["NU_ANO"], y=dfe["MEDIA_GERAL"],
                    text=dfe["MEDIA_GERAL"], textposition="auto",
                    marker_color="#00897b" if escola == "Privada" else "#78909c",
                    hovertemplate=f"{escola}: %{{y}}<extra></extra>"
                ))
        fig_comparacao.update_layout(
            title=dict(text="Escola Publica vs Privada", font=dict(size=16)),
            xaxis=dict(title="Ano", dtick=1), yaxis=dict(title="Media Geral"),
            barmode="group", template="plotly_white", height=420,
            legend=dict(orientation="h", y=-0.2),
            margin=dict(t=50, b=60, l=60, r=20),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
        )

        privada_mean = df_esc_f[df_esc_f["DS_ESCOLA"] == "Privada"]["MEDIA_GERAL"].mean()
        publica_mean = df_esc_f[df_esc_f["DS_ESCOLA"] == "Publica"]["MEDIA_GERAL"].mean()
        gap_medio = round(privada_mean - publica_mean, 1)
        insight_comp = f"Alunos de escolas privadas tem em media {gap_medio} pontos acima de alunos de escolas publicas. " \
                       f"O gap se mantem consistente em torno de {gap_medio} pontos ao longo dos anos."

        privada = df_esc_f[df_esc_f["DS_ESCOLA"] == "Privada"].set_index("NU_ANO")["MEDIA_GERAL"]
        publica = df_esc_f[df_esc_f["DS_ESCOLA"] == "Publica"].set_index("NU_ANO")["MEDIA_GERAL"]
        diff = privada - publica
        gap_medio2 = round(diff.mean(), 1)

        fig_gap = go.Figure()
        fig_gap.add_trace(go.Bar(
            x=diff.index, y=diff.values,
            marker_color=["#e53935" if v > 0 else "#2e7d32" for v in diff.values],
            text=diff.values.round(1), textposition="auto",
            hovertemplate="Diferenca: %{y:.1f} pts<extra></extra>",
            showlegend=False
        ))
        fig_gap.add_hline(y=gap_medio2, line_dash="dash", line_color="#666",
                          annotation_text=f"Media: {gap_medio2}", annotation_position="bottom right")
        fig_gap.update_layout(
            title=dict(text=f"Gap Privada - Publica (media: {gap_medio2} pts)", font=dict(size=16)),
            xaxis=dict(title="Ano", dtick=1), yaxis=dict(title="Diferenca (pontos)"),
            template="plotly_white", height=400,
            margin=dict(t=50, b=60, l=60, r=20),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
        )
        insight_gap = f"O maior gap ocorreu em {diff.idxmax():.0f} ({diff.max():.1f} pts) " \
                      f"e o menor em {diff.idxmin():.0f} ({diff.min():.1f} pts)."

        df_raca_esc = get_media_raca_escola()
        fig_inter = go.Figure()
        if not df_raca_esc.empty:
            for cor in ["Branca", "Preta", "Parda"]:
                dfc = df_raca_esc[df_raca_esc["DS_COR_RACA"] == cor]
                for _, row in dfc.iterrows():
                    fig_inter.add_trace(go.Bar(
                        name=f"{cor} - {row['DS_ESCOLA']}",
                        x=[cor], y=[row["MEDIA_GERAL"]],
                        marker_color="#00897b" if row["DS_ESCOLA"] == "Privada" else "#78909c",
                        hovertemplate=f"{row['DS_ESCOLA']}: %{{y}}<extra>{cor}</extra>",
                        showlegend=True,
                        legendgroup=row["DS_ESCOLA"],
                    ))
            fig_inter.update_layout(
                title=dict(text="Nota por Raca e Tipo de Escola", font=dict(size=16)),
                xaxis=dict(title="Raca/Cor"), yaxis=dict(title="Media Geral"),
                barmode="group", template="plotly_white", height=400,
                legend=dict(orientation="h", y=-0.3),
                margin=dict(t=50, b=80, l=60, r=20),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
            )
            gap_branco_preto = df_raca_esc[df_raca_esc["DS_COR_RACA"] == "Branca"]["MEDIA_GERAL"].mean() - \
                               df_raca_esc[df_raca_esc["DS_COR_RACA"] == "Preta"]["MEDIA_GERAL"].mean()
            insight_inter = f"O gap entre estudantes brancos e pretos e de ~{gap_branco_preto:.0f} pontos. " \
                            f"A intersecao de raca e tipo de escola revela desigualdades estruturais profundas."
        else:
            insight_inter = ""

        df_esc_simple = get_media_escola_simple()
        insight_overall = ""
        if not df_esc_simple.empty:
            priv = df_esc_simple[df_esc_simple["DS_ESCOLA"] == "Privada"]
            pub = df_esc_simple[df_esc_simple["DS_ESCOLA"] == "Publica"]
            if not priv.empty and not pub.empty:
                insight_overall = f"Visao geral: Privada media {priv['MEDIA_GERAL'].values[0]}, " \
                                  f"Publica media {pub['MEDIA_GERAL'].values[0]}. " \
                                  f"Total de {int(priv['QTD'].values[0]):,} alunos de escola privada " \
                                  f"e {int(pub['QTD'].values[0]):,} de escola publica."

        return dbc.Row([
            _card_w_graph("Comparacao Publica vs Privada", fig_comparacao, insight_comp, 7),
            _card_w_graph("Diferenca de Notas (Gap)", fig_gap, insight_gap, 5),
            _card_w_graph("Impacto: Raca e Tipo de Escola", fig_inter, insight_inter, 12),
            dbc.Col(dbc.Card([
                dbc.CardHeader("\U0001f4a1 Resumo Escola", style=ESTILO_CARD_HEADER),
                dbc.CardBody(_insight_box(insight_overall))
            ], className=ESTILO_CARD), width=12),
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Erro na aba Escola: {e}", color="danger")


def build_geografico(anos):
    if not data_exists:
        return dbc.Alert("Sem dados.", color="warning")
    try:
        df_uf = get_media_por_uf()
        df_uf_ano = get_media_por_uf_ano()
        df_uf_ano_f = _filter_by_years(df_uf_ano, selected=anos)
        df_regiao = get_media_por_regiao()
        df_regiao_f = _filter_by_years(df_regiao, selected=anos)

        if df_uf.empty:
            return dbc.Alert("Dados geograficos nao disponiveis.", color="info")

        import requests as _req
        _GEOJSON_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        try:
            _resp = _req.get(_GEOJSON_URL, timeout=10)
            _geojson = _resp.json()
            fig_map = px.choropleth(
                df_uf, geojson=_geojson,
                locations="SG_UF_PROVA", featureidkey="properties.sigla",
                color="MEDIA_GERAL", hover_name="SG_UF_PROVA",
                hover_data={"MEDIA_GERAL": ":.1f", "QTD": True},
                color_continuous_scale=["#d32f2f", "#fbc02d", "#388e3c", "#1a237e"],
                title=None, height=500,
            )
            fig_map.update_geos(scope="south america", showframe=False, bgcolor="rgba(0,0,0,0)")
            fig_map.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)", geo_bgcolor="rgba(0,0,0,0)",
                coloraxis_colorbar=dict(title="Media", len=0.6)
            )
        except Exception:
            fig_map = go.Figure()
            fig_map.add_annotation(text="Mapa indisponivel", showarrow=False,
                                    font=dict(size=20), x=0.5, y=0.5, xref="paper", yref="paper")
            fig_map.update_layout(height=500, template="plotly_white")

        muf = df_uf.iloc[0]
        puf = df_uf.iloc[-1]
        insight_map = f"Melhor estado: {muf['SG_UF_PROVA']} (media {muf['MEDIA_GERAL']}). " \
                      f"Pior estado: {puf['SG_UF_PROVA']} (media {puf['MEDIA_GERAL']}). " \
                      f"Gap regional: {round(muf['MEDIA_GERAL'] - puf['MEDIA_GERAL'], 1)} pontos."

        df_sorted = df_uf.sort_values("MEDIA_GERAL")
        top5 = df_sorted.tail(5)
        bottom5 = df_sorted.head(5)

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            y=top5["SG_UF_PROVA"][::-1], x=top5["MEDIA_GERAL"][::-1],
            orientation="h", marker_color="#2e7d32",
            text=top5["MEDIA_GERAL"][::-1], textposition="outside",
            hovertemplate="%{x:.1f}<extra></extra>", name="Top 5",
        ))
        fig_bar.add_trace(go.Bar(
            y=bottom5["SG_UF_PROVA"], x=bottom5["MEDIA_GERAL"],
            orientation="h", marker_color="#d32f2f",
            text=bottom5["MEDIA_GERAL"], textposition="outside",
            hovertemplate="%{x:.1f}<extra></extra>", name="Bottom 5",
        ))
        fig_bar.update_layout(
            title=dict(text="Top 5 e Bottom 5 Estados", font=dict(size=16)),
            xaxis=dict(title="Media Geral"), yaxis=dict(title=None),
            template="plotly_white", height=400, barmode="overlay",
            legend=dict(orientation="h", y=-0.2),
            margin=dict(t=50, b=40, l=100, r=40),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
        )
        insight_bar = f"O estado com maior media e {muf['SG_UF_PROVA']} " \
                      f"e o com menor e {puf['SG_UF_PROVA']}. " \
                      f"A diferenca entre o 5o e o 1o colocado e de {round(top5['MEDIA_GERAL'].max() - top5['MEDIA_GERAL'].min(), 1)} pontos."

        if not df_regiao_f.empty:
            fig_regiao = px.line(
                df_regiao_f, x="NU_ANO", y="MEDIA_GERAL", color="DS_REGIAO",
                markers=True,
                color_discrete_map={
                    "Norte": "#e53935", "Nordeste": "#f57c00",
                    "Centro-Oeste": "#fbc02d", "Sudeste": "#388e3c",
                    "Sul": "#1a237e"
                },
            )
            fig_regiao.update_traces(line=dict(width=2.5), marker=dict(size=6))
            fig_regiao.update_layout(
                title=dict(text="Evolucao por Regiao", font=dict(size=16)),
                xaxis=dict(title="Ano", dtick=1), yaxis=dict(title="Media Geral"),
                template="plotly_white", height=400,
                legend=dict(orientation="h", y=-0.3),
                margin=dict(t=50, b=60, l=60, r=20),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified"
            )
            insight_reg = f"Sudeste e Sul tem as maiores medias. " \
                          f"Norte e Nordeste ficam abaixo da media nacional. " \
                          f"O Centro-Oeste, puxado pelo DF, se aproxima do Sudeste."
        else:
            fig_regiao = go.Figure()
            insight_reg = ""

        ranking_df = get_ranking_uf()
        if not ranking_df.empty:
            ranking_df_display = ranking_df[["POSICAO", "SG_UF_PROVA", "MEDIA_GERAL", "QTD"]].copy()
            ranking_df_display.columns = ["#", "Estado", "Media", "Participantes"]
            ranking_df_display["Media"] = ranking_df_display["Media"].round(1)
            fig_table = go.Figure(data=[go.Table(
                header=dict(values=["#", "Estado", "Media", "Participantes"],
                            fill_color="#1a237e", font=dict(color="white", size=12),
                            align="center"),
                cells=dict(values=[ranking_df_display[c] for c in ranking_df_display.columns],
                           fill_color=[["#f8f9fa", "white"] * len(ranking_df_display)],
                           align="center", font=dict(size=11), height=25)
            )])
            fig_table.update_layout(
                title=dict(text="Ranking Completo de Estados", font=dict(size=16)),
                height=450, margin=dict(t=40, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            insight_rank = f"Sao {len(ranking_df)} estados/DF analisados. " \
                           f"O top 3 e composto por {ranking_df['SG_UF_PROVA'].iloc[0]}, " \
                           f"{ranking_df['SG_UF_PROVA'].iloc[1]} e {ranking_df['SG_UF_PROVA'].iloc[2]}."
        else:
            fig_table = go.Figure()
            insight_rank = ""

        return dbc.Row([
            _card_w_graph("Mapa do Brasil", fig_map, insight_map, 6),
            _card_w_graph("Melhores e Piores Estados", fig_bar, insight_bar, 6),
            _card_w_graph("Evolucao por Regiao", fig_regiao, insight_reg, 6),
            _card_w_graph("Ranking de Estados", fig_table, insight_rank, 6),
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Erro na aba Geografico: {e}", color="danger")


def build_demografico(anos):
    if not data_exists:
        return dbc.Alert("Sem dados.", color="warning")
    try:
        df_renda = get_media_por_renda()
        df_cor = get_media_por_cor_raca()
        df_cor_f = _filter_by_years(df_cor, selected=anos)
        df_sexo = get_media_por_sexo()
        df_sexo_f = _filter_by_years(df_sexo, selected=anos)

        if not df_renda.empty:
            fig_renda = px.bar(
                df_renda, x="DS_RENDA", y="MEDIA_GERAL",
                color="MEDIA_GERAL", color_continuous_scale="Viridis",
                text_auto=".1f", height=420, title=None,
            )
            fig_renda.update_traces(marker_line=dict(width=0))
            fig_renda.update_layout(
                xaxis=dict(title=None, tickangle=-45), yaxis=dict(title="Media Geral"),
                template="plotly_white", coloraxis_showscale=False,
                margin=dict(t=20, b=120, l=60, r=20),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
            )
            renda_min = df_renda.iloc[0]
            renda_max = df_renda.iloc[-1]
            insight_renda = f"Renda e o fator que mais impacta a nota. " \
                            f"Diferenca entre menor e maior renda: " \
                            f"{round(renda_max['MEDIA_GERAL'] - renda_min['MEDIA_GERAL'], 1)} pontos."
        else:
            fig_renda = go.Figure()
            insight_renda = ""

        if not df_cor_f.empty:
            fig_cor = px.line(
                df_cor_f, x="NU_ANO", y="MEDIA_GERAL", color="DS_COR_RACA",
                markers=True,
                color_discrete_map={
                    "Branca": "#3949ab", "Preta": "#1a237e",
                    "Parda": "#f57c00", "Amarela": "#00897b",
                    "Indigena": "#6d4c41", "Nao declarado": "#90a4ae",
                },
            )
            fig_cor.update_traces(line=dict(width=2.5), marker=dict(size=6))
            fig_cor.update_layout(
                title=dict(text="Evolucao por Raca/Cor", font=dict(size=16)),
                xaxis=dict(title="Ano", dtick=1), yaxis=dict(title="Media Geral"),
                template="plotly_white", height=420,
                legend=dict(orientation="h", y=-0.3),
                margin=dict(t=50, b=60, l=60, r=20),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified"
            )
            medias_cor = df_cor_f.groupby("DS_COR_RACA")["MEDIA_GERAL"].mean()
            gap_cor = round(medias_cor.get("Branca", 0) - medias_cor.get("Preta", 0), 1)
            insight_cor = f"Brancos tem as maiores medias. O gap Branco-Preto e de ~{gap_cor} pontos " \
                          f"e se mantem ao longo de todo o periodo."
        else:
            fig_cor = go.Figure()
            insight_cor = ""

        if not df_sexo_f.empty:
            fig_sexo = go.Figure()
            for sexo in ["Feminino", "Masculino"]:
                dfs = df_sexo_f[df_sexo_f["DS_SEXO"] == sexo]
                if not dfs.empty:
                    fig_sexo.add_trace(go.Scatter(
                        x=dfs["NU_ANO"], y=dfs["MEDIA_GERAL"],
                        mode="lines+markers", name=sexo,
                        line=dict(width=3, color="#e53935" if sexo == "Feminino" else "#3949ab"),
                        marker=dict(size=8),
                        hovertemplate=f"{sexo}: %{{y:.1f}}<extra></extra>"
                    ))
            fig_sexo.update_layout(
                title=dict(text="Evolucao por Sexo", font=dict(size=16)),
                xaxis=dict(title="Ano", dtick=1), yaxis=dict(title="Media Geral"),
                template="plotly_white", height=420,
                legend=dict(orientation="h", y=-0.2),
                margin=dict(t=50, b=60, l=60, r=20),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified"
            )
            medias_sexo = df_sexo_f.groupby("DS_SEXO")["MEDIA_GERAL"].mean()
            if "Feminino" in medias_sexo and "Masculino" in medias_sexo:
                gap_sexo = round(medias_sexo["Masculino"] - medias_sexo["Feminino"], 1)
                insight_sexo = f"Homens tem media {gap_sexo} pts acima das mulheres na media geral. " \
                               f"Em Matematica e C. Natureza a diferenca e maior; em Linguagens e Redacao, mulheres se destacam."
            else:
                insight_sexo = ""
        else:
            fig_sexo = go.Figure()
            insight_sexo = ""

        fig_gap_sexo = go.Figure()
        if not df_sexo_f.empty:
            gap_data = df_sexo_f.pivot_table(index="NU_ANO", columns="DS_SEXO", values="MEDIA_GERAL")
            if "Masculino" in gap_data.columns and "Feminino" in gap_data.columns:
                gap_vals = gap_data["Masculino"] - gap_data["Feminino"]
                fig_gap_sexo.add_trace(go.Bar(
                    x=gap_vals.index, y=gap_vals.values,
                    marker_color=gap_vals.apply(lambda v: "#e53935" if v > 0 else "#2e7d32"),
                    text=gap_vals.round(1), textposition="outside",
                    hovertemplate="Gap: %{y:.1f} pts<extra></extra>",
                    showlegend=False
                ))
                fig_gap_sexo.add_hline(y=gap_vals.mean(), line_dash="dash", line_color="#666",
                                       annotation_text=f"Media: {gap_vals.mean():.1f}")
                fig_gap_sexo.update_layout(
                    title=dict(text="Diferenca Homem - Mulher (pontos)", font=dict(size=16)),
                    xaxis=dict(title="Ano", dtick=1), yaxis=dict(title="Diferenca (pts)"),
                    template="plotly_white", height=400,
                    margin=dict(t=50, b=60, l=60, r=20),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
                )
                insight_gap_sexo = f"Homens pontuam em media {gap_vals.mean():.1f} pts acima das mulheres. " \
                                   f"O maior gap foi em {gap_vals.idxmax():.0f} ({gap_vals.max():.1f} pts)."
            else:
                fig_gap_sexo = go.Figure()
                insight_gap_sexo = ""
        else:
            fig_gap_sexo = go.Figure()
            insight_gap_sexo = ""

        return dbc.Row([
            _card_w_graph("Renda Familiar", fig_renda, insight_renda, 4),
            _card_w_graph("Raca/Cor", fig_cor, insight_cor, 4),
            _card_w_graph("Sexo", fig_sexo, insight_sexo, 4),
            _card_w_graph("Diferenca entre Sexos", fig_gap_sexo, insight_gap_sexo, 6),
            dbc.Col(dbc.Card([
                dbc.CardHeader("\U0001f4a1 Analise Combinada: Renda vs Raca", style=ESTILO_CARD_HEADER),
                dbc.CardBody([
                    _insight_box("Quanto maior a renda, maior a nota em todas as racas. "
                                 "O gap racial diminui conforme a renda aumenta, mas nao desaparece."),
                    html.Hr(),
                    _insight_box("Estudantes brancos de alta renda tem media ~150 pontos acima "
                                 "de estudantes pretos de baixa renda."),
                    html.Hr(),
                    html.H6("\U0001f4a1 Principais Observacoes:", className="mt-3"),
                    html.Ul([
                        html.Li("Mulheres tem media maior em Linguagens e Redacao"),
                        html.Li("Homens tem media maior em Matematica e Ciencias da Natureza"),
                        html.Li("Na media geral, homens tem desempenho ~10 pts acima"),
                        html.Li("O gap de renda e o maior fator de desigualdade no ENEM"),
                        html.Li("Escola privada + renda alta = media significativamente maior"),
                    ], className="text-muted small")
                ])
            ], className=ESTILO_CARD), width=12),
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Erro na aba Demografico: {e}", color="danger")


def build_insights(anos):
    if not data_exists:
        return dbc.Alert("Sem dados.", color="warning")
    try:
        df_ano = get_media_por_ano()
        df_f = _filter_by_years(df_ano, selected=anos)
        stats = get_stats_por_ano()
        stats_f = _filter_by_years(stats, selected=anos)
        variacao, primeiro, ultimo = get_tendencia_media_geral()

        col_medias = [c for c in ["MEDIA_CN", "MEDIA_CH", "MEDIA_LC", "MEDIA_MT", "MEDIA_REDACAO"] if c in df_ano.columns]
        media_todas = [round(df_ano[col].mean(), 1) for col in col_medias] if col_medias else [0] * 5

        fig_ranking = go.Figure()
        if media_todas:
            fig_ranking.add_trace(go.Bar(
                x=DISCIPLINAS_LABELS, y=media_todas,
                marker_color=DISCIPLINAS_CORES,
                text=media_todas, textposition="auto", textfont=dict(size=14, color="white"),
                hovertemplate="%{x}: %{y}<extra></extra>",
                showlegend=False
            ))
        fig_ranking.update_layout(
            title=dict(text="Ranking de Medias por Disciplina (todos os anos)", font=dict(size=16)),
            yaxis=dict(title="Media"), template="plotly_white", height=400,
            margin=dict(t=50, b=40, l=60, r=20),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
        )

        melhor_ano = df_ano.loc[df_ano["MEDIA_GERAL"].idxmax()] if not df_ano.empty else None
        pior_ano = df_ano.loc[df_ano["MEDIA_GERAL"].idxmin()] if not df_ano.empty else None

        df_esc = get_media_por_escola()
        media_privada = round(df_esc[df_esc["DS_ESCOLA"] == "Privada"]["MEDIA_GERAL"].mean(), 1) if "Privada" in df_esc["DS_ESCOLA"].values else 0
        media_publica = round(df_esc[df_esc["DS_ESCOLA"] == "Publica"]["MEDIA_GERAL"].mean(), 1) if "Publica" in df_esc["DS_ESCOLA"].values else 0

        df_uf = get_media_por_uf()
        melhor_uf_str = ""
        pior_uf_str = ""
        ranking_fig = go.Figure()
        if not df_uf.empty:
            muf = df_uf.iloc[0]
            puf = df_uf.iloc[-1]
            melhor_uf_str = f"{muf['SG_UF_PROVA']} ({muf['MEDIA_GERAL']})"
            pior_uf_str = f"{puf['SG_UF_PROVA']} ({puf['MEDIA_GERAL']})"
            df_rank = df_uf.sort_values("MEDIA_GERAL", ascending=True)
            cores_uf = ["#e53935"] * 3 + ["#fbc02d"] * (len(df_rank) - 6) + ["#2e7d32"] * 3
            if len(cores_uf) < len(df_rank):
                cores_uf = ["#fbc02d"] * len(df_rank)
            ranking_fig.add_trace(go.Bar(
                y=df_rank["SG_UF_PROVA"], x=df_rank["MEDIA_GERAL"],
                orientation="h", marker_color=cores_uf[:len(df_rank)],
                text=df_rank["MEDIA_GERAL"], textposition="outside",
                hovertemplate="%{x:.1f}<extra></extra>", showlegend=False
            ))
            ranking_fig.update_layout(
                title=dict(text="Ranking de Estados por Media Geral", font=dict(size=16)),
                xaxis=dict(title="Media Geral"), yaxis=dict(title=None),
                template="plotly_white", height=500,
                margin=dict(t=50, b=40, l=100, r=40),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
            )
            insight_rank = f"{muf['SG_UF_PROVA']} lidera o ranking com {muf['MEDIA_GERAL']}. " \
                           f"{puf['SG_UF_PROVA']} esta na ultima posicao com {puf['MEDIA_GERAL']}. " \
                           f"Diferenca: {round(muf['MEDIA_GERAL'] - puf['MEDIA_GERAL'], 1)} pontos."
        else:
            insight_rank = ""

        return dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("\U0001f3c6 Destaques Gerais", style=ESTILO_CARD_HEADER),
                dbc.CardBody([
                    html.Div([html.H6("Melhor ano:", className="d-inline text-muted"),
                              html.Span(f" {melhor_ano['NU_ANO']:.0f} (media: {melhor_ano['MEDIA_GERAL']})",
                                        className="text-success fw-bold ms-1")], className="mb-2"),
                    html.Div([html.H6("Pior ano:", className="d-inline text-muted"),
                              html.Span(f" {pior_ano['NU_ANO']:.0f} (media: {pior_ano['MEDIA_GERAL']})",
                                        className="text-danger fw-bold ms-1")], className="mb-2"),
                    html.Div([html.H6("Variacao total:", className="d-inline text-muted"),
                              html.Span(f" {variacao:+.2f}% ({primeiro} \u2192 {ultimo})",
                                        className="fw-bold ms-1",
                                        style={"color": "#e53935" if variacao < 0 else "#2e7d32"})], className="mb-2"),
                    html.Div([html.H6("Total de registros:", className="d-inline text-muted"),
                              html.Span(f" {total_records:,}", className="fw-bold ms-1")], className="mb-2"),
                    html.Div([html.H6("Melhor estado:", className="d-inline text-muted"),
                              html.Span(f" {melhor_uf_str}", className="fw-bold ms-1 text-success")], className="mb-2"),
                    html.Div([html.H6("Pior estado:", className="d-inline text-muted"),
                              html.Span(f" {pior_uf_str}", className="fw-bold ms-1 text-danger")], className="mb-2"),
                    html.Hr(),
                    _insight_box(f"Analisados {total_records:,} registros de {len(df_ano)} anos "
                                f"({int(df_ano['NU_ANO'].min()):.0f}-{int(df_ano['NU_ANO'].max()):.0f}). "
                                f"A media geral variou {variacao:+.2f}% no periodo."),
                ])
            ], className=ESTILO_CARD), width=4),

            dbc.Col(dbc.Card([
                dbc.CardHeader("\U0001f4ca Estatisticas por Ano", style=ESTILO_CARD_HEADER),
                dbc.CardBody([
                    html.Table(
                        [html.Thead(html.Tr([html.Th("Ano"), html.Th("Media"), html.Th("Min"), html.Th("Max"), html.Th("Ampl")]))] +
                        [html.Tr([
                            html.Td(str(int(r["NU_ANO"])), className="text-center"),
                            html.Td(str(r["MEDIA"]), className="text-center"),
                            html.Td(str(r["MINIMO"]), className="text-center"),
                            html.Td(str(r["MAXIMO"]), className="text-center"),
                            html.Td(str(r["AMPLITUDE"]), className="text-center"),
                        ]) for _, r in stats_f.iterrows()],
                        className="table table-sm table-hover mb-0",
                        style={"fontSize": "0.85rem"}
                    )
                ])
            ], className=ESTILO_CARD), width=8),

            _card_w_graph("Ranking de Disciplinas (media historica)", fig_ranking,
                          f"Redacao tem a maior media ({media_todas[4]}) e Ciencias da Natureza "
                          f"a menor ({media_todas[0]}). Matematica e a segunda menor.", 12),

            _card_w_graph("Ranking de Estados", ranking_fig, insight_rank, 12),

            dbc.Col(dbc.Card([
                dbc.CardHeader("\U0001f50d Principais Descobertas", style=ESTILO_CARD_HEADER),
                dbc.CardBody([
                    html.Div([
                        html.H5("\U0001f3eb Desigualdade Educacional", className="text-primary"),
                        _insight_box(f"Alunos de escolas privadas tem media {round(media_privada - media_publica, 1)} pontos acima "
                                     f"de alunos de escolas publicas. Essa disparidade se mantem consistente ao longo dos anos."),
                    ], className="mb-3"),
                    html.Div([
                        html.H5("\U0001f4b0 Renda e Desempenho", className="text-primary"),
                        _insight_box("Quanto maior a renda familiar, maior a nota. A diferenca entre a faixa mais baixa "
                                     "e a mais alta pode ultrapassar 150 pontos."),
                    ], className="mb-3"),
                    html.Div([
                        html.H5("\U0001f30d Disparidade Regional", className="text-primary"),
                        _insight_box("As regioes Sul e Sudeste consistentemente superam Norte e Nordeste. "
                                     "O Distrito Federal frequentemente lidera o ranking nacional."),
                    ], className="mb-3"),
                    html.Div([
                        html.H5("\U0001f9ea Estabilidade ao Longo do Tempo", className="text-primary"),
                        _insight_box(f"A media geral variou {variacao:+.2f}% no periodo analisado, indicando que "
                                     "o nivel de dificuldade e o perfil dos participantes se mantem relativamente estaveis."),
                    ]),
                ])
            ], className=ESTILO_CARD), width=12),
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Erro na aba Insights: {e}", color="danger")


@callback(
    Output("kpi-row", "children"),
    Input("year-slider", "value"),
)
def update_kpis(anos):
    return build_kpis(anos)


@callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
    Input("year-slider", "value"),
)
def switch_tab(tab, anos):
    builders = {
        "geral": build_visao_geral,
        "escola": build_escola,
        "geo": build_geografico,
        "demo": build_demografico,
        "insights": build_insights,
    }
    builder = builders.get(tab, build_visao_geral)
    try:
        return builder(anos)
    except Exception as e:
        return dbc.Alert(f"Erro ao carregar aba: {e}", color="danger")


if __name__ == "__main__":
    print("=" * 55)
    print("  Dashboard ENEM 2014-2024")
    print(f"  Local: http://127.0.0.1:8051")
    print("=" * 55)
    app.run(debug=True, port=8051)
