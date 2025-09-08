import numpy as np
import pandas as pd
import plotly.graph_objects as go

# -----------------------------
# 1) Simulación de datos (~2 meses)
# -----------------------------
np.random.seed(42)
dates = pd.date_range("2025-07-01", periods=60, freq="D")

def smooth_series(base, size, amp=0.08, noise=0.03, period=14, phase=None):
    t = np.arange(size)
    if phase is None:
        phase = np.random.uniform(0, 2*np.pi)
    y = base * (1 + amp*np.sin(2*np.pi*t/period + phase) + noise*np.random.randn(size))
    return np.clip(y, 1, None).round().astype(int)

# Subcategorías
corp_cols = ["SUPPLIER", "Shareholder", "Remarketing Dealer", "CUS_CORPORATE"]
priv_cols = ["Individual", "Director", "UBO", "Customer", "Representative", "Guarantor", "Unknown"]

data = {"date": dates}
# Corporate
bases_c = dict(SUPPLIER=1800, Shareholder=140, Remarketing_Dealer=320, CUS_CORPORATE=720)
for k, base in bases_c.items():
    data[k] = smooth_series(base, len(dates))

# Private
bases_p = dict(Individual=2200, Director=650, UBO=600, Customer=550, Representative=500, Guarantor=80, Unknown=40)
for k, base in bases_p.items():
    data[k] = smooth_series(base, len(dates))

df = pd.DataFrame(data)

# Totales
df["Corporate"] = df[[c.replace(" ", "_") if " " in c else c for c in corp_cols]].sum(axis=1)
df["Private"]   = df[priv_cols].sum(axis=1)

# -----------------------------
# 2) Colores
# -----------------------------
colors = {
    # Totales
    "Corporate": "#111111",
    "Private":   "#1f77b4",
    # Corporate subcats
    "SUPPLIER": "#e41a1c",
    "Shareholder": "#377eb8",
    "Remarketing Dealer": "#4daf4a",
    "CUS_CORPORATE": "#984ea3",
    # Private subcats
    "Individual": "#ff7f00",
    "Director": "#a65628",
    "UBO": "#f781bf",
    "Customer": "#999999",
    "Representative": "#66c2a5",
    "Guarantor": "#8da0cb",
    "Unknown": "#e78ac3",
}

# -----------------------------
# 3) Figura: barras agrupadas + botones (Totales / Subcategorías / Todo)
# -----------------------------
fig = go.Figure()

# Orden de trazas: primero TOTales, luego subcategorías Corporate y Private
order = ["Corporate", "Private"] + corp_cols + priv_cols

for name in order:
    fig.add_trace(go.Bar(
        x=df["date"],
        y=df[name],
        name=name,
        marker_color=colors[name],
        visible=True if name in ["Corporate", "Private"] else "legendonly",  # por defecto solo totales
        hovertemplate="<b>%{fullData.name}</b><br>Fecha: %{x|%d/%m/%Y}<br>Valor: %{y:,}<extra></extra>",
    ))

def vis_mask(mode="totals"):
    """Devuelve una lista de visibilidad para las trazas en 'order'."""
    if mode == "totals":
        return [True if n in ["Corporate", "Private"] else False for n in order]
    if mode == "subcats":
        return [False if n in ["Corporate", "Private"] else True for n in order]
    # "all"
    return [True] * len(order)

fig.update_layout(
    barmode="group",
    title="Totales y subcategorías por fecha (Corporate & Private)",
    xaxis_title="Fecha",
    yaxis_title="Valor",
    template="plotly_white",
    xaxis=dict(type="date", tickformat="%d/%m/%Y", rangeslider=dict(visible=True)),
    legend_title_text="Serie",
    margin=dict(l=60, r=30, t=60, b=60),
    updatemenus=[dict(
        type="buttons",
        direction="right",
        x=0.5, xanchor="center",
        y=1.12, yanchor="top",
        buttons=[
            dict(label="Totales", method="update", args=[{"visible": vis_mask("totals")}]),
            dict(label="Subcategorías", method="update", args=[{"visible": vis_mask("subcats")}]),
            dict(label="Todo", method="update", args=[{"visible": vis_mask("all")}]),
        ]
    )]
)

fig.show()
