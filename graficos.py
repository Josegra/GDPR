import pandas as pd
import plotly.graph_objects as go
from datetime import date

# -----------------------------
# Datos snapshot (un solo día)
# -----------------------------
private = {
    "Individual": 109736, "Director": 5580, "UBO": 4001, "Customer": 1327,
    "Representative": 784, "Guarantor": 18, "Unknown": 1
}
corporate = {
    "SUPPLIER": 5501, "Shareholder": 63, "Remarketing Dealer": 524, "CUS_CORPORATE": 995
}

snap_date = pd.to_datetime(date.today())  # usa la fecha de hoy; cambia si quieres

df = pd.DataFrame({
    "date": [snap_date],
    "Corporate": [sum(corporate.values())],
    "Private":   [sum(private.values())],
})

# Para permitir trazar también subcategorías en el mismo estilo
# (se añaden como "columnas" con el mismo valor en ese día)
for k, v in corporate.items():
    df[k] = v
for k, v in private.items():
    df[k] = v

# -----------------------------
# GRÁFICO PLOTLY (adaptación del tuyo)
# -----------------------------
fig = go.Figure()

series = [
    ("Corporate", "#111111", True),
    ("Private",   "#1f77b4", True),
    # Corporate subcats
    ("SUPPLIER", "rgba(0,0,0,0.6)", False),
    ("Shareholder", "rgba(0,0,0,0.6)", False),
    ("Remarketing Dealer", "rgba(0,0,0,0.6)", False),
    ("CUS_CORPORATE", "rgba(0,0,0,0.6)", False),
    # Private subcats
    ("Individual", "#2ca02c", False),
    ("Director",   "#2ca02c", False),
    ("UBO",        "#2ca02c", False),
    ("Customer",   "#2ca02c", False),
    ("Representative", "#2ca02c", False),
    ("Guarantor",  "#2ca02c", False),
    ("Unknown",    "#2ca02c", False),
]

for name, color, visible in series:
    fig.add_trace(
        go.Scatter(
            x=df["date"], y=df[name],
            name=name, mode="lines+markers",
            line=dict(width=3, color=color),
            marker=dict(size=9),
            visible=True if visible else "legendonly",
            hovertemplate="<b>%{fullData.name}</b><br>Fecha: %{x|%Y-%m-%d}<br>Valor: %{y:,}<extra></extra>",
        )
    )

fig.update_layout(
    title="Snapshot: Corporate, Private y subcategorías",
    xaxis_title="Fecha",
    yaxis_title="Conteo",
    hovermode="x unified",
    legend_title_text="Serie",
    template="plotly_white",
    xaxis=dict(type="date"),
    margin=dict(l=60, r=30, t=60, b=60),
)

def _visibility(all_on=False, only_totals=False):
    if only_totals:
        # Las dos primeras trazas son Corporate y Private
        mask = [True, True] + [False]*(len(series)-2)
        return mask
    if all_on:
        return [True]*len(series)
    # Por defecto: solo totales visibles
    return [True, True] + ["legendonly"]*(len(series)-2)

fig.update_layout(
    updatemenus=[dict(
        type="buttons", direction="right",
        x=0.5, xanchor="center", y=1.12, yanchor="top",
        buttons=[
            dict(label="Totales", method="update",
                 args=[{"visible": _visibility(only_totals=True)}]),
            dict(label="Subcategorías", method="update",
                 args=[{"visible": [False, False] + [True]*(len(series)-2)}]),
            dict(label="Todo", method="update",
                 args=[{"visible": _visibility(all_on=True)}]),
        ]
    )]
)

fig.show()



------------------------------------------------------------------------------------------------------------------------------------------------------------------
from plotly.subplots import make_subplots
import plotly.graph_objects as go

fig_donuts = make_subplots(
    rows=1, cols=2, specs=[[{"type":"domain"},{"type":"domain"}]],
    subplot_titles=[f"Private (n={sum(private.values()):,})", f"Corporate (n={sum(corporate.values()):,})"]
)

fig_donuts.add_trace(
    go.Pie(labels=list(private.keys()), values=list(private.values()),
           hole=0.55, name="Private",
           hovertemplate="<b>%{label}</b><br>Conteo: %{value:,}<br>% %{percent}<extra></extra>"),
    1, 1
)
fig_donuts.add_trace(
    go.Pie(labels=list(corporate.keys()), values=list(corporate.values()),
           hole=0.55, name="Corporate",
           hovertemplate="<b>%{label}</b><br>Conteo: %{value:,}<br>% %{percent}<extra></extra>"),
    1, 2
)

fig_donuts.update_traces(textinfo="percent+label")
fig_donuts.update_layout(title="Distribución por subcategorías: Private vs Corporate", template="plotly_white")
fig_donuts.show()

------------------------------------------------------------------------------------------------------------------------------------------------------------------
import plotly.express as px
import pandas as pd

# Private
dfp = pd.DataFrame({"subcategory": list(private.keys()), "count": list(private.values())})
dfp = dfp.sort_values("count", ascending=True)
dfp["pct"] = dfp["count"] / dfp["count"].sum()

