import numpy as np
import pandas as pd

np.random.seed(42)
dates = pd.date_range("2025-07-01", periods=60, freq="D")

def smooth_series(base, size, amp=0.08, noise=0.03, period=14):
    t = np.arange(size)
    phase = np.random.uniform(0, 2*np.pi)
    y = base * (1 + amp*np.sin(2*np.pi*t/period + phase) + noise*np.random.randn(size))
    return np.clip(y, 1, None).round().astype(int)

df = pd.DataFrame({
    "date": dates,
    "Corporate": smooth_series(1500, len(dates)),
    "Private": smooth_series(1400, len(dates)),
    "Datacap": smooth_series(1200, len(dates)),
    "Third parties": smooth_series(1000, len(dates)),
})

import plotly.graph_objects as go

fig1 = go.Figure()

colors = {"Corporate":"#111111", "Private":"#1f77b4", "Datacap":"#e41a1c", "Third parties":"#4daf4a"}

for c in ["Corporate","Private","Datacap","Third parties"]:
    fig1.add_trace(go.Scatter(
        x=df["date"], y=df[c], name=c,
        mode="lines+markers", line=dict(width=3, color=colors[c])
    ))

fig1.update_layout(
    title="Evolución diaria por categoría",
    xaxis_title="Fecha", yaxis_title="Valor",
    hovermode="x unified", template="plotly_white",
    xaxis=dict(type="date", rangeslider=dict(visible=True))
)

fig1.show()


fig2 = go.Figure()

for c in ["Corporate","Private","Datacap","Third parties"]:
    fig2.add_trace(go.Bar(x=df["date"], y=df[c], name=c, marker_color=colors[c]))

fig2.update_layout(
    title="Totales diarios por categoría",
    barmode="group",
    xaxis_title="Fecha", yaxis_title="Valor",
    template="plotly_white",
    xaxis=dict(type="date", rangeslider=dict(visible=True))
)

fig2.show()

fig3 = go.Figure()

for c in ["Corporate","Private","Datacap","Third parties"]:
    fig3.add_trace(go.Bar(x=df["date"], y=df[c], name=c, marker_color=colors[c]))

fig3.update_layout(
    title="Participación por categoría (apilado)",
    barmode="stack",
    xaxis_title="Fecha", yaxis_title="Valor",
    template="plotly_white",
    xaxis=dict(type="date")
)

fig3.show()


deltas = df.copy()
for c in ["Corporate","Private","Datacap","Third parties"]:
    deltas[c] = deltas[c].diff()

fig4 = go.Figure()
for c in ["Corporate","Private","Datacap","Third parties"]:
    fig4.add_trace(go.Bar(x=deltas["date"], y=deltas[c], name=f"Δ {c}", marker_color=colors[c]))

fig4.update_layout(
    title="Variación diaria (Δ vs día anterior)",
    barmode="group",
    xaxis_title="Fecha", yaxis_title="Δ",
    template="plotly_white", xaxis=dict(type="date")
)
fig4.add_hline(y=0, line_width=1, line_color="black")

fig4.show()


import plotly.express as px

heat = deltas.set_index("date")[["Corporate","Private","Datacap","Third parties"]].T
fig5 = px.imshow(
    heat, aspect="auto", origin="lower", 
    color_continuous_scale="RdYlGn", 
    title="Mapa de calor – variaciones diarias",
    labels=dict(x="Fecha", y="Categoría", color="Δ diario")
)
fig5.update_layout(template="plotly_white")
fig5.show()


from plotly.subplots import make_subplots
import plotly.graph_objects as go

fig_line = make_subplots(
    rows=1, cols=2, shared_yaxes=True,
    subplot_titles=("Corporate vs Private", "Datacap vs Third parties")
)

# --- Corporate & Private
for c, col in zip(["Corporate","Private"], ["#111111","#1f77b4"]):
    fig_line.add_trace(
        go.Scatter(x=df["date"], y=df[c], name=c, mode="lines+markers", line=dict(width=3, color=col)),
        row=1, col=1
    )

