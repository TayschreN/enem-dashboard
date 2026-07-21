import dash
from dash import dcc, html, Input, Output, callback
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
                title="Dashboard ENEM 2019-2024 | Engenharia de Dados",
                update_title=None)

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .nav-link-dash {
                font-weight: 600 !important;
                cursor: pointer !important;
                border-radius: 8px 8px 0 0 !important;
                transition: all 0.2s ease !important;
                color: #666 !important;
                padding: 10px 20px !important;
            }
            .nav-link-dash:hover {
                background: rgba(26,35,126,0.06) !important;
                color: #1a237e !important;
            }
            .nav-link-dash.active {
                background: white !important;
                color: #1a237e !important;
                border-bottom: 3px solid #1a237e !important;
                font-weight: 700 !important;
            }
            .nav-tabs .nav-link {
                border: none !important;
            }
            ._dash-loading {
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 200px;
                color: #1a237e;
                font-size: 1.2rem;
            }
            .rc-slider-track {
                background-color: #1a237e !important;
            }
            .rc-slider-handle {
                border-color: #1a237e !important;
                box-shadow: 0 2px 6px rgba(26,35,126,0.3) !important;
            }
            .rc-slider-handle:hover {
                border-color: #283593 !important;
            }
            .card.hover-lift:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.1) !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""
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
DISCIPLINAS_CORES = ["#636efa", "#00cc96", "#ef553b", "#ab63fa", "#ffa15a"]

ESTILO_CARD = "shadow-sm border-0 mb-3 rounded-4"
ESTILO_CARD_HEADER = {"fontWeight": "700", "backgroundColor": "#f8f9fa", "borderBottom": "2px solid #e9ecef",
                       "borderRadius": "calc(0.5rem - 1px) calc(0.5rem - 1px) 0 0", "padding": "14px 20px"}

app.layout = dbc.Container([

    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H1("\U0001f4ca ENEM Data Analysis",
                            className="d-inline-block",
                            style={"fontWeight": "700", "fontSize": "2.2rem", "color": "white"}),
                    html.Span(" 2019 - 2024", style={"fontSize": "1.5rem", "color": "rgba(255,255,255,0.8)"}),
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
        "background": "linear-gradient(135deg, #0f0c29 0%, #1a237e 50%, #24243e 100%)",
        "padding": "28px 36px", "borderRadius": "16px", "marginBottom": "24px",
        "boxShadow": "0 12px 40px rgba(26,35,126,0.25)"
    }),

    dbc.Row(id="kpi-row", className="mb-3"),

    dbc.Row([
        dbc.Col([
            html.Label("Selecione os anos:", style={"fontWeight": "600", "fontSize": "0.9rem", "color": "#555"}),
            dcc.RangeSlider(
                id="year-slider",
                min=2019, max=2024,
                value=[2019, 2024],
                marks={str(y): str(y) for y in range(2019, 2025)},
                step=1,
                tooltip={"placement": "top", "always_visible": True},
                allowCross=False,
            ),
        ], width=12, className="px-3 mb-3"),
    ]),

    dcc.Store(id="tab-store", data="geral"),

    dbc.Nav([
        dbc.NavLink(["\U0001f4ca Visao Geral"], id="nav-geral", n_clicks=0, active=True,
                    className="nav-link-dash"),
        dbc.NavLink(["\U0001f3eb Escolas"], id="nav-escola", n_clicks=0, active=False,
                    className="nav-link-dash"),
        dbc.NavLink(["\U0001f5fa Geografico"], id="nav-geo", n_clicks=0, active=False,
                    className="nav-link-dash"),
        dbc.NavLink(["\U0001f465 Demografico"], id="nav-demo", n_clicks=0, active=False,
                    className="nav-link-dash"),
        dbc.NavLink(["\U0001f4a1 Insights"], id="nav-insights", n_clicks=0, active=False,
                    className="nav-link-dash"),
    ], id="tabs", className="nav-tabs nav-fill mb-3",
       style={"borderBottom": "2px solid #e0e0e0", "gap": "2px"}),

    dbc.Row([
        dbc.Col(id="tab-content", width=12)
    ])

], fluid=True, style={"backgroundColor": "#f0f2f6", "minHeight": "100vh", "padding": "24px 28px"})


