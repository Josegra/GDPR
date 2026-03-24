import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.colors import qualitative
from plotly.io import to_html
import os

# ── Branch values ──
branch_vals = sorted([b for b in df_result.select("BRANCH").distinct().rdd.flatMap(lambda x: x).collect() if b])

# ── Palette ──
palette = {
    "remarketing": "#636EFA", "third party": "#EF5538", "datacap": "#00CC96",
    "Customer": "#1f77b4", "UBO": "#ff7f0e", "Representative": "#2ca02c",
    "Shareholder": "#d62728", "Director": "#9467bd", "CUS_PRIVATE": "#d62728",
    "SUPPLIER": "#9467bd", "CUS CORPORATE": "#8c564b",
}

fig = make_subplots(rows=2, cols=1,
                    subplot_titles=("Counts by Date – source_type",
                                    "Counts by Date – source_type2_viz"),
                    vertical_spacing=0.15, shared_xaxes=False)

all_branches = ["All"] + branch_vals
traces_meta = []  # (branch, row, is_line)

for branch in all_branches:
    df_b = df_result if branch == "All" else df_result.filter(F.col("BRANCH") == branch)

    # ── Graph 1 ──
    pdf_type = (df_b.groupBy("date","source_type")
                .agg(F.sum("count").alias("cnt"))
                .toPandas()
                .pivot(index="date", columns="source_type", values="cnt")
                .fillna(0).reset_index())
    pdf_type["date"] = pdf_type["date"].astype(str)
    x1 = pdf_type["date"].tolist()
    for col in ["remarketing","third party","datacap"]:
        if col not in pdf_type.columns: pdf_type[col] = 0

    for col, color in [("remarketing","#636EFA"),("third party","#EF5538"),("datacap","#00CC96")]:
        # line
        fig.add_trace(go.Scatter(x=x1, y=pdf_type[col].tolist(), name=col.title(),
                                 mode="lines+markers", line=dict(color=color),
                                 visible=(branch=="All"), legendgroup=col,
                                 showlegend=(branch=="All")), row=1, col=1)
        traces_meta.append((branch, 1, True))
        # bar
        fig.add_trace(go.Bar(x=x1, y=pdf_type[col].tolist(), name=col.title(),
                             marker_color=color, visible=False,
                             legendgroup=col, showlegend=False), row=1, col=1)
        traces_meta.append((branch, 1, False))

    # ── Graph 2 ──
    pdf_s2 = (df_b.groupBy("date","source_type","source_type2_viz")
              .agg(F.sum("count").alias("cnt")).toPandas())
    pdf_s2["date"] = pd.to_datetime(pdf_s2["date"])
    dvals = pdf_s2["date"].dt.strftime("%Y-%m-%d").sort_values().unique().tolist()

    for src in ["remarketing","third party","datacap"]:
        for sg in pdf_s2[pdf_s2["source_type"]==src]["source_type2_viz"].dropna().unique().tolist():
            y = [int(pdf_s2[(pdf_s2["date"].dt.strftime("%Y-%m-%d")==d) &
                            (pdf_s2["source_type"]==src) &
                            (pdf_s2["source_type2_viz"]==sg)]["cnt"].sum()) for d in dvals]
            color = palette.get(sg, palette.get(src, "#777777"))
            # line
            fig.add_trace(go.Scatter(x=dvals, y=y, name=f"{sg} ({src})",
                                     mode="lines+markers", line=dict(width=2, color=color),
                                     visible=(branch=="All"), legendgroup=f"{sg}_{src}",
                                     showlegend=(branch=="All")), row=2, col=1)
            traces_meta.append((branch, 2, True))
            # bar
            fig.add_trace(go.Bar(x=dvals, y=y, name=f"{sg} ({src})",
                                 marker_color=color, visible=False,
                                 legendgroup=f"{sg}_{src}", showlegend=False), row=2, col=1)
            traces_meta.append((branch, 2, False))

total = len(traces_meta)

# ── Branch buttons ──
branch_buttons = []
for branch in all_branches:
    vis = []
    for i, (b, row, is_line) in enumerate(traces_meta):
        vis.append(b == branch and is_line)
    branch_buttons.append(dict(label=branch, method="update",
                               args=[{"visible": vis},
                                     {"title": f"Forces VIZ | Branch: <b>{branch}</b>"}]))

# ── Lines/Bars buttons ──
def toggle(show_lines):
    return [is_line == show_lines and fig.data[i].visible != False
            if True else False for i, (_,_,is_line) in enumerate(traces_meta)]

# simpler toggle using current active branch (All by default)
def vis_toggle(show_lines, active="All"):
    return [b == active and (is_line if show_lines else not is_line)
            for b, _, is_line in traces_meta]

line_bar_buttons = [
    dict(label="Lines", method="update", args=[{"visible": vis_toggle(True)}]),
    dict(label="Bars",  method="update", args=[{"visible": vis_toggle(False)}]),
]

# ── Layout ──
fig.update_layout(
    title=dict(text="Forces VIZ | Branch: <b>All</b>", x=0.5, xanchor="center"),
    template="plotly_white",
    hovermode="x unified",
    height=900,
    yaxis_type="log", yaxis2_type="log",
    legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.12),
    margin=dict(t=130, b=100, l=60, r=40),
    updatemenus=[
        dict(buttons=branch_buttons, direction="down", showactive=True,
             x=0.0, xanchor="left", y=1.12, yanchor="top",
             bgcolor="#5B6EE1", font=dict(color="white")),
        dict(buttons=line_bar_buttons, type="buttons", direction="right",
             showactive=True, x=0.5, xanchor="center", y=1.12, yanchor="top",
             bgcolor="#444", font=dict(color="white")),
    ],
    annotations=[
        dict(text="<b>Branch:</b>", x=0.0, y=1.15,
             xref="paper", yref="paper", showarrow=False),
    ]
)

fig.show()

# ── Export HTML ──
OUTPUT_PATH = "/Workspace/Users/TU_EMAIL@dominio.com/forces_viz.html"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
fig.write_html(OUTPUT_PATH, include_plotlyjs="cdn", full_html=True,
               config={"scrollZoom": True})
print(f"✅ {OUTPUT_PATH}")
