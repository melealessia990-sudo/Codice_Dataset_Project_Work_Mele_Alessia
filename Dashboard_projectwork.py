from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

# =========================
# CARICAMENTO E PULIZIA DATASET
# =========================

# Legge il dataset CSV dei mirtilli
""" DataFrame contenente tutti i dati raccolti dal progetto, con colonne su:
    - Data
    - Ricavo_euro
    - Costo_tot
    - Profitto_euro
    - Qualità_media
    - Indice_soddisfazione
    - Temperatura_C
    - Umidita_%
    - Pioggia_mm
"""

df = pd.read_csv("dataset_projectwork.csv", encoding="utf-8")


# Conversione della colonna 'Data' in formato datetime
""" Convertiamo la colonna 'Data' in datetime; eventuali valori non validi diventano NaT """
df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

# Controllo valori non validi
if df["Data"].isna().any():
    print("Attenzione: alcune date non sono valide e saranno rimosse")
    print(df[df["Data"].isna()])


# Creazione colonne utili per analisi mensile e trimestrale
df["mese"] = df["Data"].dt.to_period("M").astype(str)
df["trimestre"] = df["Data"].dt.quarter

print(df.head())

# =========================
# INIZIALIZZAZIONE APP
# =========================

# Creazione dell'applicazione Dash
""" Oggetto Dash principale che gestisce layout e callback """
app = Dash(__name__)
app.config.suppress_callback_exceptions = True
app.title = "Dashboard Mirtilli"

# =========================
# LAYOUT PRINCIPALE
# =========================
app.layout = html.Div([
    html.H1("Dashboard Azienda Agricola di Mirtilli",
            style={"textAlign": "center", "marginBottom": "30px"}),

    dcc.Tabs(
        id="sezione",
        value="economica",
        children=[
            dcc.Tab(label="Analisi Economica", value="economica"),
            dcc.Tab(label="Analisi Ambientale", value="ambientale"),
            dcc.Tab(label="Profitto vs Ambiente", value="profitto_ambiente")
        ]
    ),

    html.Br(),

    html.Label("Seleziona il periodo"),
    dcc.Dropdown(
        id="filtro_periodo",
        options=[
            {"label": "Tutto l'anno", "value": "all"},
            {"label": "1° Trimestre", "value": 1},
            {"label": "2° Trimestre", "value": 2},
            {"label": "3° Trimestre", "value": 3},
            {"label": "4° Trimestre", "value": 4}
        ],
        value="all",
        clearable=False,
        style={"width": "50%"}
    ),

    html.Br(),

    html.Label("Seleziona il tipo di analisi"),
    dcc.Dropdown(
        id="tipo_analisi",        
        value=None,
        clearable=False,
        style={"width": "50%"}
    ),

    html.Br(),

    html.Div(id="kpi_box", style={
        "display": "flex",
        "justifyContent": "space-around",
        "flexWrap": "wrap",
        "gap": "20px"
    }),

    html.Br(),

    dcc.Graph(id="grafico_mirtilli"),
    html.Div(id="descrizione", style={
        "marginTop": "20px",
        "textAlign": "center",
        "color": "black",
        "fontWeight": "bold"
    })
],style={"padding": "20px", "backgroundColor": "white", "fontFamily": "Arial, sans-serif"})
 


# =======================================================
# CALLBACK 1: AGGIORNA DROPDOWN TIPO_ANALISI
# =======================================================
@app.callback(
    Output("tipo_analisi", "options"),
    Output("tipo_analisi", "value"),
    Input("sezione", "value")
)
def aggiorna_dropdown(sezione):
    """
    Aggiorna le opzioni del dropdown 'tipo_analisi' in base alla sezione selezionata.
    
    Parametri:
    - sezione (str): può essere 'economica', 'ambientale' o 'profitto_ambiente'
    
    Ritorna:
    - options (list): lista di dizionari {'label': str, 'value': str} da mostrare nel dropdown
    - default (str): valore di default selezionato nel dropdown
    """
    if sezione == "economica":  #SEZIONE ECONOMICA
        options = [
            {"label": "Ricavi mensili (€)", "value": "ricavo"},
            {"label": "Costi mensili (€)", "value": "costo"},
            {"label": "Profitto mensile (€)", "value": "profitto"},
            {"label": "Qualità media (0-10)", "value": "qualita"},
            {"label": "Indice soddisfazione (0-100)", "value": "soddisfazione"}
        ]
        default = "ricavo"

    elif sezione == "ambientale":    #SEZIONE AMBIENTALE
        options = [
            {"label": "Temperatura media (°C)", "value": "temperatura"},
            {"label": "Umidità media (%)", "value": "umidita"},
            {"label": "Pioggia totale (mm)", "value": "pioggia"}
        ]
        default = "temperatura"

    else:  #PROFITTO vs AMBIENTE
        options = [
            {"label": "Temperatura vs Profitto", "value": "temperatura"},
            {"label": "Umidità vs Profitto", "value": "umidita"},
            {"label": "Pioggia vs Profitto", "value": "pioggia"}
        ]
        default = "temperatura"

    return options, default


