# ============================================
# Simulated 2-month dataset + Plotly dashboards
# ============================================
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------
# 1) Create ~60 days of data
# -----------------------------
np.random.seed(42)
dates = pd.date_range("2025-07-01", periods=60, freq="D")

def smooth_series(base, size, amp=0.10, noise=0.04, period=14, phase=None):
    """Multiplicative sinusoidal trend + noise around a base level"""
    t = np.arange(size)
    if phase is None:
        phase = np.random.uniform(0, 2*np.pi)
    series = base * (1 + amp*np.sin(2*np.pi*t/period + phase) + noise*np.random.randn(size))
    series = np.clip(series, 1, None)
    return series.round().astype(int)

# Set bases so magnitudes are close (no single series dominates)
# --- Private subcategories
priv_bases = dict(
    Individual=2200, Director=650, UBO=600, Customer=550,
    Representative=500, Guarantor=80, Unknown=40
)
# --- Corporate subcategories
corp_bases = dict(
    SUPPLIER=1800, Shareholder=140, Remarketing_Dealer=320, CUS_CORPORATE=720
)

# Generate series
data = {"date": dates}
for k, base in {**priv_bases, **corp_bases}.items():
    data[k] = smooth_series(base, len(dates))

df = pd.DataFrame(data)

# Totals
private_cols = list(priv_bases.keys())
corporate_cols = list(corp_bases.keys())
df["Private"] = df[private_cols].sum(axis=1)
df["Corporate"] = df[corporate_cols].sum(axis=1)