def _card(children, color="#1a237e", width=2, extra_class=""):
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(children, className="text-center py-3"),
            className=f"border-0 shadow-sm {extra_class}",
            style={"borderLeft": f"4px solid {color}", "borderRadius": "12px",
                   "transition": "transform 0.15s, box-shadow 0.15s"}
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
       style={"backgroundColor": "#f0f4ff", "borderRadius": "10px", "borderLeft": "4px solid #1a237e",
               "boxShadow": "0 1px 3px rgba(0,0,0,0.04)"})


_GRAFICO_BASE = dict(
    template="plotly_white", hovermode="x unified",
    font=dict(family="Segoe UI, system-ui, sans-serif", size=12),
    hoverlabel=dict(bgcolor="#1a237e", font=dict(color="white", size=12)),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(gridcolor="rgba(0,0,0,0.06)", zerolinecolor="rgba(0,0,0,0.08)"),
    yaxis=dict(gridcolor="rgba(0,0,0,0.06)", zerolinecolor="rgba(0,0,0,0.08)"),
)


def _card_w_graph(title, figure, insight_text="", width=6):
    figure.update_layout(title=dict(text=title, font=dict(size=15, color="#1a237e")), **_GRAFICO_BASE)
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

        if len(df) >= 2:
            primeiro_val = df["MEDIA_GERAL"].iloc[0]
            ultimo_val = df["MEDIA_GERAL"].iloc[-1]
            variacao = round(((ultimo_val - primeiro_val) / primeiro_val) * 100, 2)
        else:
            variacao = 0.0

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
        if not df_ano_f.empty:
            anos_x = df_ano_f["NU_ANO"]
            for disc, label, cor in zip(DISCIPLINAS_LIST, DISCIPLINAS_LABELS, DISCIPLINAS_CORES):
                col = disc.replace("NU_NOTA_", "MEDIA_") if disc.startswith("NU_NOTA_") else disc
                if col in df_ano_f.columns and not df_ano_f[col].isna().all():
                    fig_evolucao.add_trace(go.Scatter(
                        x=anos_x, y=df_ano_f[col],
                        mode="lines+markers", name=label,
                        line=dict(width=3, color=cor, shape="spline", smoothing=0.3),
                        marker=dict(size=8, symbol="circle", line=dict(width=1, color="white")),
                        hovertemplate="<b>%{fullData.name}</b><br>%{x}: %{y:.1f}<extra></extra>"
                    ))
            fig_evolucao.update_layout(
                xaxis=dict(title="Ano", dtick=1, showgrid=True, rangeslider=dict(visible=True, thickness=0.05)),
                yaxis=dict(title="Media", range=[400, 700], showgrid=True, zeroline=False),
                legend=dict(orientation="h", yanchor="top", y=-0.2, font=dict(size=11)),
                height=440, margin=dict(b=100, t=30),
                hovermode="x unified",
            )

        cols_media = [c for c in df_ano_f.columns if c.startswith("MEDIA_")]
        insight_evol = f"Redacao tem a maior media historica, enquanto Ciencias da Natureza tem a menor. " \
                       f"Linguagens apresenta a maior estabilidade ao longo dos anos."

        fig_participacao = go.Figure()
        if not df_total_f.empty:
            fig_participacao.add_trace(go.Bar(
                x=df_total_f["NU_ANO"], y=df_total_f["QTD"],
                marker=dict(color="#636efa", opacity=0.65, line=dict(width=0)),
                hovertemplate="<b>%{x}</b><br>Participantes: %{y:,}<extra></extra>",
                showlegend=False, name="Participantes"
            ))
            fig_participacao.add_trace(go.Scatter(
                x=df_total_f["NU_ANO"], y=df_total_f["QTD"],
                mode="lines+markers", showlegend=False,
                line=dict(color="#ef553b", width=2.5, shape="spline", smoothing=0.3),
                marker=dict(size=10, symbol="diamond", color="#ef553b", line=dict(width=1.5, color="white")),
                hovertemplate="<b>%{x}</b><br>%{y:,}<extra></extra>"
            ))
            pico_val = df_total_f.loc[df_total_f["QTD"].idxmax()]
            fig_participacao.add_annotation(
                x=pico_val["NU_ANO"], y=pico_val["QTD"],
                text=f"Pico: {int(pico_val['QTD']):,}",
                showarrow=True, arrowhead=2, arrowsize=1.2, arrowcolor="#ef553b",
                font=dict(size=11, color="#ef553b"), bgcolor="white", bordercolor="#ef553b", borderwidth=1,
                ax=0, ay=-35
            )
        fig_participacao.update_layout(
            xaxis=dict(title="Ano", dtick=1, showgrid=True),
            yaxis=dict(title="Participantes", tickformat=",", showgrid=True, zeroline=False),
            height=420,
        )

        pico = df_total_f.loc[df_total_f["QTD"].idxmax()] if not df_total_f.empty else None
        insight_part = f"O ano de {pico['NU_ANO']:.0f} teve o maior numero de participantes ({int(pico['QTD']):,}). " \
                       f"Ha uma tendencia de queda nas inscricoes a partir de 2019." if pico is not None else ""

        df_dist = get_distribuicao_notas()
        df_dist_f = _filter_by_years(df_dist, selected=anos)
        if not df_dist_f.empty:
            pivot = df_dist_f.pivot_table(index="NU_ANO", columns="FAIXA_NOTA", values="QTD")
            pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
            faixa_order = ["0-300", "300-400", "400-500", "500-600", "600-700", "700-800", "800-1000"]
            faixa_exists = [c for c in faixa_order if c in pivot_pct.columns]
            pivot_pct = pivot_pct[faixa_exists]
            text_for_heatmap = np.round(pivot_pct.values, 1)
            textfont_for_heatmap = [
                ["white" if v > 50 else "#333" for v in row]
                for row in pivot_pct.values
            ]
            fig_heatmap = go.Figure(data=go.Heatmap(
                z=pivot_pct.values, x=[c.replace("-", " a ") for c in faixa_exists],
                y=[str(int(y)) for y in pivot_pct.index],
                colorscale="Blues",
                text=text_for_heatmap,
                texttemplate="%{text}%", textfont=dict(size=12),
                hovertemplate="<b>%{y}</b><br>Faixa: %{x}<br>%{z:.1f}%<extra></extra>",
            ))
            fig_heatmap.update_layout(
                xaxis=dict(title="Faixa de Nota"), yaxis=dict(title="Ano"),
                height=450,
            )
            insight_heatmap = "A maior concentracao de participantes esta nas faixas de 400 a 600 pontos. " \
                              "A distribuicao e consistente entre os anos, com leve deslocamento para a direita."
        else:
            fig_heatmap = go.Figure()
            insight_heatmap = ""

        fig_radar = go.Figure()
        insight_radar = ""

        if not df_corr.empty:
            fig_corr = px.imshow(
                df_corr, text_auto=".2f", aspect="auto",
                color_continuous_scale=px.colors.diverging.RdBu_r,
                zmin=-1, zmax=1,
                labels=dict(x="Disciplina", y="Disciplina", color="Correlacao"),
                x=DISCIPLINAS_LABELS, y=DISCIPLINAS_LABELS,
            )
            fig_corr.update_traces(textfont=dict(size=13, color="#333"))
            fig_corr.update_layout(
                height=440, margin=dict(t=50, b=20, l=20, r=20),
                coloraxis_colorbar=dict(title="Corr", len=0.6, thickness=15, tickvals=[-1, -0.5, 0, 0.5, 1]),
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
            colors_delta = ["#ef553b" if v < 0 else "#00cc96" for v in df_delta_f["DELTA"]]
            fig_delta.add_trace(go.Bar(
                x=df_delta_f["NU_ANO"], y=df_delta_f["DELTA"],
                marker=dict(color=colors_delta, line=dict(width=0), opacity=0.85),
                text=df_delta_f["DELTA"].round(1),
                textposition="outside", textfont=dict(size=12, color="#333"),
                hovertemplate="<b>%{x}</b><br>Delta: %{y:+.1f} pts<extra></extra>", showlegend=False
            ))
            fig_delta.add_hline(y=0, line_color="#999", line_width=1, line_dash="dash")
        fig_delta.update_layout(
            xaxis=dict(title="Ano", dtick=1, showgrid=False),
            yaxis=dict(title="Delta (pontos)", showgrid=True, zeroline=False),
            height=400,
        )

        if len(df_ano_f) >= 2:
            prim = df_ano_f["MEDIA_GERAL"].iloc[0]
            ult = df_ano_f["MEDIA_GERAL"].iloc[-1]
            var_delta = round(((ult - prim) / prim) * 100, 2)
        else:
            var_delta = 0.0
            prim = ult = 0
        insight_delta = f"A media geral variou {var_delta:+.2f}% no periodo ({prim} -> {ult}). " \
                        f"O maior aumento ocorreu no ano com maior variacao positiva no grafico."

        return dbc.Row([
            _card_w_graph("Evolucao das Notas", fig_evolucao, insight_evol, 6),
            _card_w_graph("Participacao", fig_participacao, insight_part, 6),
            _card_w_graph("Distribuicao das Notas", fig_heatmap, insight_heatmap, 6),
            _card_w_graph("Variacao Anual (Delta)", fig_delta, insight_delta, 6),
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
                cor_escola = "#00cc96" if escola == "Privada" else "#636efa"
                fig_comparacao.add_trace(go.Bar(
                    name=escola, x=dfe["NU_ANO"], y=dfe["MEDIA_GERAL"],
                    text=dfe["MEDIA_GERAL"], textposition="auto",
                    textfont=dict(size=11, color="white"),
                    marker=dict(color=cor_escola, opacity=0.88, line=dict(width=0)),
                    hovertemplate=f"<b>{escola}</b><br>%{{x}}: %{{y}}<extra></extra>"
                ))
        fig_comparacao.update_layout(
            xaxis=dict(title="Ano", dtick=1, showgrid=False),
            yaxis=dict(title="Media Geral", showgrid=True, zeroline=False),
            barmode="group", height=420, margin=dict(b=60),
            legend=dict(orientation="h", y=-0.2, font=dict(size=11)),
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
        colors_gap = ["#00cc96" if v >= 0 else "#ef553b" for v in diff.values]
        fig_gap.add_trace(go.Bar(
            x=diff.index, y=diff.values,
            marker=dict(color=colors_gap, line=dict(width=0), opacity=0.85),
            text=diff.values.round(1), textposition="outside",
            textfont=dict(size=11, color="#333"),
            hovertemplate="<b>%{x}</b><br>Gap: %{y:.1f} pts<extra></extra>",
            showlegend=False
        ))
        fig_gap.add_hline(y=gap_medio2, line_dash="dash", line_color="#999",
                          annotation_text=f"Media: {gap_medio2} pts", annotation_position="bottom right",
                          annotation_font=dict(size=11, color="#666"))
        fig_gap.update_layout(
            xaxis=dict(title="Ano", dtick=1, showgrid=False),
            yaxis=dict(title="Diferenca (pontos)", showgrid=True, zeroline=False),
            height=400,
        )
        insight_gap = f"O maior gap ocorreu em {diff.idxmax():.0f} ({diff.max():.1f} pts) " \
                      f"e o menor em {diff.idxmin():.0f} ({diff.min():.1f} pts)."

        df_raca_esc = get_media_raca_escola()
        fig_inter = go.Figure()
        if not df_raca_esc.empty:
            escola_colors_intersec = {"Privada": "#00cc96", "Publica": "#636efa"}
            for escola_tipo in ["Publica", "Privada"]:
                df_esc_tipo = df_raca_esc[df_raca_esc["DS_ESCOLA"] == escola_tipo]
                df_esc_tipo = df_esc_tipo.set_index("DS_COR_RACA").reindex(["Branca", "Preta", "Parda"])
                fig_inter.add_trace(go.Bar(
                    name=escola_tipo,
                    x=df_esc_tipo.index, y=df_esc_tipo["MEDIA_GERAL"].values,
                    marker_color=escola_colors_intersec[escola_tipo],
                    marker=dict(opacity=0.85, line=dict(width=0)),
                    text=df_esc_tipo["MEDIA_GERAL"].round(1).values,
                    textposition="auto", textfont=dict(size=11, color="white"),
                    hovertemplate=f"<b>%{{x}}</b><br>{escola_tipo}: %{{y:.1f}}<extra></extra>",
                ))
            fig_inter.update_layout(
                title=dict(text="Nota por Raca e Tipo de Escola", font=dict(size=15)),
                xaxis=dict(title="Raca/Cor"), yaxis=dict(title="Media Geral", zeroline=False),
                barmode="group", template="plotly_white", height=420,
                legend=dict(orientation="h", y=-0.25, font=dict(size=11)),
                margin=dict(t=50, b=70, l=60, r=20),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
            )
            gap_branco_preto = df_raca_esc[df_raca_esc["DS_COR_RACA"] == "Branca"]["MEDIA_GERAL"].mean() - \
                               df_raca_esc[df_raca_esc["DS_COR_RACA"] == "Preta"]["MEDIA_GERAL"].mean()
            gap_priv_pub = df_raca_esc[df_raca_esc["DS_ESCOLA"] == "Privada"]["MEDIA_GERAL"].mean() - \
                           df_raca_esc[df_raca_esc["DS_ESCOLA"] == "Publica"]["MEDIA_GERAL"].mean()
            insight_inter = f"O gap entre estudantes brancos e pretos e de ~{gap_branco_preto:.0f} pontos. " \
                            f"Entre escola privada e publica, a diferenca e de ~{gap_priv_pub:.0f} pontos. " \
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
                color_continuous_scale=px.colors.sequential.Plasma_r,
                title=None, height=500,
            )
            fig_map.update_traces(hovertemplate="<b>%{hovertext}</b><br>Media: %{z:.1f}<br>Participantes: %{customdata[0]:,}<extra></extra>")
            fig_map.update_geos(scope="south america", showframe=False, bgcolor="rgba(0,0,0,0)",
                                projection=dict(type="mercator"),
                                showcountries=True, countrycolor="rgba(0,0,0,0.1)",
                                showsubunits=True, subunitcolor="rgba(0,0,0,0.1)")
            fig_map.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)", geo_bgcolor="rgba(0,0,0,0)",
                coloraxis_colorbar=dict(title="Media", len=0.6, thickness=15, tickprefix=""),
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
            orientation="h", marker=dict(color="#00cc96", line=dict(width=0)),
            text=top5["MEDIA_GERAL"][::-1], textposition="outside",
            textfont=dict(size=11), hovertemplate="<b>%{y}</b><br>Media: %{x:.1f}<extra></extra>",
            name="Top 5", width=0.6,
        ))
        fig_bar.add_trace(go.Bar(
            y=bottom5["SG_UF_PROVA"], x=bottom5["MEDIA_GERAL"],
            orientation="h", marker=dict(color="#ef553b", line=dict(width=0)),
            text=bottom5["MEDIA_GERAL"], textposition="outside",
            textfont=dict(size=11), hovertemplate="<b>%{y}</b><br>Media: %{x:.1f}<extra></extra>",
            name="Bottom 5", width=0.6,
        ))
        fig_bar.update_layout(
            xaxis=dict(title="Media Geral", showgrid=True, zeroline=False),
            yaxis=dict(title=None, showgrid=False),
            height=400, barmode="overlay",
            legend=dict(orientation="h", y=-0.2, font=dict(size=11)),
            margin=dict(t=30, b=60, l=100, r=50),
        )
        insight_bar = f"O estado com maior media e {muf['SG_UF_PROVA']} " \
                      f"e o com menor e {puf['SG_UF_PROVA']}. " \
                      f"A diferenca entre o 5o e o 1o colocado e de {round(top5['MEDIA_GERAL'].max() - top5['MEDIA_GERAL'].min(), 1)} pontos."

        if not df_regiao_f.empty:
            region_colors = {
                "Norte": "#ef553b", "Nordeste": "#ffa15a",
                "Centro-Oeste": "#ffd86b", "Sudeste": "#00cc96",
                "Sul": "#636efa"
            }
            fig_regiao = go.Figure()
            for reg in ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]:
                dfr = df_regiao_f[df_regiao_f["DS_REGIAO"] == reg]
                if not dfr.empty:
                    c = region_colors.get(reg, "#999")
                    fig_regiao.add_trace(go.Scatter(
                        x=dfr["NU_ANO"], y=dfr["MEDIA_GERAL"],
                        mode="lines+markers", name=reg,
                        line=dict(width=3, color=c, shape="spline", smoothing=0.3),
                        marker=dict(size=9, color=c, symbol="circle", line=dict(width=1.5, color="white")),
                        hovertemplate=f"<b>{reg}</b><br>%{{x}}: %{{y:.1f}}<extra></extra>"
                    ))
            fig_regiao.update_layout(
                xaxis=dict(title="Ano", dtick=1, showgrid=True),
                yaxis=dict(title="Media Geral", showgrid=True, zeroline=False),
                height=420, margin=dict(b=90),
                legend=dict(orientation="h", y=-0.35, font=dict(size=11)),
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
                            fill_color="#636efa", font=dict(color="white", size=12, family="Segoe UI"),
                            align="center", height=30),
                cells=dict(values=[ranking_df_display[c] for c in ranking_df_display.columns],
                           fill_color=[["rgba(99,110,250,0.06)", "rgba(99,110,250,0.02)"] * len(ranking_df_display)],
                           align="center", font=dict(size=11, color="#333"), height=26,
                           line=dict(color="rgba(0,0,0,0.04)")),
            )])
            fig_table.update_layout(
                height=450, margin=dict(t=10, b=10, l=10, r=10),
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
            fig_renda.update_traces(marker=dict(line=dict(width=0)),
                                    textfont=dict(size=10, color="white"),
                                    hovertemplate="<b>%{x}</b><br>Media: %{y:.1f}<extra></extra>")
            fig_renda.update_layout(
                xaxis=dict(title=None, tickangle=-40, showgrid=False),
                yaxis=dict(title="Media Geral", showgrid=True, zeroline=False),
                coloraxis_showscale=False,
                margin=dict(t=20, b=140, l=60, r=20),
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
            race_colors = {
                "Branca": "#636efa", "Preta": "#1a237e",
                "Parda": "#ffa15a", "Amarela": "#00cc96",
                "Indigena": "#ef553b", "Nao declarado": "#b0bec5",
            }
            fig_cor = go.Figure()
            for cor_name in ["Branca", "Preta", "Parda", "Amarela", "Indigena", "Nao declarado"]:
                dfc = df_cor_f[df_cor_f["DS_COR_RACA"] == cor_name]
                if not dfc.empty:
                    c = race_colors.get(cor_name, "#b0bec5")
                    fig_cor.add_trace(go.Scatter(
                        x=dfc["NU_ANO"], y=dfc["MEDIA_GERAL"],
                        mode="lines+markers", name=cor_name,
                        line=dict(width=3, color=c, shape="spline", smoothing=0.3),
                        marker=dict(size=8, color=c, symbol="circle", line=dict(width=1.5, color="white")),
                        hovertemplate=f"<b>{cor_name}</b><br>%{{x}}: %{{y:.1f}}<extra></extra>"
                    ))
            fig_cor.update_layout(
                xaxis=dict(title="Ano", dtick=1, showgrid=True),
                yaxis=dict(title="Media Geral", showgrid=True, zeroline=False),
                height=420, margin=dict(b=90),
                legend=dict(orientation="h", y=-0.35, font=dict(size=10)),
            )
            medias_cor = df_cor_f.groupby("DS_COR_RACA")["MEDIA_GERAL"].mean()
            gap_cor = round(medias_cor.get("Branca", 0) - medias_cor.get("Preta", 0), 1)
            insight_cor = f"Brancos tem as maiores medias. O gap Branco-Preto e de ~{gap_cor} pontos " \
                          f"e se mantem ao longo de todo o periodo."
        else:
            fig_cor = go.Figure()
            insight_cor = ""

        if not df_sexo_f.empty:
            sexo_colors = {"Masculino": "#636efa", "Feminino": "#ef553b"}
            fig_sexo = go.Figure()
            for sexo in ["Feminino", "Masculino"]:
                dfs = df_sexo_f[df_sexo_f["DS_SEXO"] == sexo]
                if not dfs.empty:
                    fig_sexo.add_trace(go.Scatter(
                        x=dfs["NU_ANO"], y=dfs["MEDIA_GERAL"],
                        mode="lines+markers", name=sexo,
                        line=dict(width=3, color=sexo_colors[sexo], shape="spline", smoothing=0.3),
                        marker=dict(size=9, color=sexo_colors[sexo],
                                    symbol="circle", line=dict(width=2, color="white")),
                        hovertemplate=f"<b>{sexo}</b><br>%{{x}}: %{{y:.1f}}<extra></extra>"
                    ))
            fig_sexo.update_layout(
                xaxis=dict(title="Ano", dtick=1, showgrid=True),
                yaxis=dict(title="Media Geral", showgrid=True, zeroline=False),
                height=420, margin=dict(b=60),
                legend=dict(orientation="h", y=-0.2, font=dict(size=11)),
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
                gap_sex_colors = ["#00cc96" if v >= 0 else "#ef553b" for v in gap_vals.values]
                fig_gap_sexo.add_trace(go.Bar(
                    x=gap_vals.index, y=gap_vals.values,
                    marker=dict(color=gap_sex_colors, line=dict(width=0), opacity=0.85),
                    text=gap_vals.round(1), textposition="outside",
                    textfont=dict(size=11, color="#333"),
                    hovertemplate="<b>%{x}</b><br>Gap: %{y:.1f} pts<extra></extra>",
                    showlegend=False
                ))
                mean_gap = gap_vals.mean()
                fig_gap_sexo.add_hline(y=mean_gap, line_dash="dash", line_color="#999",
                                       annotation_text=f"Media: {mean_gap:.1f}",
                                       annotation_font=dict(size=11, color="#666"))
                fig_gap_sexo.update_layout(
                    xaxis=dict(title="Ano", dtick=1, showgrid=False),
                    yaxis=dict(title="Diferenca (pts)", showgrid=True),
                    height=400,
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
        df_ano_f = _filter_by_years(df_ano, selected=anos)
        stats = get_stats_por_ano()
        stats_f = _filter_by_years(stats, selected=anos)
        if len(df_ano_f) >= 2:
            primeiro_valor = df_ano_f["MEDIA_GERAL"].iloc[0]
            ultimo_valor = df_ano_f["MEDIA_GERAL"].iloc[-1]
            variacao = round(((ultimo_valor - primeiro_valor) / primeiro_valor) * 100, 2)
            primeiro = round(primeiro_valor, 1)
            ultimo = round(ultimo_valor, 1)
        else:
            variacao = 0.0
            primeiro = 0
            ultimo = 0

        col_medias = [c for c in ["MEDIA_CN", "MEDIA_CH", "MEDIA_LC", "MEDIA_MT", "MEDIA_REDACAO"] if c in df_ano_f.columns]
        media_todas = [round(df_ano_f[col].mean(), 1) for col in col_medias] if col_medias else [0] * 5

        fig_ranking = go.Figure()
        if media_todas:
            sorted_idx = sorted(range(len(media_todas)), key=lambda i: media_todas[i], reverse=True)
            sorted_labels = [DISCIPLINAS_LABELS[i] for i in sorted_idx]
            sorted_values = [media_todas[i] for i in sorted_idx]
            sorted_colors = [DISCIPLINAS_CORES[i] for i in sorted_idx]
            fig_ranking.add_trace(go.Bar(
                x=sorted_labels, y=sorted_values,
                marker_color=sorted_colors,
                text=sorted_values, textposition="auto", textfont=dict(size=14, color="white"),
                hovertemplate="<b>%{x}</b><br>Media: %{y}<extra></extra>",
                showlegend=False
            ))
        fig_ranking.update_layout(
            title=dict(text="Ranking de Medias por Disciplina", font=dict(size=16)),
            yaxis=dict(title="Media", showgrid=True, zeroline=False),
            template="plotly_white", height=420,
            margin=dict(t=50, b=40, l=60, r=40),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)"
        )

        melhor_ano = df_ano_f.loc[df_ano_f["MEDIA_GERAL"].idxmax()] if not df_ano_f.empty else None
        pior_ano = df_ano_f.loc[df_ano_f["MEDIA_GERAL"].idxmin()] if not df_ano_f.empty else None

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
            n = len(df_rank)
            cores_uf = px.colors.sequential.Viridis
            colors_rank = [cores_uf[int(i * (len(cores_uf)-1) / max(n-1, 1))] for i in range(n)]
            ranking_fig.add_trace(go.Bar(
                y=df_rank["SG_UF_PROVA"], x=df_rank["MEDIA_GERAL"],
                orientation="h", marker=dict(color=colors_rank, line=dict(width=0)),
                text=df_rank["MEDIA_GERAL"], textposition="outside",
                textfont=dict(size=11), hovertemplate="<b>%{y}</b><br>Media: %{x:.1f}<extra></extra>",
                showlegend=False, width=0.7,
            ))
            ranking_fig.update_layout(
                xaxis=dict(title="Media Geral", showgrid=True, zeroline=False),
                yaxis=dict(title=None, showgrid=False),
                height=max(400, len(df_rank) * 30),
                margin=dict(t=30, b=30, l=100, r=60),
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
                    _insight_box(f"Analisados {total_records:,} registros de {len(df_ano_f)} anos "
                                f"({int(df_ano_f['NU_ANO'].min()):.0f}-{int(df_ano_f['NU_ANO'].max()):.0f}). "
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
                          f"Redacao tem a maior media ({media_todas[4] if len(media_todas) > 4 else 'N/A'}) e Ciencias da Natureza "
                          f"a menor ({media_todas[0] if len(media_todas) > 0 else 'N/A'}). Matematica e a segunda menor.", 12),

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
    Output("tab-store", "data"),
    Output("nav-geral", "active"),
    Output("nav-escola", "active"),
    Output("nav-geo", "active"),
    Output("nav-demo", "active"),
    Output("nav-insights", "active"),
    Input("nav-geral", "n_clicks"),
    Input("nav-escola", "n_clicks"),
    Input("nav-geo", "n_clicks"),
    Input("nav-demo", "n_clicks"),
    Input("nav-insights", "n_clicks"),
    prevent_initial_call=True,
)
def update_active_tab(n_geral, n_escola, n_geo, n_demo, n_insights):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, True, False, False, False, False
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    tab_map = {
        "nav-geral": "geral",
        "nav-escola": "escola",
        "nav-geo": "geo",
        "nav-demo": "demo",
        "nav-insights": "insights",
    }
    tab = tab_map.get(triggered_id, "geral")
    return tab, tab == "geral", tab == "escola", tab == "geo", tab == "demo", tab == "insights"


@callback(
    Output("tab-content", "children"),
    Input("tab-store", "data"),
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
