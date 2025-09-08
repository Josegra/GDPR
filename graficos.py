import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Definir subcategorías
priv_cols = ["Individual", "Director", "UBO", "Customer", "Representative", "Guarantor", "Unknown"]
corp_cols = ["SUPPLIER", "Shareholder", "Remarketing Dealer", "CUS_CORPORATE"]

# Crear subplots: 2 filas (Private arriba, Corporate abajo)
fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True,
    subplot_titles=("Private – subcategorías", "Corporate – subcategorías")
)

# --- Private subcats
for c in priv_cols:
    fig.add_trace(
        go.Scatter(
            x=df["date"], y=df[c],
            mode="lines+markers",
            name=c,
            line=dict(width=2),
            marker=dict(size=5)
        ),
        row=1, col=1
    )
# Total Private resaltado
fig.add_trace(
    go.Scatter(
        x=df["date"], y=df["Private"],
        mode="lines+markers",
        name="Private total",
        line=dict(width=4, color="royalblue"),
        marker=dict(size=7, color="royalblue")
    ),
    row=1, col=1
)

# --- Corporate subcats
for c in corp_cols:
    fig.add_trace(
        go.Scatter(
            x=df["date"], y=df[c],
            mode="lines+markers",
            name=c,
            line=dict(width=2),
            marker=dict(size=5)
        ),
        row=2, col=1
    )
# Total Corporate resaltado
fig.add_trace(
    go.Scatter(
        x=df["date"], y=df["Corporate"],
        mode="lines+markers",
        name="Corporate total",
        line=dict(width=4, color="black"),
        marker=dict(size=7, color="black")
    ),
    row=2, col=1
)

# Layout
fig.update_layout(
    height=700, width=1000,
    title="Evolución diaria de subcategorías – Private (arriba) y Corporate (abajo)",
    template="plotly_white",
    hovermode="x unified",
    xaxis2=dict(title="Fecha"),
    yaxis_title="Valor"
)

fig.show()