fig_p = px.bar(
    dfp, x="count", y="subcategory", orientation="h",
    text=dfp["pct"].map(lambda p: f"{p:.1%}"),
    title=f"Private (n={dfp['count'].sum():,}) – barras con %",
    labels={"count":"Conteo","subcategory":"Subcategoría"}
)
fig_p.update_traces(textposition="outside")
fig_p.update_layout(template="plotly_white")
fig_p.show()

# Corporate
dfc = pd.DataFrame({"subcategory": list(corporate.keys()), "count": list(corporate.values())})
dfc = dfc.sort_values("count", ascending=True)
dfc["pct"] = dfc["count"] / dfc["count"].sum()

fig_c = px.bar(
    dfc, x="count", y="subcategory", orientation="h",
    text=dfc["pct"].map(lambda p: f"{p:.1%}"),
    title=f"Corporate (n={dfc['count'].sum():,}) – barras con %",
    labels={"count":"Conteo","subcategory":"Subcategoría"}
)
fig_c.update_traces(textposition="outside")
fig_c.update_layout(template="plotly_white")
fig_c.show()

------------------------------------------------------------------------------------------------------------------------------------------------------------------
import plotly.graph_objects as go

fig_stack = go.Figure()

# Apilado de Corporate
fig_stack.add_trace(go.Bar(name='SUPPLIER', x=['Corporate'], y=[corporate['SUPPLIER']]))
fig_stack.add_trace(go.Bar(name='Shareholder', x=['Corporate'], y=[corporate['Shareholder']]))
fig_stack.add_trace(go.Bar(name='Remarketing Dealer', x=['Corporate'], y=[corporate['Remarketing Dealer']]))
fig_stack.add_trace(go.Bar(name='CUS_CORPORATE', x=['Corporate'], y=[corporate['CUS_CORPORATE']]))

# Apilado de Private
fig_stack.add_trace(go.Bar(name='Individual', x=['Private'], y=[private['Individual']]))
fig_stack.add_trace(go.Bar(name='Director', x=['Private'], y=[private['Director']]))
fig_stack.add_trace(go.Bar(name='UBO', x=['Private'], y=[private['UBO']]))
fig_stack.add_trace(go.Bar(name='Customer', x=['Private'], y=[private['Customer']]))
fig_stack.add_trace(go.Bar(name='Representative', x=['Private'], y=[private['Representative']]))
fig_stack.add_trace(go.Bar(name='Guarantor', x=['Private'], y=[private['Guarantor']]))
fig_stack.add_trace(go.Bar(name='Unknown', x=['Private'], y=[private['Unknown']]))

fig_stack.update_layout(
    barmode='stack',
    title='Private vs Corporate – barras apiladas por subcategoría',
    yaxis_title='Conteo',
    template='plotly_white'
)
fig_stack.show()

------------------------------------------------------------------------------------------------------------------------------------------------------------------
import plotly.graph_objects as go

fig_stack = go.Figure()

# Apilado de Corporate
fig_stack.add_trace(go.Bar(name='SUPPLIER', x=['Corporate'], y=[corporate['SUPPLIER']]))
fig_stack.add_trace(go.Bar(name='Shareholder', x=['Corporate'], y=[corporate['Shareholder']]))
fig_stack.add_trace(go.Bar(name='Remarketing Dealer', x=['Corporate'], y=[corporate['Remarketing Dealer']]))
fig_stack.add_trace(go.Bar(name='CUS_CORPORATE', x=['Corporate'], y=[corporate['CUS_CORPORATE']]))

# Apilado de Private
fig_stack.add_trace(go.Bar(name='Individual', x=['Private'], y=[private['Individual']]))
fig_stack.add_trace(go.Bar(name='Director', x=['Private'], y=[private['Director']]))
fig_stack.add_trace(go.Bar(name='UBO', x=['Private'], y=[private['UBO']]))
fig_stack.add_trace(go.Bar(name='Customer', x=['Private'], y=[private['Customer']]))
fig_stack.add_trace(go.Bar(name='Representative', x=['Private'], y=[private['Representative']]))
fig_stack.add_trace(go.Bar(name='Guarantor', x=['Private'], y=[private['Guarantor']]))
fig_stack.add_trace(go.Bar(name='Unknown', x=['Private'], y=[private['Unknown']]))

fig_stack.update_layout(
    barmode='stack',
    title='Private vs Corporate – barras apiladas por subcategoría',
    yaxis_title='Conteo',
    template='plotly_white'
)
fig_stack.show()

------------------------------------------------------------------------------------------------------------------------------------------------------------------
import plotly.express as px
import pandas as pd

sun = pd.DataFrame(
    [["Private", k, v] for k, v in private.items()] +
    [["Corporate", k, v] for k, v in corporate.items()],
    columns=["Parent","Subcategory","Count"]
)
sun["Root"] = "Total"

fig_sun = px.sunburst(
    sun, path=["Root","Parent","Subcategory"], values="Count",
    title=f"Jerarquía Total → (Private / Corporate) → Subcategorías (Total n={(sun['Count'].sum()):,})",
    color="Parent", color_discrete_sequence=px.colors.qualitative.Set2,
    branchvalues="total"
)
fig_sun.update_layout(template="plotly_white")
fig_sun.show()

------------------------------------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------------------------------------------------------------------------------------------