# --- Datacap & Third parties
for c, col in zip(["Datacap","Third parties"], ["#e41a1c","#4daf4a"]):
    fig_line.add_trace(
        go.Scatter(x=df["date"], y=df[c], name=c, mode="lines+markers", line=dict(width=3, color=col)),
        row=1, col=2
    )

fig_line.update_layout(
    height=500, width=1200,
    title="Evolución diaria – Comparación lado a lado",
    template="plotly_white", hovermode="x unified"
)
fig_line.show()


fig_bar = make_subplots(
    rows=1, cols=2, shared_yaxes=True,
    subplot_titles=("Corporate vs Private", "Datacap vs Third parties")
)

fig_bar.add_trace(go.Bar(x=df["date"], y=df["Corporate"], name="Corporate", marker_color="#111111"), row=1,col=1)
fig_bar.add_trace(go.Bar(x=df["date"], y=df["Private"], name="Private", marker_color="#1f77b4"), row=1,col=1)

fig_bar.add_trace(go.Bar(x=df["date"], y=df["Datacap"], name="Datacap", marker_color="#e41a1c"), row=1,col=2)
fig_bar.add_trace(go.Bar(x=df["date"], y=df["Third parties"], name="Third parties", marker_color="#4daf4a"), row=1,col=2)

fig_bar.update_layout(
    barmode="group",
    height=500, width=1200,
    title="Totales diarios – Barras agrupadas lado a lado",
    template="plotly_white"
)
fig_bar.show()


deltas = df.copy()
for c in ["Corporate","Private","Datacap","Third parties"]:
    deltas[c] = deltas[c].diff()

fig_delta = make_subplots(
    rows=1, cols=2, shared_yaxes=True,
    subplot_titles=("Δ Corporate vs Private", "Δ Datacap vs Third parties")
)

fig_delta.add_trace(go.Bar(x=deltas["date"], y=deltas["Corporate"], name="Δ Corporate", marker_color="#111111"), row=1,col=1)
fig_delta.add_trace(go.Bar(x=deltas["date"], y=deltas["Private"], name="Δ Private", marker_color="#1f77b4"), row=1,col=1)

fig_delta.add_trace(go.Bar(x=deltas["date"], y=deltas["Datacap"], name="Δ Datacap", marker_color="#e41a1c"), row=1,col=2)
fig_delta.add_trace(go.Bar(x=deltas["date"], y=deltas["Third parties"], name="Δ Third parties", marker_color="#4daf4a"), row=1,col=2)

fig_delta.update_layout(
    barmode="group",
    height=500, width=1200,
    title="Variación diaria (Δ) – lado a lado",
    template="plotly_white"
)
fig_delta.add_hline(y=0, line_color="black", line_width=1)
fig_delta.show()


fig_area = make_subplots(
    rows=1, cols=2, shared_yaxes=True,
    subplot_titles=("Corporate vs Private", "Datacap vs Third parties")
)

fig_area.add_trace(go.Scatter(x=df["date"], y=df["Corporate"], name="Corporate", stackgroup="one", line=dict(color="#111111")), row=1,col=1)
fig_area.add_trace(go.Scatter(x=df["date"], y=df["Private"], name="Private", stackgroup="one", line=dict(color="#1f77b4")), row=1,col=1)

fig_area.add_trace(go.Scatter(x=df["date"], y=df["Datacap"], name="Datacap", stackgroup="two", line=dict(color="#e41a1c")), row=1,col=2)
fig_area.add_trace(go.Scatter(x=df["date"], y=df["Third parties"], name="Third parties", stackgroup="two", line=dict(color="#4daf4a")), row=1,col=2)

fig_area.update_layout(
    height=500, width=1200,
    title="Participación relativa – Áreas apiladas lado a lado",
    template="plotly_white", hovermode="x unified"
)
fig_area.show()

