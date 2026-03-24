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
                    vertical_spacing=0.18,
                    shared_xaxes=True)   # <-- TRUE para sincronizar hover

# ════════════════════════════════════════════════
# GRAPH 1
# ════════════════════════════════════════════════
df_counts_type = (df_result.groupBy("date","source_type")
                  .agg(F.sum("count").alias("cnt")))
pdf_type = (df_counts_type.toPandas()
            .pivot(index="date", columns="source_type", values="cnt")
            .fillna(0).reset_index())
pdf_type["date"] = pd.to_datetime(pdf_type["date"])   # <-- datetime, no string
pdf_type = pdf_type.sort_values("date")
x_dates = pdf_type["date"].tolist()

for col in ["remarketing","third party","datacap"]:
    if col not in pdf_type.columns: pdf_type[col] = 0

for col, color in [("remarketing","#636EFA"),("third party","#EF5538"),("datacap","#00CC96")]:
    fig.add_trace(go.Scatter(x=x_dates, y=pdf_type[col].tolist(),
                             name=col.title(), mode="lines+markers",
                             line=dict(color=color), visible=True,
                             legendgroup=col), row=1, col=1)

for col, color in [("remarketing","#636EFA"),("third party","#EF5538"),("datacap","#00CC96")]:
    fig.add_trace(go.Bar(x=x_dates, y=pdf_type[col].tolist(),
                         name=col.title(), marker_color=color,
                         visible=False, legendgroup=col,
                         showlegend=False), row=1, col=1)

n1 = 3
vis_g1_lines = [True]*n1  + [False]*n1
vis_g1_bars  = [False]*n1 + [True]*n1

# ════════════════════════════════════════════════
# GRAPH 2
# ════════════════════════════════════════════════
df_counts_s2 = (df_result.groupBy("date","source_type","source_type2_viz")
                .agg(F.sum("count").alias("cnt")))
pdf_s2 = df_counts_s2.toPandas()
pdf_s2["date"] = pd.to_datetime(pdf_s2["date"])       # <-- datetime
pdf_s2 = pdf_s2.sort_values("date")
date_vals = pdf_s2["date"].sort_values().unique().tolist()  # <-- datetime list, no strings