# -----------------------------
# 2) Color palette (distinct)
# -----------------------------
colors = {
    # Totals
    "Corporate": "#111111",
    "Private":   "#1f77b4",
    # Corporate subcats
    "SUPPLIER": "#e41a1c",
    "Shareholder": "#377eb8",
    "Remarketing_Dealer": "#4daf4a",
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

# ============================================
# A) Evolution lines: Corporate, Private & subcats (with buttons)
# ============================================
fig_main = go.Figure()
series_order = ["Corporate","Private"] + corporate_cols + private_cols

for name in series_order:
    fig_main.add_trace(go.Scatter(
        x=df["date"], y=df[name], name=name,
        mode="lines+markers",
        line=dict(width=2.5, color=colors[name]),
        marker=dict(size=5),
        visible=True if name in ["Corporate","Private"] else "legendonly",
        hovertemplate="<b>%{fullData.name}</b><br>Fecha: %{x|%Y-%m-%d}<br>Valor: %{y:,}<extra></extra>",
    ))

def _vis(state="totals"):
    if state == "totals":
        return [name in ["Corporate","Private"] for name in series_order]
    if state == "subcats":
        return [name in corporate_cols+private_cols for name in series_order]
    return [True]*len(series_order)

fig_main.update_layout(
    title="Evolución diaria: Corporate, Private y subcategorías",
    xaxis_title="Fecha", yaxis_title="Valor",
    hovermode="x unified", template="plotly_white",
    xaxis=dict(rangeslider=dict(visible=True), type="date"),
    updatemenus=[dict(
        type="buttons", direction="right", x=0.5, xanchor="center", y=1.12, yanchor="top",
        buttons=[
            dict(label="Totales", method="update", args=[{"visible": _vis('totals') }]),
            dict(label="Subcategorías", method="update", args=[{"visible": _vis('subcats') }]),
            dict(label="Todo", method="update", args=[{"visible": _vis('all') }]),
        ]
    )],
    legend_title_text="Serie",
    margin=dict(l=60, r=30, t=60, b=60),
)
fig_main.show()

# ============================================
# B) Stacked AREA: Corporate subcats  /  Private subcats
# ============================================
def stacked_area(df, cols, title):
    fig = go.Figure()
    cum = np.zeros(len(df))
    for c in cols:
        fig.add_trace(go.Scatter(
            x=df["date"], y=df[c], name=c, stackgroup="one",
            mode="none", # area only
            hovertemplate=f"<b>{c}</b><br>%{{x|%Y-%m-%d}}<br>Valor: %{{y:,}}<extra></extra>",
            line=dict(color=colors[c])
        ))
    fig.update_layout(
        title=title, xaxis_title="Fecha", yaxis_title="Valor",
        template="plotly_white", hovermode="x unified",
        xaxis=dict(type="date")
    )
    return fig

fig_area_corp = stacked_area(df, corporate_cols, "Corporate – subcategorías (área apilada)")
fig_area_priv = stacked_area(df, private_cols, "Private – subcategorías (área apilada)")
fig_area_corp.show()
fig_area_priv.show()

# ============================================
# C) Day-to-day variation (Δ): totals + subcats
# ============================================
deltas = df[["date"] + series_order].copy()
for c in series_order:
    deltas[c] = deltas[c].diff()

# Totals
fig_delta_tot = go.Figure()
fig_delta_tot.add_trace(go.Bar(x=deltas["date"], y=deltas["Corporate"], name="Δ Corporate", marker_color=colors["Corporate"]))
fig_delta_tot.add_trace(go.Bar(x=deltas["date"], y=deltas["Private"], name="Δ Private", marker_color=colors["Private"]))
fig_delta_tot.update_layout(
    title="Variación diaria (Δ): Totales",
    xaxis_title="Fecha", yaxis_title="Δ vs. día anterior",
    template="plotly_white", barmode="group", xaxis=dict(type="date")
)
fig_delta_tot.add_hline(y=0, line_color="black", line_width=1)
fig_delta_tot.show()

# Corporate subcats Δ
fig_delta_c = go.Figure()
for c in corporate_cols:
    fig_delta_c.add_trace(go.Bar(x=deltas["date"], y=deltas[c], name=f"Δ {c}", marker_color=colors[c]))
fig_delta_c.update_layout(
    title="Variación diaria (Δ): Corporate subcategorías",
    xaxis_title="Fecha", yaxis_title="Δ vs. día anterior",
    template="plotly_white", barmode="group", xaxis=dict(type="date")
)
fig_delta_c.add_hline(y=0, line_color="black", line_width=1)
fig_delta_c.show()

# Private subcats Δ
fig_delta_p = go.Figure()
for c in private_cols:
    fig_delta_p.add_trace(go.Bar(x=deltas["date"], y=deltas[c], name=f"Δ {c}", marker_color=colors[c]))
fig_delta_p.update_layout(
    title="Variación diaria (Δ): Private subcategorías",
    xaxis_title="Fecha", yaxis_title="Δ vs. día anterior",
    template="plotly_white", barmode="group", xaxis=dict(type="date")
)
fig_delta_p.add_hline(y=0, line_color="black", line_width=1)
fig_delta_p.show()

# ============================================
# D) Heatmap of daily deltas (all series)
# ============================================
heat = deltas.set_index("date")[series_order].T  # rows=series, cols=days
fig_heat = px.imshow(
    heat, aspect="auto", origin="lower", color_continuous_scale="RdYlGn", 
    title="Mapa de calor – variaciones diarias (todas las series)",
    labels=dict(x="Fecha", y="Serie", color="Δ diario")
)
fig_heat.update_layout(template="plotly_white")
fig_heat.show()

# ============================================
# E) Two-panel subplot (Corporate vs Private): totals (thick) + subcats
# ============================================
fig_sub = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=("Corporate (total + subcategorías)", "Private (total + subcategorías)"))

# Corporate
for c in corporate_cols:
    fig_sub.add_trace(go.Scatter(x=df["date"], y=df[c], name=c, mode="lines",
                                 line=dict(width=1.8, color=colors[c])), row=1, col=1)
fig_sub.add_trace(go.Scatter(x=df["date"], y=df["Corporate"], name="Corporate total", mode="lines+markers",
                             line=dict(width=3.5, color=colors["Corporate"])), row=1, col=1)

# Private
for c in private_cols:
    fig_sub.add_trace(go.Scatter(x=df["date"], y=df[c], name=c, mode="lines",
                                 line=dict(width=1.8, color=colors[c])), row=2, col=1)
fig_sub.add_trace(go.Scatter(x=df["date"], y=df["Private"], name="Private total", mode="lines+markers",
                             line=dict(width=3.5, color=colors["Private"])), row=2, col=1)

fig_sub.update_layout(
    height=700, title="Corporate vs Private – totales y subcategorías",
    template="plotly_white", hovermode="x unified",
    xaxis2=dict(title="Fecha", type="date"), yaxis_title="Valor"
)
fig_sub.show()
