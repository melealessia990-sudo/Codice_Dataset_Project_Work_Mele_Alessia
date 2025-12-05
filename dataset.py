import numpy as np
import pandas as pd
import plotly.graph_objects as go

# IMPOSTAZIONI INIZIALI

np.random.seed(42)
start_date = "2025-01-01"
end_date = "2025-12-31"
days = pd.date_range(start=start_date, end=end_date, freq="D")
n = len(days)

# Generazione dati
temperature = 22 + 10 * np.pi * (np.arange(n)/365)+ np.random.normal(0, 2, n) # temperatura media giornaliera

humidity = 75 - (temperature - 22) * 0.8 + np.random.normal(0, 5, n)# umidità relativa - maggiore se fa piu freddo
humidity = np.clip(humidity, 30, 100)

rainfall = np.random.gamma(shape=2, scale=2, size=n)
rainfall[np.random.rand(n) < 0.7] =0

day_of_year = np.arange(1, n+1)
harvest_peak = 135
harvest_sigma = 30

base_yield = 200 * np.exp(-0.5 * ((day_of_year - harvest_peak) / harvest_sigma) **2)

yield_factor = 1 + 0.02 * (temperature - 12) + 0.01 * (humidity -75) /10
yield_kg = base_yield * yield_factor + np.random.normal( 0, 5, n)
yield_kg = np.clip(yield_kg, 0, 250)


price_per_kg = 4.5 + np.random.normal(0, 0.2, n) - 0.002 *(yield_kg - 100)
price_per_kg = np.clip(price_per_kg, 3.5, 5.5)

cost_per_kg = np.random.normal(1.9, 0.1, n)
cost_per_kg = np.clip(cost_per_kg, 1.5, 2.3)

revenue = yield_kg * price_per_kg
costs = yield_kg * cost_per_kg
profit = revenue - costs

qualita_media = (
    8
    - 0.05 * np.abs(temperature - 18)
    - 0.03 * np.abs(humidity - 70)
    - 0.001 * np.maximum(rainfall - 10, 0)
    + np.random.normal(0, 0.3, n)
)
qualita_media = np.clip(qualita_media, 0, 10)

indice_soddisfazione = qualita_media * 10 + np.random.normal(0, 5, n)
indice_soddisfazione = np.clip(indice_soddisfazione, 0, 100)

margine_percentuale = np.where(revenue > 0, profit / revenue, 0)
margine_percentuale = np.clip(margine_percentuale, 0,1)

indice_efficienza = (
    0.6 *(margine_percentuale / np.max(margine_percentuale)) * 100
    + 0.4 * (yield_kg / np.max(yield_kg)) * 100

)

indice_efficienza = np.clip(indice_efficienza, 0, 100)
# Creazione del DataFrame

df = pd.DataFrame({
    "Data": days,
    "Temperatura_C": temperature.round(1),
    "Umidita_%": humidity.round(1),
    "Pioggia_mm": rainfall.round(1),
    "Resa_kg" : yield_kg.round(1),
    "Prezzo_euro/kg": price_per_kg.round(2),
    "Costo_euro/kg": cost_per_kg.round(2),
    "Ricavo_euro": revenue.round(2),
    "Costo_tot": costs.round(2),
    "Profitto_euro": profit.round(2),
    "Qualità_media": qualita_media.round(2),
    "Indice_soddisfazione": indice_soddisfazione.round(1),
    "Margine_%": margine_percentuale.round(2),
    "Indice_efficienza": indice_efficienza.round(1)

})


filename = "dataset_projectwork.csv"
df.to_csv(filename, index=False)
print(f"File salvato: {filename}")
print (df.head())


# Creiamo la figura
fig = go.Figure()

# Aggiungiamo la temperatura
fig.add_trace(go.Scatter(
    x=df["Data"],
    y=df["Temperatura_C"],
    mode="lines",
    name="Temperatura (C°)",
    line=dict(color="red")
))

# Aggiungiamo la resa giornaliera
fig.add_trace(go.Scatter(
    x=df["Data"],
    y=df["Resa_kg"],
    mode="lines",
    name="Resa giornaliera (kg)",
    line=dict(color="green")
))

# Aggiungiamo l'umidità
fig.add_trace(go.Scatter(
    x=df["Data"],
    y=df["Umidita_%"],
    mode="lines",
    name="Umidità relativa (%)",
    line=dict(color="blue")
))

# Aggiungiamo la pioggia
fig.add_trace(go.Scatter(
    x=df["Data"],
    y=df["Pioggia_mm"],
    mode="lines",
    name="Pioggia (mm)",
    line=dict(color="purple")
))

# Impostiamo il layout
fig.update_layout(
    title="Andamento metereologico e resa dei mirtilli (2025)",
    xaxis_title="Data",
    yaxis_title="Valori",
    template="plotly_white",
    legend=dict(x=0.01, y=0.99),
    width=1000,
    height=500
)

fig.show()


df["month"] = df["Data"].dt.to_period("M").astype(str)
monthly = df.groupby("month").agg({
    "Ricavo_euro": "sum",
    "Costo_tot": "sum",
    "Profitto_euro": "sum",
    "Margine_%": "mean"
}).reset_index()

fig = go.Figure()

fig.add_trace(go.Bar(
    x=monthly["month"],
    y=monthly ["Ricavo_euro"],
    name="Ricavi totali",
    hovertemplate="%{y:, .0f} €<extra></extra>"
))

fig.add_trace(go.Bar(
    x=monthly["month"],
    y=monthly ["Costo_tot"],
    name="Costi totali",
    hovertemplate="%{y:, .0f} €<extra></extra>"
))

fig.add_trace(go.Bar(
    x=monthly["month"],
    y=monthly ["Profitto_euro"],
    name="Profitto totale",
    hovertemplate="%{y:, .0f} €<extra></extra>"
))

fig.add_trace(go.Scatter(
    x=monthly["month"],
    y=monthly ["Margine_%"],
    name="Margine medio (%)",
    mode="lines+markers",
    yaxis="y2",
    hovertemplate="%{y:.2%}<extra></extra>" # Changed to percentage format
))

fig.update_layout(
    title="Indicatori economici mensili - Ricavi / Costi / Profitto e Margine%",
    xaxis=dict(title="Mese"),
    yaxis=dict(title="Valori (€)"), # Corrected 'tile' to 'title'
    yaxis2= dict (
        title="Margine medio (%)",
        overlaying="y",
        side="right",
        showgrid=False
    ),
    barmode="group",
    legend=dict(x=0.01, y=0.99),
    template="plotly_white",
    margin=dict(t=80, b=40)
)

fig.show() 

df.to_csv("dataset.csv", index=False
            )