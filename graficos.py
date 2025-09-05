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












import plotly.express as px

fig = px.area(
    df,
    x="date",
    y=["Law", "Business", "Tech", "Biotech"],
    title="Evolución diaria: Subcategorías apiladas",
    labels={"value": "KPI diario", "date": "Fecha", "variable": "Subcategoría"},
)

fig.update_layout(template="plotly_white")
fig.show()






# Calcular variaciones
df_deltas = df[['date','Corporate','Private','Law','Business','Tech','Biotech']].copy()
for col in ['Corporate','Private','Law','Business','Tech','Biotech']:
    df_deltas[col] = df_deltas[col].diff()

fig = px.bar(
    df_deltas.melt(id_vars="date", var_name="Serie", value_name="Delta"),
    x="date", y="Delta", color="Serie",
    title="Variación diaria por categoría y subcategoría",
    barmode="group"
)
fig.update_layout(template="plotly_white")
fig.show()




import plotly.express as px

df_deltas = df[['date','Corporate','Private','Law','Business','Tech','Biotech']].copy()
for col in ['Corporate','Private','Law','Business','Tech','Biotech']:
    df_deltas[col] = df_deltas[col].diff()

# Transformar a formato ancho
heatmap_data = df_deltas.set_index("date").T

fig = px.imshow(
    heatmap_data,
    aspect="auto",
    color_continuous_scale="RdYlGn",
    origin="lower",
    title="Mapa de calor de variaciones diarias",
    labels=dict(x="Fecha", y="Serie", color="Δ diario")
)
fig.update_layout(template="plotly_white")
fig.show()




from plotly.subplots import make_subplots
import plotly.graph_objects as go

fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    subplot_titles=("Corporate (Law + Business)", "Private (Tech + Biotech)"))

# Corporate
fig.add_trace(go.Scatter(x=df['date'], y=df['Law'], mode='lines', name='Law'), row=1, col=1)
fig.add_trace(go.Scatter(x=df['date'], y=df['Business'], mode='lines', name='Business'), row=1, col=1)
fig.add_trace(go.Scatter(x=df['date'], y=df['Corporate'], mode='lines+markers', name='Corporate total',
                         line=dict(width=3, color='black')), row=1, col=1)

# Private
fig.add_trace(go.Scatter(x=df['date'], y=df['Tech'], mode='lines', name='Tech'), row=2, col=1)
fig.add_trace(go.Scatter(x=df['date'], y=df['Biotech'], mode='lines', name='Biotech'), row=2, col=1)
fig.add_trace(go.Scatter(x=df['date'], y=df['Private'], mode='lines+markers', name='Private total',
                         line=dict(width=3, color='blue')), row=2, col=1)

fig.update_layout(
    height=600, width=900,
    title="Evolución separada: Corporate y Private con sus subcategorías",
    template="plotly_white"
)
fig.show()




fig = px.treemap(
    df.melt(id_vars="date", value_vars=["Law","Business","Tech","Biotech"],
            var_name="Subcategoría", value_name="KPI"),
    path=[px.Constant("Total"), "Subcategoría"],
    values="KPI",
    title="Treemap de participación relativa (ejemplo en una fecha)",
)

fig.update_traces(root_color="lightgrey")
fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
fig.show()