all_s2 = pdf_s2["source_type2_viz"].dropna().unique().tolist()
extra_colors = qualitative.Plotly * ((len(all_s2) // len(qualitative.Plotly)) + 1)
for i, s2 in enumerate(all_s2):
    if s2 not in palette:
        palette[s2] = extra_colors[i]

traces_line_g2, traces_bar_g2 = [], []
src_trace_map = {"remarketing": [], "third party": [], "datacap": []}

for src in ["remarketing", "third party", "datacap"]:
    sub_groups = (pdf_s2[pdf_s2["source_type"] == src]["source_type2_viz"]
                  .dropna().unique().tolist())
    for sg in sub_groups:
        y_vals = [int(pdf_s2[(pdf_s2["date"] == d) &        # <-- compara datetime con datetime
                             (pdf_s2["source_type"] == src) &
                             (pdf_s2["source_type2_viz"] == sg)]["cnt"].sum())
                  for d in date_vals]
        color = palette.get(sg, palette.get(src, "#777777"))
        trace_name = f"{sg} ({src})"

        fig.add_trace(go.Scatter(x=date_vals, y=y_vals, name=trace_name,
                                 mode="lines+markers", line=dict(width=2, color=color),
                                 visible=False, legendgroup=sg,
                                 showlegend=True), row=2, col=1)
        src_trace_map[src].append(len(fig.data) - 1)
        traces_line_g2.append(len(fig.data) - 1)

        fig.add_trace(go.Bar(x=date_vals, y=y_vals, name=trace_name,
                             marker_color=color, visible=False,
                             legendgroup=sg, showlegend=False), row=2, col=1)
        src_trace_map[src].append(len(fig.data) - 1)
        traces_bar_g2.append(len(fig.data) - 1)

total = len(fig.data)

# ════════════════════════════════════════════════
# BUTTONS G1
# ════════════════════════════════════════════════
def make_vis_g1(show_lines):
    vis = [False] * total
    for i in range(n1):
        vis[i]      = show_lines
        vis[i + n1] = not show_lines
    return vis

buttons_g1 = [
    dict(label="Lines", method="update", args=[{"visible": make_vis_g1(True)}]),
    dict(label="Bars",  method="update", args=[{"visible": make_vis_g1(False)}]),
]

# ════════════════════════════════════════════════
# BUTTONS G2
# ════════════════════════════════════════════════
buttons_g2 = []
for src in ["remarketing", "third party", "datacap"]:
    line_idx = [i for i in src_trace_map[src] if i in traces_line_g2]
    bar_idx  = [i for i in src_trace_map[src] if i in traces_bar_g2]

    vis_lines = [False] * total
    for i in line_idx: vis_lines[i] = True
    buttons_g2.append(dict(label=f"{src.title()} Lines",
                           method="update", args=[{"visible": vis_lines}]))

    vis_bars = [False] * total
    for i in bar_idx: vis_bars[i] = True
    buttons_g2.append(dict(label=f"{src.title()} Bars",
                           method="update", args=[{"visible": vis_bars}]))

# ════════════════════════════════════════════════
# BRANCH DROPDOWN
# ════════════════════════════════════════════════
branch_buttons = []
for branch in all_branches:
    df_b = df_result if branch == "All" else df_result.filter(F.col("BRANCH") == branch)

    # graph 1
    pdf_b1 = (df_b.groupBy("date","source_type").agg(F.sum("count").alias("cnt"))
              .toPandas().pivot(index="date", columns="source_type", values="cnt")
              .fillna(0).reset_index())
    pdf_b1["date"] = pd.to_datetime(pdf_b1["date"])   # <-- datetime
    pdf_b1 = pdf_b1.sort_values("date")
    for col in ["remarketing","third party","datacap"]:
        if col not in pdf_b1.columns: pdf_b1[col] = 0
    x1 = pdf_b1["date"].tolist()

    # graph 2
    pdf_b2 = (df_b.groupBy("date","source_type","source_type2_viz")
              .agg(F.sum("count").alias("cnt")).toPandas())
    pdf_b2["date"] = pd.to_datetime(pdf_b2["date"])   # <-- datetime
    pdf_b2 = pdf_b2.sort_values("date")
    dvals_b = pdf_b2["date"].sort_values().unique().tolist()  # <-- datetime list

    new_x, new_y = [], []
    for col in ["remarketing","third party","datacap"]:
        new_x.append(x1); new_y.append(pdf_b1[col].tolist())
    for col in ["remarketing","third party","datacap"]:
        new_x.append(x1); new_y.append(pdf_b1[col].tolist())

    for src in ["remarketing","third party","datacap"]:
        sub = (pdf_b2[pdf_b2["source_type"]==src]["source_type2_viz"]
               .dropna().unique().tolist())
        for sg in sub:
            y = [int(pdf_b2[(pdf_b2["date"] == d) &        # <-- datetime == datetime
                            (pdf_b2["source_type"]==src) &
                            (pdf_b2["source_type2_viz"]==sg)]["cnt"].sum())
                 for d in dvals_b]
            new_x.append(dvals_b); new_y.append(y)
            new_x.append(dvals_b); new_y.append(y)

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
    xaxis=dict(type="date"),           # <-- fuerza tipo date
    xaxis2=dict(type="date"),          # <-- fuerza tipo date
    legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.12),
    margin=dict(t=150, b=100, l=60, r=40),
    updatemenus=[
        dict(buttons=branch_buttons, direction="down", showactive=True,
             x=0.0, xanchor="left", y=1.13, yanchor="top",
             bgcolor="#5B6EE1", font=dict(color="white")),
        dict(buttons=buttons_g1, type="buttons", direction="right",
             showactive=True, x=0.5, xanchor="center", y=1.13, yanchor="top",
             bgcolor="#444", font=dict(color="white")),
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




#####################################################################
#####################################################################
#####################################################################
#####################################################################

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
                    vertical_spacing=0.18,
                    shared_xaxes=True)   # <-- TRUE para sincronizar hover

# ════════════════════════════════════════════════
# GRAPH 1
# ════════════════════════════════════════════════
df_counts_type = (df_result.groupBy("date","source_type")
                  .agg(F.sum("count").alias("cnt")))
pdf_type = (df_counts_type.toPandas()
            .pivot(index="date", columns="source_type", values="cnt")
            .fillna(0).reset_index())
pdf_type["date"] = pd.to_datetime(pdf_type["date"])   # <-- datetime, no string
pdf_type = pdf_type.sort_values("date")
x_dates = pdf_type["date"].tolist()

for col in ["remarketing","third party","datacap"]:
    if col not in pdf_type.columns: pdf_type[col] = 0

for col, color in [("remarketing","#636EFA"),("third party","#EF5538"),("datacap","#00CC96")]:
    fig.add_trace(go.Scatter(x=x_dates, y=pdf_type[col].tolist(),
                             name=col.title(), mode="lines+markers",
                             line=dict(color=color), visible=True,
                             legendgroup=col), row=1, col=1)

for col, color in [("remarketing","#636EFA"),("third party","#EF5538"),("datacap","#00CC96")]:
    fig.add_trace(go.Bar(x=x_dates, y=pdf_type[col].tolist(),
                         name=col.title(), marker_color=color,
                         visible=False, legendgroup=col,
                         showlegend=False), row=1, col=1)

n1 = 3
vis_g1_lines = [True]*n1  + [False]*n1
vis_g1_bars  = [False]*n1 + [True]*n1

# ════════════════════════════════════════════════
# GRAPH 2
# ════════════════════════════════════════════════
df_counts_s2 = (df_result.groupBy("date","source_type","source_type2_viz")
                .agg(F.sum("count").alias("cnt")))
pdf_s2 = df_counts_s2.toPandas()
pdf_s2["date"] = pd.to_datetime(pdf_s2["date"])       # <-- datetime
pdf_s2 = pdf_s2.sort_values("date")
date_vals = pdf_s2["date"].sort_values().unique().tolist()  # <-- datetime list, no strings

all_s2 = pdf_s2["source_type2_viz"].dropna().unique().tolist()
extra_colors = qualitative.Plotly * ((len(all_s2) // len(qualitative.Plotly)) + 1)
for i, s2 in enumerate(all_s2):
    if s2 not in palette:
        palette[s2] = extra_colors[i]

traces_line_g2, traces_bar_g2 = [], []
src_trace_map = {"remarketing": [], "third party": [], "datacap": []}

for src in ["remarketing", "third party", "datacap"]:
    sub_groups = (pdf_s2[pdf_s2["source_type"] == src]["source_type2_viz"]
                  .dropna().unique().tolist())
    for sg in sub_groups:
        y_vals = [int(pdf_s2[(pdf_s2["date"] == d) &        # <-- compara datetime con datetime
                             (pdf_s2["source_type"] == src) &
                             (pdf_s2["source_type2_viz"] == sg)]["cnt"].sum())
                  for d in date_vals]
        color = palette.get(sg, palette.get(src, "#777777"))
        trace_name = f"{sg} ({src})"

        fig.add_trace(go.Scatter(x=date_vals, y=y_vals, name=trace_name,
                                 mode="lines+markers", line=dict(width=2, color=color),
                                 visible=False, legendgroup=sg,
                                 showlegend=True), row=2, col=1)
        src_trace_map[src].append(len(fig.data) - 1)
        traces_line_g2.append(len(fig.data) - 1)

        fig.add_trace(go.Bar(x=date_vals, y=y_vals, name=trace_name,
                             marker_color=color, visible=False,
                             legendgroup=sg, showlegend=False), row=2, col=1)
        src_trace_map[src].append(len(fig.data) - 1)
        traces_bar_g2.append(len(fig.data) - 1)

total = len(fig.data)

# ════════════════════════════════════════════════
# BUTTONS G1
# ════════════════════════════════════════════════
def make_vis_g1(show_lines):
    vis = [False] * total
    for i in range(n1):
        vis[i]      = show_lines
        vis[i + n1] = not show_lines
    return vis

buttons_g1 = [
    dict(label="Lines", method="update", args=[{"visible": make_vis_g1(True)}]),
    dict(label="Bars",  method="update", args=[{"visible": make_vis_g1(False)}]),
]

# ════════════════════════════════════════════════
# BUTTONS G2
# ════════════════════════════════════════════════
buttons_g2 = []
for src in ["remarketing", "third party", "datacap"]:
    line_idx = [i for i in src_trace_map[src] if i in traces_line_g2]
    bar_idx  = [i for i in src_trace_map[src] if i in traces_bar_g2]

    vis_lines = [False] * total
    for i in line_idx: vis_lines[i] = True
    buttons_g2.append(dict(label=f"{src.title()} Lines",
                           method="update", args=[{"visible": vis_lines}]))

    vis_bars = [False] * total
    for i in bar_idx: vis_bars[i] = True
    buttons_g2.append(dict(label=f"{src.title()} Bars",
                           method="update", args=[{"visible": vis_bars}]))

# ════════════════════════════════════════════════
# BRANCH DROPDOWN
# ════════════════════════════════════════════════
branch_buttons = []
for branch in all_branches:
    df_b = df_result if branch == "All" else df_result.filter(F.col("BRANCH") == branch)

    # graph 1
    pdf_b1 = (df_b.groupBy("date","source_type").agg(F.sum("count").alias("cnt"))
              .toPandas().pivot(index="date", columns="source_type", values="cnt")
              .fillna(0).reset_index())
    pdf_b1["date"] = pd.to_datetime(pdf_b1["date"])   # <-- datetime
    pdf_b1 = pdf_b1.sort_values("date")
    for col in ["remarketing","third party","datacap"]:
        if col not in pdf_b1.columns: pdf_b1[col] = 0
    x1 = pdf_b1["date"].tolist()

    # graph 2
    pdf_b2 = (df_b.groupBy("date","source_type","source_type2_viz")
              .agg(F.sum("count").alias("cnt")).toPandas())
    pdf_b2["date"] = pd.to_datetime(pdf_b2["date"])   # <-- datetime
    pdf_b2 = pdf_b2.sort_values("date")
    dvals_b = pdf_b2["date"].sort_values().unique().tolist()  # <-- datetime list

    new_x, new_y = [], []
    for col in ["remarketing","third party","datacap"]:
        new_x.append(x1); new_y.append(pdf_b1[col].tolist())
    for col in ["remarketing","third party","datacap"]:
        new_x.append(x1); new_y.append(pdf_b1[col].tolist())

    for src in ["remarketing","third party","datacap"]:
        sub = (pdf_b2[pdf_b2["source_type"]==src]["source_type2_viz"]
               .dropna().unique().tolist())
        for sg in sub:
            y = [int(pdf_b2[(pdf_b2["date"] == d) &        # <-- datetime == datetime
                            (pdf_b2["source_type"]==src) &
                            (pdf_b2["source_type2_viz"]==sg)]["cnt"].sum())
                 for d in dvals_b]
            new_x.append(dvals_b); new_y.append(y)
            new_x.append(dvals_b); new_y.append(y)

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
    xaxis=dict(type="date"),           # <-- fuerza tipo date
    xaxis2=dict(type="date"),          # <-- fuerza tipo date
    legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.12),
    margin=dict(t=150, b=100, l=60, r=40),
    updatemenus=[
        dict(buttons=branch_buttons, direction="down", showactive=True,
             x=0.0, xanchor="left", y=1.13, yanchor="top",
             bgcolor="#5B6EE1", font=dict(color="white")),
        dict(buttons=buttons_g1, type="buttons", direction="right",
             showactive=True, x=0.5, xanchor="center", y=1.13, yanchor="top",
             bgcolor="#444", font=dict(color="white")),
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
