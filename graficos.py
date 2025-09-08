import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Subcategorías
priv_cols = ["Individual", "Director", "UBO", "Customer", "Representative", "Guarantor", "Unknown"]
corp_cols = ["SUPPLIER", "Shareholder", "Remarketing Dealer", "CUS_CORPORATE"]

# Crear subplots: 1 fila, 2 columnas
fig = make_subplots(
    rows=1, cols=2, shared_yaxes=True,
    subplot_titles=("Private – subcategorías", "Corporate – subcategorías")
)

# --- Private (col=1)
for c in priv_cols:
    fig.add_trace(
        go.Scatter(
            x=df["date"], y=df[c],
            mode="lines+markers", name=c,
            line=dict(width=2), marker=dict(size=5)
        ),
        row=1, col=1
    )
# Total Private
fig.add_trace(
    go.Scatter(
        x=df["date"], y=df["Private"],
        mode="lines+markers", name="Private total",
        line=dict(width=4, color="royalblue"), marker=dict(size=7, color="royalblue")
    ),
    row=1, col=1
)

# --- Corporate (col=2)
for c in corp_cols:
    fig.add_trace(
        go.Scatter(
            x=df["date"], y=df[c],
            mode="lines+markers", name=c,
            line=dict(width=2), marker=dict(size=5)
        ),
        row=1, col=2
    )
# Total Corporate
fig.add_trace(
    go.Scatter(
        x=df["date"], y=df["Corporate"],
        mode="lines+markers", name="Corporate total",
        line=dict(width=4, color="black"), marker=dict(size=7, color="black")
    ),
    row=1, col=2
)

# Layout
fig.update_layout(
    height=500, width=1200,
    title="Evolución diaria de subcategorías – Private (izquierda) vs Corporate (derecha)",
    template="plotly_white",
    hovermode="x unified",
    xaxis_title="Fecha", xaxis2_title="Fecha",
    yaxis_title="Valor"
)

fig.show()
