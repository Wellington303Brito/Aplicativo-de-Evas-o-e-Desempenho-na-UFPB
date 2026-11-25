from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget

try:
    import shinyswatch

    TEMA = shinyswatch.theme.flatly
except ImportError:
    TEMA = None

# ---------------------------------------------------------------------------
# 1. Carregamento  (discentes_ccen_ufpb.csv)
# ---------------------------------------------------------------------------
CAMINHO_CSV = Path(__file__).resolve().parent / "discentes_ccen_ufpb.csv"
df_ccen = pd.read_csv(CAMINHO_CSV)

df_ccen["Taxa Abandono (%)"] = np.where(
    df_ccen["Qtde Estudantes"] > 0,
    (df_ccen["Qtde Abandono"] / df_ccen["Qtde Estudantes"]) * 100.0,
    0.0,
).round(2)

VARIAVEIS_NUM = {
    "Qtde Estudantes": "Quantidade de Estudantes",
    "Qtde Concluintes": "Quantidade de Concluintes",
    "Qtde Abandono": "Quantidade de Abandono",
    "Qtde Trancamentos": "Quantidade de Trancamentos",
    "Taxa Abandono (%)": "Taxa de Abandono (%)",
}

ANOS_ORDENADOS = sorted(df_ccen["Ano Referencia"].unique().tolist())
CURSOS_ORDENADOS = sorted(df_ccen["Curso"].unique().tolist())
MODALIDADES_ORDENADAS = sorted(df_ccen["Modalidade"].unique().tolist())

# ---------------------------------------------------------------------------
# 2. Interface (UI)
# ---------------------------------------------------------------------------
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h5("Filtros e Controles", class_="mb-3"),
        ui.input_select(
            "variavel",
            "Variável para o Boxplot:",
            choices=VARIAVEIS_NUM,
            selected="Taxa Abandono (%)",
        ),
        ui.input_slider(
            "faixa_anos",
            "Ano de Referência:",
            min=int(min(ANOS_ORDENADOS)),
            max=int(max(ANOS_ORDENADOS)),
            value=(int(min(ANOS_ORDENADOS)), int(max(ANOS_ORDENADOS))),
            step=1,
            sep="",
        ),
        ui.input_select(
            "curso",
            "Curso:",
            choices=["Todos"] + CURSOS_ORDENADOS,
            selected="Todos",
        ),
        ui.input_select(
            "modalidade",
            "Modalidade:",
            choices=["Todas"] + MODALIDADES_ORDENADAS,
            selected="Todas",
        ),
        ui.input_checkbox(
            "colorir_modalidade",
            "Colorir por Modalidade",
            value=True,
        ),
        width=300,
    ),
    ui.div(
        ui.h2("Evasão e Desempenho — CCEN / UFPB", class_="fw-bold mb-1"),
        ui.p(
            "Análise interativa dos discentes do Centro de Ciências Exatas e da Natureza "
            "(2020–2026) a partir de estudantes, concluintes, abandonos e trancamentos.",
            class_="text-muted mb-3",
        ),
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Estudantes vs. Concluintes"),
            output_widget("grafico_scatter"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header("Distribuição por Curso"),
            output_widget("grafico_boxplot"),
            full_screen=True,
        ),
        col_widths=[6, 6],
    ),
    ui.card(
        ui.card_header("Estatísticas Descritivas"),
        ui.output_data_frame("tabela_descritiva"),
        class_="mt-2",
    ),
    title="Evasão e Desempenho — CCEN / UFPB",
    theme=TEMA,
)


# ---------------------------------------------------------------------------
# 3. Servidor (Server)
# ---------------------------------------------------------------------------
def server(input, output, session):
    @reactive.calc
    def dados_filtrados():
        ano_min, ano_max = input.faixa_anos()
        dff = df_ccen[
            (df_ccen["Ano Referencia"] >= ano_min)
            & (df_ccen["Ano Referencia"] <= ano_max)
        ]
        if input.curso() != "Todos":
            dff = dff[dff["Curso"] == input.curso()]
        if input.modalidade() != "Todas":
            dff = dff[dff["Modalidade"] == input.modalidade()]
        return dff

    @render_widget
    def grafico_scatter():
        df = dados_filtrados()
        cor = "Modalidade" if input.colorir_modalidade() else None
        fig = px.scatter(
            df,
            x="Qtde Estudantes",
            y="Qtde Concluintes",
            color=cor,
            hover_data=["Curso", "Ano Referencia", "Turno", "Qtde Abandono", "Taxa Abandono (%)"],
            labels={
                "Qtde Estudantes": "Quantidade de Estudantes",
                "Qtde Concluintes": "Quantidade de Concluintes",
                "Modalidade": "Modalidade",
            },
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(t=24, l=16, r=16, b=16),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        return fig

    @render_widget
    def grafico_boxplot():
        df = dados_filtrados()
        var = input.variavel()
        cor = "Modalidade" if input.colorir_modalidade() else None
        fig = px.box(
            df,
            x="Curso",
            y=var,
            color=cor,
            labels={
                "Curso": "Curso",
                var: VARIAVEIS_NUM[var],
            },
        )
        fig.update_layout(
            template="plotly_white",
            margin=dict(t=24, l=16, r=16, b=80),
            xaxis_tickangle=-25,
        )
        return fig

    @render.data_frame
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
        return render.DataGrid(pd.DataFrame(linhas), width="100%")


app = App(app_ui, server)