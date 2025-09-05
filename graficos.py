import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------
# EJEMPLO DE DATOS (quita esta parte si ya tienes tu DataFrame)
# -----------------------------
np.random.seed(7)
dates = pd.date_range('2025-08-07', periods=30, freq='D')
df = pd.DataFrame({
    'date': dates,
    'Law': np.random.randint(1200, 1800, size=30),
    'Business': np.random.randint(2500, 3400, size=30),
    'Tech': np.random.randint(900, 1400, size=30),
    'Biotech': np.random.randint(600, 1100, size=30),
})
# Totales por categoría principal
df['Corporate'] = df['Law'] + df['Business']
df['Private']   = df['Tech'] + df['Biotech']

# -----------------------------
# GRÁFICO PLOTLY
# -----------------------------
fig = go.Figure()

series = [
    ('Corporate', '#111111', True),   # (nombre, color, visible por defecto)
    ('Private',   '#1f77b4', True),
    ('Law',       '#2ca02c', False),
    ('Business',  '#bcbd22', False),
    ('Tech',      '#1f77b4', False),
    ('Biotech',   '#ff7f0e', False),
]

for name, color, visible in series:
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df[name],
            name=name,
            mode='lines+markers',
            line=dict(width=2, color=color),
            marker=dict(size=6),
            visible=True if visible else 'legendonly',
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "Fecha: %{x|%Y-%m-%d}<br>"
                "KPI: %{y:,}<extra></extra>"
            ),
        )
    )

# Layout
fig.update_layout(
    title="Evolución diaria: Corporate, Private y subcategorías",
    xaxis_title="Fecha",
    yaxis_title="KPI diario",
    hovermode="x unified",
    legend_title_text="Serie",
    template="plotly_white",
    xaxis=dict(rangeslider=dict(visible=True), type="date"),
    margin=dict(l=60, r=30, t=60, b=60)
)

# Botones para alternar vista (Totales / Subcategorías / Todo)
def _visibility(all_on=False, only_totals=False):
    if only_totals:
        # 2 primeras (Corporate, Private) visibles
        return [True, True, False, False, False, False]
    if all_on:
        return [True, True, True, True, True, True]
    # Vista por defecto: solo totales visibles, subcats en legendonly
    return [True, True, 'legendonly', 'legendonly', 'legendonly', 'legendonly']

fig.update_layout(
    updatemenus=[dict(
        type="buttons",
        direction="right",
        x=0.5, xanchor="center",
        y=1.12, yanchor="top",
        buttons=[
            dict(label="Totales",     method="update",
                 args=[{"visible": _visibility(only_totals=True)}]),
            dict(label="Subcategorías", method="update",
                 args=[{"visible": [False, False, True, True, True, True]}]),
            dict(label="Todo",        method="update",
                 args=[{"visible": _visibility(all_on=True)}]),
        ]
    )]
)

fig.show()