# =======================================================
# CALLBACK 2: AGGIORNA GRAFICO + KPI
# =======================================================
@app.callback(
    [Output("grafico_mirtilli", "figure"),
     Output("descrizione", "children"),
     Output("kpi_box", "children")],
    [Input("tipo_analisi", "value"),
     Input("filtro_periodo", "value"),
     Input("sezione", "value"),]
)
def aggiorna_dashboard(tipo_analisi, filtro_periodo, sezione):
    """
    Aggiorna grafico e KPI in base al tipo di analisi, periodo e sezione selezionata.
    
    Parametri:
    - tipo_analisi (str): tipo di dato da visualizzare (es. 'ricavo', 'temperatura')
    - filtro_periodo (str/int): filtro per trimestre o 'all'
    - sezione (str): sezione selezionata ('economica', 'ambientale', 'profitto_ambiente')
    
    Ritorna:
    - figure: grafico Plotly aggiornato
    - descrizione (str): titolo o descrizione del grafico
    - kpi_box (list): lista di Div contenenti i KPI principali
    """
    if tipo_analisi is None:
        return {}, "", []

    # Filtro dati per periodo selezionato
    df_filtrato = df if filtro_periodo == "all" else df[df["trimestre"] == int(filtro_periodo)]

    if df_filtrato.empty:
        return {}, "Nessun dato disponibile per questo periodo", []

    # ================= ECONOMICA =================
    if sezione == "economica":
        # Calcolo KPI economici
        ricavi = df_filtrato["Ricavo_euro"].sum()
        costi = df_filtrato["Costo_tot"].sum()
        profitto = df_filtrato["Profitto_euro"].sum()
        qualita = df_filtrato["Qualità_media"].mean()
        soddisfazione = df_filtrato["Indice_soddisfazione"].mean()

        # Layout KPI
        kpi_layout = [
            html.Div([html.H3("Ricavi Totali"), html.H2(f"{ricavi:,.0f} €")]),
            html.Div([html.H3("Costi Totali"), html.H2(f"{costi:,.0f} €")]),
            html.Div([html.H3("Profitto Totale"), html.H2(f"{profitto:,.0f} €")]),
            html.Div([html.H3("Qualità Media"), html.H2(f"{qualita:.2f}")]),
            html.Div([html.H3("Soddisfazione Media"), html.H2(f"{soddisfazione:.2f}")])
        ]

        # Mapping colonna-grafico
        mapping = {
            "ricavo": ("Ricavo_euro", "Ricavi mensili (€)"),
            "costo": ("Costo_tot", "Costi mensili (€)"),
            "profitto": ("Profitto_euro", "Profitto mensile (€)"),
            "qualita": ("Qualità_media", "Qualità media"),
            "soddisfazione": ("Indice_soddisfazione", "Soddisfazione clienti")
        }
        colonna, titolo = mapping[tipo_analisi]

        # Line chart
        dati = df_filtrato.groupby("mese")[colonna].mean().reset_index()
        dati = dati.sort_values("mese")
        fig = px.line(dati, x="mese", y=colonna, markers=True, title=titolo)
        fig.update_layout(template="plotly_white", font_color="black")
        return fig, titolo, kpi_layout

    # ================= AMBIENTALE =================
    elif sezione == "ambientale":
        # Calcolo KPI ambientali
        temperatura = df_filtrato["Temperatura_C"].mean()
        umidita = df_filtrato["Umidita_%"].mean()
        pioggia = df_filtrato["Pioggia_mm"].sum()

        kpi_layout = [
            html.Div([html.H3("Temperatura Media"), html.H2(f"{temperatura:.1f} °C")]),
            html.Div([html.H3("Umidità Media"), html.H2(f"{umidita:.1f} %")]),
            html.Div([html.H3("Pioggia Totale"), html.H2(f"{pioggia:.1f} mm")])
        ]

        # Mapping colonna-grafico
        mapping_env = {
            "temperatura": ("Temperatura_C", "Temperatura media mensile"),
            "umidita": ("Umidita_%", "Umidità media mensile"),
            "pioggia": ("Pioggia_mm", "Pioggia totale mensile")
        }
        colonna, titolo = mapping_env[tipo_analisi]

        # Line chart
        dati = df_filtrato.groupby("mese")[colonna].mean().reset_index()
        dati = dati.sort_values("mese")
        fig = px.line(dati, x="mese", y=colonna, markers=True, title=titolo)
        fig.update_layout(template="plotly_white", font_color="black")
        return fig, titolo, kpi_layout

    # ================= PROFITTO vs AMBIENTE =================
    else:
        mapping_pa = {
            "temperatura": ("Temperatura_C", "Profitto vs Temperatura"),
            "umidita": ("Umidita_%", "Profitto vs Umidità"),
            "pioggia": ("Pioggia_mm", "Profitto vs Pioggia")
        }
        xcol, titolo_amb = mapping_pa[tipo_analisi]
        ycol = "Profitto_euro"

        # Scatter plot con trendline OLS
        fig = px.scatter(
            df_filtrato,
            x=xcol,
            y=ycol,
            size=ycol,
            color=ycol,
            color_continuous_scale="Viridis",
            trendline="ols",
            trendline_color_override="red",
            title=titolo_amb,
            labels={xcol: xcol, ycol: "Profitto (€)"},
            hover_data=["mese", xcol, ycol]
        )

        fig.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color="DarkSlateGrey")))
        fig.update_layout(template="plotly_white", font_color="black")

        kpi_layout = [
            html.Div([html.H3("Profitto Totale"), html.H2(f"{df_filtrato[ycol].sum():,.0f} €")]),
            html.Div([html.H3(f"{xcol} Medio"), html.H2(f"{df_filtrato[xcol].mean():.2f}")])
        ]

        return fig, titolo_amb, kpi_layout


# =========================
# AVVIO SERVER
# =========================
if __name__ == "__main__":
    """Avvia il server Dash """
    app.run(debug=True, port=8060)
