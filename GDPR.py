import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.colors import qualitative
import os

# ════════════════════════════════════════════════
# PALETTE
# ════════════════════════════════════════════════
palette = {
    "remarketing":          "#636EFA",
    "third party":          "#EF5538",
    "datacap":              "#00CC96",
    "Customer":             "#1f77b4",
    "UBO":                  "#ff7f0e",
    "Representative":       "#2ca02c",
    "Shareholder":          "#d62728",
    "Director":             "#9467bd",
    "CUS_PRIVATE":          "#e377c2",
    "SUPPLIER":             "#7f7f7f",
    "CUS CORPORATE":        "#8c564b",
    "Remarketing Dealer":   "#bcbd22",
    "Legal Representative": "#17becf",
    "other third parties":  "#aec7e8",
}

all_s2 = (df_result.select("source_type2_viz").distinct()
          .rdd.flatMap(lambda x: x).collect())
extra_colors = qualitative.Plotly * ((len(all_s2) // len(qualitative.Plotly)) + 1)
for i, s2 in enumerate(all_s2):
    if s2 and s2 not in palette:
        palette[s2] = extra_colors[i]

# ════════════════════════════════════════════════
# BRANCH VALUES
# ════════════════════════════════════════════════
branch_vals  = sorted([b for b in df_result.select("BRANCH").distinct()
                       .rdd.flatMap(lambda x: x).collect() if b])
all_branches = ["All"] + branch_vals

# ════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════
def get_pdf_type(data):
    pdf = (data.groupBy("date", "source_type")
               .agg(F.sum("count").alias("cnt"))
               .toPandas())
    pdf["date"] = pd.to_datetime(pdf["date"])
    pdf = (pdf.pivot(index="date", columns="source_type", values="cnt")
              .fillna(0).reset_index()
              .sort_values("date"))
    for col in ["remarketing", "third party", "datacap"]:
        if col not in pdf.columns:
            pdf[col] = 0
    return pdf

def get_pdf_s2(data):
    pdf = (data.groupBy("date", "source_type", "source_type2_viz")
               .agg(F.sum("count").alias("cnt"))
               .toPandas())
    pdf["date"] = pd.to_datetime(pdf["date"])
    pdf = pdf[pdf["source_type2_viz"].notna()]
    pdf = pdf.sort_values("date").reset_index(drop=True)
    return pdf

# FIX: pd.Timestamp para el lookup, sin sorted()
def get_y_s2(pdf, src, sg, date_vals):
    sub = pdf[
        (pdf["source_type"] == src) &
        (pdf["source_type2_viz"] == sg)
    ][["date", "cnt"]].copy()
    sub = sub.groupby("date")["cnt"].sum()
    return [int(sub.get(pd.Timestamp(d), 0)) for d in date_vals]

# ════════════════════════════════════════════════
# PRECOMPUTA "ALL"
# ════════════════════════════════════════════════
pdf_type_all  = get_pdf_type(df_result)
pdf_s2_all    = get_pdf_s2(df_result)
x_dates_all   = pdf_type_all["date"].tolist()
# FIX: sin sorted(), mantiene Timestamps
date_vals_all = pdf_s2_all["date"].sort_values().unique().tolist()

# ════════════════════════════════════════════════
# FIGURA
# ════════════════════════════════════════════════
fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=("Counts by Date – summed per source_type",
                    "Counts by Date – summed per source_type2_viz"),
    vertical_spacing=0.18,
    shared_xaxes=True,
)

# ── GRAPH 1: lines ──
for col, color in [("remarketing","#636EFA"),
                   ("third party","#EF5538"),
                   ("datacap","#00CC96")]:
    fig.add_trace(go.Scatter(
        x=x_dates_all, y=pdf_type_all[col].tolist(),
        name=col.title(), mode="lines+markers",
        line=dict(color=color, width=2), marker=dict(size=4),
        visible=True, legendgroup=col,
    ), row=1, col=1)

# ── GRAPH 1: bars ──
for col, color in [("remarketing","#636EFA"),
                   ("third party","#EF5538"),
                   ("datacap","#00CC96")]:
    fig.add_trace(go.Bar(
        x=x_dates_all, y=pdf_type_all[col].tolist(),
        name=col.title(), marker_color=color,
        visible=False, legendgroup=col, showlegend=False,
    ), row=1, col=1)

n1 = 3  # traces 0-2 lines | traces 3-5 bars

# ── GRAPH 2: lines + bars ──
traces_line_g2 = []
traces_bar_g2  = []
g2_structure   = []

for src in ["remarketing", "third party", "datacap"]:
    subs = (pdf_s2_all[pdf_s2_all["source_type"] == src]["source_type2_viz"]
            .dropna().unique().tolist())
    for sg in subs:
        y_vals = get_y_s2(pdf_s2_all, src, sg, date_vals_all)
        color  = palette.get(sg, palette.get(src, "#777777"))

        fig.add_trace(go.Scatter(
            x=date_vals_all, y=y_vals,
            name=f"{sg} ({src})", mode="lines+markers",
            line=dict(width=2, color=color), marker=dict(size=4),
            visible=False, legendgroup=sg, showlegend=True,
        ), row=2, col=1)
        traces_line_g2.append(len(fig.data) - 1)
        g2_structure.append((src, sg))

        fig.add_trace(go.Bar(
            x=date_vals_all, y=y_vals,
            name=f"{sg} ({src})", marker_color=color,
            visible=False, legendgroup=sg, showlegend=False,
        ), row=2, col=1)
        traces_bar_g2.append(len(fig.data) - 1)

total = len(fig.data)

# ════════════════════════════════════════════════
# ESTADO INICIAL
# ════════════════════════════════════════════════
for i in range(n1):
    fig.data[i].visible = True
for i in range(n1, n1 * 2):
    fig.data[i].visible = False
for i, (src, sg) in enumerate(g2_structure):
    if src == "remarketing":
        fig.data[traces_line_g2[i]].visible = True

# ════════════════════════════════════════════════
# BUTTONS G1
# ════════════════════════════════════════════════
def make_vis_g1(show_lines):
    vis = [False] * total
    for i in range(n1):
        vis[i]      = show_lines
        vis[i + n1] = not show_lines
    for i, (src, sg) in enumerate(g2_structure):
        if src == "remarketing":
            vis[traces_line_g2[i]] = True
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
    line_idx = [traces_line_g2[i] for i, (s, _) in enumerate(g2_structure) if s == src]
    bar_idx  = [traces_bar_g2[i]  for i, (s, _) in enumerate(g2_structure) if s == src]

    vis_lines = [False] * total
    for i in range(n1):  vis_lines[i]      = True
    for i in range(n1):  vis_lines[i + n1] = False
    for i in line_idx:   vis_lines[i]      = True
    buttons_g2.append(dict(label=f"{src.title()} Lines",
                           method="update", args=[{"visible": vis_lines}]))

    vis_bars = [False] * total
    for i in range(n1):  vis_bars[i]      = True
    for i in range(n1):  vis_bars[i + n1] = False
    for i in bar_idx:    vis_bars[i]      = True
    buttons_g2.append(dict(label=f"{src.title()} Bars",
                           method="update", args=[{"visible": vis_bars}]))

# ════════════════════════════════════════════════
# BRANCH DROPDOWN
# ════════════════════════════════════════════════
branch_buttons = []
for branch in all_branches:
    df_b    = df_result if branch == "All" else df_result.filter(F.col("BRANCH") == branch)
    pdf_b1  = get_pdf_type(df_b)
    pdf_b2  = get_pdf_s2(df_b)
    x1      = pdf_b1["date"].tolist()
    dvals_b = pdf_b2["date"].sort_values().unique().tolist()  # sin sorted()

    new_x, new_y = [], []

    for col in ["remarketing", "third party", "datacap"]:
        new_x.append(x1); new_y.append(pdf_b1[col].tolist())
    for col in ["remarketing", "third party", "datacap"]:
        new_x.append(x1); new_y.append(pdf_b1[col].tolist())

    for src, sg in g2_structure:
        y = get_y_s2(pdf_b2, src, sg, dvals_b)
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
    yaxis=dict( title="Count", type="log", showgrid=True, gridcolor="#f0f0f0"),
    yaxis2=dict(title="Count", type="log", showgrid=True, gridcolor="#f0f0f0"),
    xaxis=dict( type="date", showticklabels=False),
    xaxis2=dict(type="date", title="Date"),
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

# ════════════════════════════════════════════════
# EXPORT
# ════════════════════════════════════════════════
OUTPUT_PATH = "/Workspace/Users/TU_EMAIL@dominio.com/forces_viz.html"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
fig.write_html(OUTPUT_PATH, include_plotlyjs="cdn", full_html=True,
               config={"scrollZoom": True})
print(f"✅ Exportado: {OUTPUT_PATH}")
