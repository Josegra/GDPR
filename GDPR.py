import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.colors import qualitative
from plotly.io import to_html
import os

# ── Palette ──
palette = {
    "remarketing": "#636EFA", "third party": "#EF5538", "datacap": "#00CC96",
    "Customer": "#1f77b4", "UBO": "#ff7f0e", "Representative": "#2ca02c",
    "Shareholder": "#d62728", "Director": "#9467bd", "CUS_PRIVATE": "#d62728",
    "SUPPLIER": "#9467bd", "CUS CORPORATE": "#8c564b",
}

# ── Branch values ──
branch_vals = sorted([b for b in df_result.select("BRANCH").distinct().rdd.flatMap(lambda x: x).collect() if b])
all_branches = ["All"] + branch_vals

fig = make_subplots(rows=2, cols=1,
                    subplot_titles=("Counts by Date – summed per source_type",
                                    "Counts by Date – summed per source_type2_viz"),
                    vertical_spacing=0.18, shared_xaxes=False)

# ════════════════════════════════════════════════
# GRAPH 1 — igual que el tuyo original
# 3 line traces + 3 bar traces
# ════════════════════════════════════════════════
df_counts_type = (df_result.groupBy("date","source_type")
                  .agg(F.sum("count").alias("cnt")))
pdf_type = (df_counts_type.toPandas()
            .pivot(index="date", columns="source_type", values="cnt")
            .fillna(0).reset_index())
pdf_type["date"] = pdf_type["date"].astype(str)
x_dates = pdf_type["date"].tolist()

for col in ["remarketing","third party","datacap"]:
    if col not in pdf_type.columns: pdf_type[col] = 0

# line traces (visibles por defecto)
for col, color in [("remarketing","#636EFA"),("third party","#EF5538"),("datacap","#00CC96")]:
    fig.add_trace(go.Scatter(x=x_dates, y=pdf_type[col].tolist(),
                             name=col.title(), mode="lines+markers",
                             line=dict(color=color), visible=True,
                             legendgroup=col, legendgrouptitle_text=""), row=1, col=1)

# bar traces (ocultas por defecto)
for col, color in [("remarketing","#636EFA"),("third party","#EF5538"),("datacap","#00CC96")]:
    fig.add_trace(go.Bar(x=x_dates, y=pdf_type[col].tolist(),
                         name=col.title(), marker_color=color,
                         visible=False, legendgroup=col,
                         showlegend=False), row=1, col=1)

# indices graph 1
n1 = 3  # num source_types
# traces 0,1,2 = lines  |  traces 3,4,5 = bars
vis_g1_lines = [True]*n1  + [False]*n1
vis_g1_bars  = [False]*n1 + [True]*n1

# ════════════════════════════════════════════════
# GRAPH 2 — igual que el tuyo original
# por cada source_type: line traces + bar traces
# ════════════════════════════════════════════════
df_counts_s2 = (df_result.groupBy("date","source_type","source_type2_viz")
                .agg(F.sum("count").alias("cnt")))
pdf_s2 = df_counts_s2.toPandas()
pdf_s2["date"] = pd.to_datetime(pdf_s2["date"])
date_vals = pdf_s2["date"].dt.strftime("%Y-%m-%d").sort_values().unique().tolist()

