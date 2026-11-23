import numpy as np
import pandas as pd
import plotly.express as px
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget

# ---------------------------------------------------------------------------
# 1. Conjunto de dados: Evasão e Desempenho na UFPB
# (3 variáveis numéricas + 1 categórica, conforme exigido no item 1a)
# ---------------------------------------------------------------------------
rng = np.random.default_rng(42)

centros = ["CCEN", "CT", "CCHLA", "CCS"]
cursos = {
    "CCEN": ["Estatística", "Matemática", "Ciência da Computação", "Física"],
    "CT": ["Engenharia Civil", "Engenharia Elétrica", "Engenharia Mecânica", "Arquitetura"],
    "CCHLA": ["História", "Geografia", "Filosofia", "Letras"],
    "CCS": ["Medicina", "Enfermagem", "Odontologia", "Nutrição"],
}

dados = []
for semestre in ["2024.1", "2024.2", "2025.1"]:
    for centro in centros:
        for curso in cursos[centro]:
            ingressantes = int(rng.integers(30, 100))
            taxa_evasao = round(float(rng.uniform(10.0, 40.0)), 1)
            concluintes = max(1, int(round(ingressantes * (1 - taxa_evasao / 100) * 0.8)))
            dados.append(
                {
                    "centro": centro,
                    "curso": curso,
                    "semestre": semestre,
                    "ingressantes": ingressantes,
                    "concluintes": concluintes,
                    "taxa_evasao": taxa_evasao,
                }
            )

df_ufpb = pd.DataFrame(dados)

VARIAVEIS_NUM = {
    "taxa_evasao": "Taxa de Evasão (%)",
    "ingressantes": "Número de Ingressantes",
    "concluintes": "Número de Concluintes",
}

# ---------------------------------------------------------------------------
# 2. Interface (UI): Título, descrição, 3 entradas, 2 gráficos e 1 tabela
# ---------------------------------------------------------------------------
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h5("Painel de Controle"),
        # Entrada 1: seleção de variável
        ui.input_select(
            "variavel",
            "Variável para o Boxplot:",
            choices=VARIAVEIS_NUM,
            selected="taxa_evasao",
        ),
        # Entrada 2: slider para filtrar
        ui.input_slider(
            "faixa_evasao",
            "Filtrar Taxa de Evasão (%):",
            min=0.0,
            max=50.0,
            value=(0.0, 50.0),
        ),
        # Entrada 3: checkbox para agrupar
        ui.input_checkbox(
            "agrupar_centro",
            "Agrupar por Centro de Ensino",
            value=True,
        ),
    ),
    ui.h2("Evasão e Desempenho na UFPB"),
    ui.p(
        "Aplicativo interativo para explorar ingressantes, concluintes e taxa de "
        "evasão nos centros de ensino da UFPB."
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Ingressantes vs. Concluintes"),
            output_widget("grafico_scatter"),
        ),
        ui.card(
            ui.card_header("Distribuição por Centro"),
            output_widget("grafico_boxplot"),
        ),
    ),
    ui.card(
        ui.card_header("Estatísticas Descritivas"),
        ui.output_table("tabela_descritiva"),
    ),
)

# ---------------------------------------------------------------------------
# 3. Servidor (Server)
# ---------------------------------------------------------------------------
def server(input, output, session):
    @reactive.calc
    def dados_filtrados():
        ev_min, ev_max = input.faixa_evasao()
        return df_ufpb[
            (df_ufpb["taxa_evasao"] >= ev_min) & (df_ufpb["taxa_evasao"] <= ev_max)
        ]

    @render_widget
    def grafico_scatter():
        df = dados_filtrados()
        cor = "centro" if input.agrupar_centro() else None
        return px.scatter(
            df,
            x="ingressantes",
            y="concluintes",
            color=cor,
            hover_data=["curso", "semestre", "taxa_evasao"],
            labels={
                "ingressantes": "Ingressantes",
                "concluintes": "Concluintes",
                "centro": "Centro",
            },
        )

    @render_widget
    def grafico_boxplot():
        df = dados_filtrados()
        var = input.variavel()
        eixo_x = "centro" if input.agrupar_centro() else None
        return px.box(
            df,
            x=eixo_x,
            y=var,
            color=eixo_x,
            labels={
                "centro": "Centro",
                var: VARIAVEIS_NUM[var],
            },
        )

    @render.table
    def tabela_descritiva():
        df = dados_filtrados()
        linhas = []
        for col, nome in VARIAVEIS_NUM.items():
            s = df[col]
            linhas.append(
                {
                    "Variável": nome,
                    "Média": round(float(s.mean()), 2) if len(s) else None,
                    "Desvio-Padrão": round(float(s.std()), 2) if len(s) > 1 else 0.0,
                    "Mínimo": round(float(s.min()), 2) if len(s) else None,
                    "Máximo": round(float(s.max()), 2) if len(s) else None,
                }
            )
        return pd.DataFrame(linhas)


app = App(app_ui, server)