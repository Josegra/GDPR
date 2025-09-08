import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------
# Datos
# -----------------------------
private = pd.DataFrame({
    "subcategory": ["Individual","Director","UBO","Customer","Representative","Guarantor","Unknown"],
    "count":      [109736, 5580, 4001, 1327, 784, 18, 1]
})
corporate = pd.DataFrame({
    "subcategory": ["SUPPLIER","Shareholder","Remarketing Dealer","CUS_CORPORATE"],
    "count":      [5501, 63, 524, 995]
})

private_total   = private["count"].sum()
corporate_total = corporate["count"].sum()

# -----------------------------
# 1) Donuts lado a lado
# -----------------------------
fig_donuts = make_subplots(
    rows=1, cols=2, specs=[[{"type":"domain"},{"type":"domain"}]],
    subplot_titles=[f"Private (n={private_total:,})", f"Corporate (n={corporate_total:,})"]
)

fig_donuts.add_trace(
    go.Pie(labels=private["subcategory"], values=private["count"], hole=0.55, name="Private",
           hovertemplate="<b>%{label}</b><br>Conteo: %{value:,}<br>% %{percent}<extra></extra>"),
    row=1, col=1
)
fig_donuts.add_trace(
    go.Pie(labels=corporate["subcategory"], values=corporate["count"], hole=0.55, name="Corporate",
           hovertemplate="<b>%{label}</b><br>Conteo: %{value:,}<br>% %{percent}<extra></extra>"),
    row=1, col=2
)
fig_donuts.update_traces(textinfo="percent+label")
fig_donuts.update_layout(
    title="Distribución por subcategorías: Private vs Corporate",
    template="plotly_white",
    legend_title_text="Subcategoría"
)
fig_donuts.show()

# -----------------------------
# 2) Barras horizontales ordenadas con %
# -----------------------------
def bar_with_percent(df, title):
    d = df.sort_values("count", ascending=True).copy()
    d["pct"] = d["count"] / d["count"].sum()
    fig = px.bar(
        d, x="count", y="subcategory", orientation="h",
        title=title, text=d["pct"].map(lambda p: f"{p:.1%}"),
        labels={"count":"Conteo","subcategory":"Subcategoría"}
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(template="plotly_white", xaxis=dict(showgrid=True))
    return fig

fig_private_bar   = bar_with_percent(private,  f"Private (n={private_total:,}) – barras con %")
fig_corporate_bar = bar_with_percent(corporate,f"Corporate (n={corporate_total:,}) – barras con %")

fig_private_bar.show()
fig_corporate_bar.show()

# -----------------------------
# 3) Sunburst jerárquico (Total → Parent → Subcategoría)
# -----------------------------
sun_data = pd.concat([
    pd.DataFrame({"parent":"Private",   "subcategory": private["subcategory"],   "count": private["count"]}),
    pd.DataFrame({"parent":"Corporate", "subcategory": corporate["subcategory"], "count": corporate["count"]}),
], ignore_index=True)

sun_data["root"] = "Total"

fig_sun = px.sunburst(
    sun_data,
    path=["root", "parent", "subcategory"],
    values="count",
    title=f"Jerarquía Total → (Private / Corporate) → Subcategorías (Total n={(private_total+corporate_total):,})",
    color="parent",
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig_sun.update_layout(template="plotly_white")
fig_sun.update_traces(hovertemplate="<b>%{label}</b><br>Conteo: %{value:,}<extra></extra>")
fig_sun.show()