# extend palette si hay colores extra
all_s2 = pdf_s2["source_type2_viz"].dropna().unique().tolist()
extra_colors = qualitative.Plotly * ((len(all_s2) // len(qualitative.Plotly)) + 1)
for i, s2 in enumerate(all_s2):
    if s2 not in palette:
        palette[s2] = extra_colors[i]

traces_line_g2, traces_bar_g2 = [], []
src_trace_map = {"remarketing": [], "third party": [], "datacap": []}  # indices por src

for src in ["remarketing", "third party", "datacap"]:
    sub_groups = (pdf_s2[pdf_s2["source_type"] == src]["source_type2_viz"]
                  .dropna().unique().tolist())
    for sg in sub_groups:
        y_vals = [int(pdf_s2[(pdf_s2["date"].dt.strftime("%Y-%m-%d") == d) &
                             (pdf_s2["source_type"] == src) &
                             (pdf_s2["source_type2_viz"] == sg)]["cnt"].sum())
                  for d in date_vals]
        color = palette.get(sg, palette.get(src, "#777777"))
        trace_name = f"{sg} ({src})"

        # line
        fig.add_trace(go.Scatter(x=date_vals, y=y_vals, name=trace_name,
                                 mode="lines+markers", line=dict(width=2, color=color),
                                 visible=False, legendgroup=sg,
                                 showlegend=True), row=2, col=1)
        src_trace_map[src].append(len(fig.data) - 1)
        traces_line_g2.append(len(fig.data) - 1)

        # bar
        fig.add_trace(go.Bar(x=date_vals, y=y_vals, name=trace_name,
                             marker_color=color, visible=False,
                             legendgroup=sg, showlegend=False), row=2, col=1)
        src_trace_map[src].append(len(fig.data) - 1)
        traces_bar_g2.append(len(fig.data) - 1)

total = len(fig.data)
# traces 0-5 = graph1  |  traces 6..total = graph2

# ════════════════════════════════════════════════
# BUTTONS GRAPH 1 — Lines / Bars (igual que el tuyo)
# ════════════════════════════════════════════════
def make_vis_g1(show_lines):
    vis = [False] * total
    for i in range(n1):
        vis[i]      = show_lines   # lines
        vis[i + n1] = not show_lines  # bars
    return vis

buttons_g1 = [
    dict(label="Lines", method="update", args=[{"visible": make_vis_g1(True)}]),
    dict(label="Bars",  method="update", args=[{"visible": make_vis_g1(False)}]),
]

# ════════════════════════════════════════════════
# BUTTONS GRAPH 2 — Remarketing/ThirdParty/Datacap Lines+Bars
# igual que el tuyo: 6 botones (src Lines + src Bars)
# ════════════════════════════════════════════════
buttons_g2 = []
for src in ["remarketing", "third party", "datacap"]:
    line_idx = [i for i in src_trace_map[src] if i in traces_line_g2]
    bar_idx  = [i for i in src_trace_map[src] if i in traces_bar_g2]

    # Lines button
    vis_lines = [False] * total
    for i in line_idx: vis_lines[i] = True
    buttons_g2.append(dict(label=f"{src.title()} Lines",
                           method="update", args=[{"visible": vis_lines}]))
    # Bars button
    vis_bars = [False] * total
    for i in bar_idx: vis_bars[i] = True
    buttons_g2.append(dict(label=f"{src.title()} Bars",
                           method="update", args=[{"visible": vis_bars}]))

# ════════════════════════════════════════════════
# BRANCH DROPDOWN — afecta a los 2 subplots
# ════════════════════════════════════════════════
branch_buttons = []
for branch in all_branches:
    df_b = df_result if branch == "All" else df_result.filter(F.col("BRANCH") == branch)

    # recalcula graph 1
    pdf_b1 = (df_b.groupBy("date","source_type").agg(F.sum("count").alias("cnt"))
              .toPandas().pivot(index="date", columns="source_type", values="cnt")
              .fillna(0).reset_index())
    pdf_b1["date"] = pdf_b1["date"].astype(str)
    for col in ["remarketing","third party","datacap"]:
        if col not in pdf_b1.columns: pdf_b1[col] = 0
    x1 = pdf_b1["date"].tolist()

    # recalcula graph 2
    pdf_b2 = (df_b.groupBy("date","source_type","source_type2_viz")
              .agg(F.sum("count").alias("cnt")).toPandas())
    pdf_b2["date"] = pd.to_datetime(pdf_b2["date"])
    dvals_b = pdf_b2["date"].dt.strftime("%Y-%m-%d").sort_values().unique().tolist()

    new_x, new_y = [], []
    # graph 1: 3 lines + 3 bars
    for col in ["remarketing","third party","datacap"]:
        new_x.append(x1); new_y.append(pdf_b1[col].tolist())
    for col in ["remarketing","third party","datacap"]:
        new_x.append(x1); new_y.append(pdf_b1[col].tolist())

    # graph 2: mismo orden que se añadieron las trazas
    for src in ["remarketing","third party","datacap"]:
        sub = (pdf_b2[pdf_b2["source_type"]==src]["source_type2_viz"]
               .dropna().unique().tolist())
        for sg in sub:
            y = [int(pdf_b2[(pdf_b2["date"].dt.strftime("%Y-%m-%d")==d) &
                            (pdf_b2["source_type"]==src) &
                            (pdf_b2["source_type2_viz"]==sg)]["cnt"].sum())
                 for d in dvals_b]
            new_x.append(dvals_b); new_y.append(y)  # line
            new_x.append(dvals_b); new_y.append(y)  # bar

    branch_buttons.append(dict(
        label=branch, method="update",
        args=[{"x": new_x, "y": new_y},
              {"title": f"Forces VIZ | Branch: <b>{branch}</b>"}]
    ))

# ════════════════════════════════════════════════
# LAYOUT
# ════════════════════════════════════════════════
fig.update_layout(
    title=dict(text="Forces VIZ | Branch: <b>All</b>",
               x=0.5, xanchor="center", font=dict(size=16)),
    template="plotly_white",
    hovermode="x unified",
    height=950,
    yaxis_type="log", yaxis2_type="log",
    legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.12),
    margin=dict(t=150, b=100, l=60, r=40),
    updatemenus=[
        # ── Branch dropdown ──
        dict(buttons=branch_buttons, direction="down", showactive=True,
             x=0.0, xanchor="left", y=1.13, yanchor="top",
             bgcolor="#5B6EE1", font=dict(color="white")),
        # ── Graph 1: Lines / Bars ──
        dict(buttons=buttons_g1, type="buttons", direction="right",
             showactive=True, x=0.5, xanchor="center", y=1.13, yanchor="top",
             bgcolor="#444", font=dict(color="white")),
        # ── Graph 2: source_type Lines/Bars ──
        dict(buttons=buttons_g2, type="buttons", direction="right",
             showactive=True, x=0.5, xanchor="center", y=0.46, yanchor="top",
             bgcolor="#2a2a2a", font=dict(color="white")),
    ],
    annotations=[
        dict(text="<b>Branch:</b>", x=0.0, y=1.16,
             xref="paper", yref="paper", showarrow=False, font=dict(size=12)),
    ]
)

fig.show()

# ── Export ──
OUTPUT_PATH = "/Workspace/Users/TU_EMAIL@dominio.com/forces_viz.html"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
fig.write_html(OUTPUT_PATH, include_plotlyjs="cdn", full_html=True,
               config={"scrollZoom": True})
print(f"✅ {OUTPUT_PATH}")





#################################################################
#################################################################
#################################################################
#################################################################
#################################################################
#################################################################




from plotly.io import to_html
import os

# ── tus figuras ya construidas: fig_counts y fig_s2 ──
fig_counts_html = to_html(fig_counts, include_plotlyjs="cdn", full_html=False,
                          config={"scrollZoom": True, "displayModeBar": True,
                                  "toImageButtonOptions": {"filename": "source_type", "scale": 2}})

fig_s2_html = to_html(fig_s2, include_plotlyjs=False, full_html=False,
                      config={"scrollZoom": True, "displayModeBar": True,
                              "toImageButtonOptions": {"filename": "source_type2", "scale": 2}})

# ── KPIs (calcula desde tus dfs) ──
kpi_rem  = df_result.filter(F.col("source_type")=="remarketing").agg(F.sum("count")).collect()[0][0]
kpi_tp   = df_result.filter(F.col("source_type")=="third party").agg(F.sum("count")).collect()[0][0]
kpi_dc   = df_result.filter(F.col("source_type")=="datacap").agg(F.sum("count")).collect()[0][0]

def fmt(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.0f}K"
    return str(n)

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Forces VIZ</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0 }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f3; color: #111; min-height: 100vh }}
    header {{ background: #fff; border-bottom: 1px solid #e8e8e8;
              padding: 14px 28px; display: flex; align-items: center;
              justify-content: space-between }}
    header h1 {{ font-size: 16px; font-weight: 500; color: #111 }}
    header span {{ font-size: 12px; color: #888 }}
    .layout {{ display: flex; min-height: calc(100vh - 53px) }}
    .sidebar {{ width: 220px; min-width: 220px; background: #fff;
                border-right: 1px solid #e8e8e8; padding: 20px 16px;
                display: flex; flex-direction: column; gap: 20px }}
    .sidebar h3 {{ font-size: 10px; font-weight: 500; color: #999;
                   text-transform: uppercase; letter-spacing: 0.07em }}
    .filter-group {{ display: flex; flex-direction: column; gap: 6px }}
    .filter-group label {{ font-size: 12px; color: #555 }}
    select {{ width: 100%; padding: 7px 10px; font-size: 13px;
              border: 1px solid #ddd; border-radius: 8px; background: #fff;
              color: #111; cursor: pointer }}
    select:hover {{ border-color: #5B6EE1 }}
    .main {{ flex: 1; padding: 20px 24px; display: flex; flex-direction: column; gap: 16px }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px }}
    .kpi {{ background: #fff; border: 1px solid #e8e8e8; border-radius: 10px;
            padding: 14px 18px }}
    .kpi-label {{ font-size: 12px; color: #888; margin-bottom: 4px }}
    .kpi-value {{ font-size: 22px; font-weight: 500 }}
    .kpi-value.blue {{ color: #5B6EE1 }}
    .kpi-value.coral {{ color: #D85A30 }}
    .kpi-value.green {{ color: #0F6E56 }}
    .chart-card {{ background: #fff; border: 1px solid #e8e8e8; border-radius: 10px;
                   padding: 16px 20px }}
    .chart-card h2 {{ font-size: 13px; font-weight: 500; color: #666;
                      margin-bottom: 8px }}
    footer {{ text-align: center; padding: 16px; font-size: 11px; color: #bbb }}
  </style>
</head>
<body>
  <header>
    <h1>Forces VIZ</h1>
    <span id="ts"></span>
  </header>

  <div class="layout">
    <div class="sidebar">
      <h3>Filters</h3>

      <div class="filter-group">
        <label>Branch</label>
        <select id="sel-branch" onchange="applyFilters()">
          <option value="All">All branches</option>
          {"".join(f'<option value="{b}">{b}</option>' for b in branch_vals)}
        </select>
      </div>

      <div class="filter-group">
        <label>Source type</label>
        <select id="sel-src" onchange="applyFilters()">
          <option value="All">All</option>
          <option value="remarketing">Remarketing</option>
          <option value="third party">Third party</option>
          <option value="datacap">Datacap</option>
        </select>
      </div>
    </div>

    <div class="main">
      <div class="kpi-grid">
        <div class="kpi">
          <div class="kpi-label">Remarketing</div>
          <div class="kpi-value blue">{fmt(kpi_rem)}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Third party</div>
          <div class="kpi-value coral">{fmt(kpi_tp)}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Datacap</div>
          <div class="kpi-value green">{fmt(kpi_dc)}</div>
        </div>
      </div>

      <div class="chart-card">
        <h2>Counts by date — source type</h2>
        <div id="chart1">{fig_counts_html}</div>
      </div>

      <div class="chart-card">
        <h2>Counts by date — source type 2 viz</h2>
        <div id="chart2">{fig_s2_html}</div>
      </div>
    </div>
  </div>

  <footer>Forces VIZ · generated by Databricks</footer>

  <script>
    document.getElementById('ts').textContent =
      'Generated: ' + new Date().toLocaleString('es-ES');

    function applyFilters() {{
      var branch = document.getElementById('sel-branch').value;
      var src    = document.getElementById('sel-src').value;
      // Los gráficos Plotly ya tienen sus propios botones internos.
      // Aquí podrías llamar a Plotly.restyle() si quisieras
      // controlarlos desde el sidebar — extensible según necesites.
      console.log('Filter:', branch, src);
    }}
  </script>
</body>
</html>"""

OUTPUT_PATH = "/Workspace/Users/TU_EMAIL@dominio.com/forces_viz.html"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ {OUTPUT_PATH}")



##############################################################
##############################################################
##############################################################
##############################################################
##############################################################

from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
from plotly.colors import qualitative
from plotly.io import to_html
import os

# ── Palette ──
palette = {
    "remarketing": "#636EFA", "third party": "#EF5538", "datacap": "#00CC96",
    "Customer": "#1f77b4", "UBO": "#ff7f0e", "Representative": "#2ca02c",
    "Shareholder": "#d62728", "Director": "#9467bd", "CUS_PRIVATE": "#d62728",
    "SUPPLIER": "#9467bd", "CUS CORPORATE": "#8c564b",
}

# ── Datos graph 1 ──
pdf_type = (df_result.groupBy("date","source_type")
            .agg(F.sum("count").alias("cnt"))
            .toPandas()
            .pivot(index="date", columns="source_type", values="cnt")
            .fillna(0).reset_index())
pdf_type["date"] = pd.to_datetime(pdf_type["date"])
for col in ["remarketing","third party","datacap"]:
    if col not in pdf_type.columns: pdf_type[col] = 0
pdf_type = pdf_type.sort_values("date")

# ── Datos graph 2 ──
pdf_s2 = (df_result.groupBy("date","source_type","source_type2_viz")
          .agg(F.sum("count").alias("cnt")).toPandas())
pdf_s2["date"] = pd.to_datetime(pdf_s2["date"])
pdf_s2 = pdf_s2.sort_values("date")
date_vals = pdf_s2["date"].dt.strftime("%Y-%m-%d").sort_values().unique().tolist()

all_s2 = pdf_s2["source_type2_viz"].dropna().unique().tolist()
extra  = qualitative.Plotly * ((len(all_s2) // len(qualitative.Plotly)) + 1)
for i, s2 in enumerate(all_s2):
    if s2 not in palette: palette[s2] = extra[i]

# ════════════════════════════════════════════
# FIGURA
# ════════════════════════════════════════════
fig = make_subplots(
    rows=3, cols=1,
    row_heights=[0.08, 0.46, 0.46],   # fila 0 = rangeslider visual
    vertical_spacing=0.08,
    subplot_titles=("", "Counts by date — source type",
                    "Counts by date — source type 2 viz"),
    shared_xaxes=False,
)

# ── Graph 1: lines (visible) + bars (ocultas) ──
colors_g1 = {"remarketing":"#636EFA","third party":"#EF5538","datacap":"#00CC96"}
for col in ["remarketing","third party","datacap"]:
    fig.add_trace(go.Scatter(
        x=pdf_type["date"], y=pdf_type[col],
        name=col.title(), mode="lines+markers",
        line=dict(color=colors_g1[col], width=2),
        marker=dict(size=4), visible=True,
        legendgroup=col, legendgrouptitle_text="Source type",
    ), row=2, col=1)

for col in ["remarketing","third party","datacap"]:
    fig.add_trace(go.Bar(
        x=pdf_type["date"], y=pdf_type[col],
        name=col.title(), marker_color=colors_g1[col],
        visible=False, legendgroup=col, showlegend=False,
    ), row=2, col=1)

n_g1 = 3  # trazas por tipo en graph1

# ── Graph 2: lines + bars por source_type ──
traces_g2_line, traces_g2_bar = [], []
src_map = {"remarketing":[], "third party":[], "datacap":[]}

for src in ["remarketing","third party","datacap"]:
    subs = (pdf_s2[pdf_s2["source_type"]==src]["source_type2_viz"]
            .dropna().unique().tolist())
    for sg in subs:
        yv = [int(pdf_s2[
                (pdf_s2["date"].dt.strftime("%Y-%m-%d")==d) &
                (pdf_s2["source_type"]==src) &
                (pdf_s2["source_type2_viz"]==sg)
              ]["cnt"].sum()) for d in date_vals]
        c = palette.get(sg, palette.get(src,"#777"))

        fig.add_trace(go.Scatter(
            x=date_vals, y=yv, name=f"{sg}",
            mode="lines+markers", line=dict(width=2,color=c),
            marker=dict(size=4), visible=False,
            legendgroup=src,
            legendgrouptitle_text=src.title(),
        ), row=3, col=1)
        idx = len(fig.data)-1
        traces_g2_line.append(idx); src_map[src].append(idx)

        fig.add_trace(go.Bar(
            x=date_vals, y=yv, name=f"{sg}",
            marker_color=c, visible=False,
            legendgroup=src, showlegend=False,
        ), row=3, col=1)
        idx2 = len(fig.data)-1
        traces_g2_bar.append(idx2); src_map[src].append(idx2)

total = len(fig.data)

# ════════════════════════════════════════════
# HELPERS de visibilidad
# ════════════════════════════════════════════
def vis(*on_indices):
    v = [False]*total
    for i in on_indices: v[i] = True
    return v

# Graph 1
g1_lines = list(range(0, n_g1))
g1_bars  = list(range(n_g1, n_g1*2))

def g1_vis(lines=True):
    v = [False]*total
    for i in (g1_lines if lines else g1_bars): v[i] = True
    return v

# Graph 2 — por src, lines o bars
def g2_vis(src_filter, lines=True):
    v = [False]*total
    pool = traces_g2_line if lines else traces_g2_bar
    for src, idxs in src_map.items():
        if src_filter in ("all", src):
            for i in idxs:
                if i in pool: v[i] = True
    return v

# ════════════════════════════════════════════
# BOTONES GRAPH 1 — Lines / Bars
# ════════════════════════════════════════════
btns_g1 = [
    dict(label="● Lines", method="update",
         args=[{"visible": g1_vis(True)},  {"yaxis2.type":"log"}]),
    dict(label="▮ Bars",  method="update",
         args=[{"visible": g1_vis(False)}, {"yaxis2.type":"log"}]),
]

# ════════════════════════════════════════════
# BOTONES GRAPH 2 — 6 botones igual que el original
# ════════════════════════════════════════════
btns_g2 = []
for src in ["remarketing","third party","datacap"]:
    btns_g2.append(dict(
        label=f"● {src.title()}",
        method="update",
        args=[{"visible": g2_vis(src, lines=True)}]
    ))
    btns_g2.append(dict(
        label=f"▮ {src.title()}",
        method="update",
        args=[{"visible": g2_vis(src, lines=False)}]
    ))
# botón All lines
btns_g2.insert(0, dict(
    label="● All",
    method="update",
    args=[{"visible": g2_vis("all", lines=True)}]
))

# ════════════════════════════════════════════
# LAYOUT
# ════════════════════════════════════════════
fig.update_layout(
    template="plotly_white",
    height=820,
    hovermode="x unified",
    margin=dict(t=100, b=40, l=60, r=180),

    # eje log en subplots 2 y 3
    yaxis2=dict(title="Count", type="log", showgrid=True, gridcolor="#f0f0f0"),
    yaxis3=dict(title="Count", type="log", showgrid=True, gridcolor="#f0f0f0"),
    xaxis2=dict(
        title="Date",
        rangeslider=dict(visible=True, thickness=0.04),
        type="date",
    ),
    xaxis3=dict(title="Date"),

    legend=dict(
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#e0e0e0",
        borderwidth=1,
        tracegroupgap=12,
        font=dict(size=11),
        x=1.01, y=1,
        xanchor="left",
    ),

    updatemenus=[
        # ── G1: Lines / Bars — encima del subplot 1 ──
        dict(
            buttons=btns_g1,
            type="buttons", direction="right",
            showactive=True,
            x=0.0, xanchor="left",
            y=0.985, yanchor="top",
            bgcolor="#f0f0f0",
            activecolor="#5B6EE1",
            font=dict(size=12),
            bordercolor="#ccc", borderwidth=1,
            pad=dict(r=4, t=4, b=4),
        ),
        # ── G2: source_type — encima del subplot 2 ──
        dict(
            buttons=btns_g2,
            type="buttons", direction="right",
            showactive=True,
            x=0.0, xanchor="left",
            y=0.46, yanchor="top",
            bgcolor="#f0f0f0",
            activecolor="#2a2a2a",
            font=dict(size=11),
            bordercolor="#ccc", borderwidth=1,
            pad=dict(r=4, t=4, b=4),
        ),
    ],

    annotations=[
        dict(text="Graph 1", x=0.0, y=1.01, xref="paper",
             yref="paper", showarrow=False,
             font=dict(size=11, color="#888")),
        dict(text="Graph 2", x=0.0, y=0.48, xref="paper",
             yref="paper", showarrow=False,
             font=dict(size=11, color="#888")),
    ],
)

fig.show()

# ── Export ──
OUTPUT_PATH = "/Workspace/Users/TU_EMAIL@dominio.com/forces_viz.html"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
fig.write_html(OUTPUT_PATH, include_plotlyjs="cdn", full_html=True,
               config={"scrollZoom": True, "displayModeBar": True,
                       "toImageButtonOptions": {"filename":"forces_viz","scale":2}})
print(f"✅ {OUTPUT_PATH}")
