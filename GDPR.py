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

# ── Branch values ──
branch_vals = sorted([
    b for b in df_result.select("BRANCH").distinct()
    .rdd.flatMap(lambda x: x).collect() if b
])
all_branches = ["All"] + branch_vals

# ── extend palette ──
all_s2 = (df_result.select("source_type2_viz").distinct()
          .rdd.flatMap(lambda x: x).collect())
extra = qualitative.Plotly * ((len(all_s2) // len(qualitative.Plotly)) + 1)
for i, s2 in enumerate(all_s2):
    if s2 and s2 not in palette:
        palette[s2] = extra[i]

# ════════════════════════════════════════
# FIGURA ÚNICA con subplots compartiendo X
# ════════════════════════════════════════
fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=("Counts by date — source type",
                    "Counts by date — source type 2 viz"),
    vertical_spacing=0.12,
    shared_xaxes=True,       # <-- hover sincronizado entre los dos
)

traces_meta = []  # (branch, is_g1, is_line)

for branch in all_branches:
    df_b = (df_result if branch == "All"
            else df_result.filter(F.col("BRANCH") == branch))

    # ── Graph 1 ──
    pdf_type = (
        df_b.groupBy("date", "source_type")
        .agg(F.sum("count").alias("cnt"))
        .toPandas()
        .pivot(index="date", columns="source_type", values="cnt")
        .fillna(0).reset_index()
    )
    pdf_type["date"] = pd.to_datetime(pdf_type["date"])
    pdf_type = pdf_type.sort_values("date")
    for col in ["remarketing", "third party", "datacap"]:
        if col not in pdf_type.columns:
            pdf_type[col] = 0

    for col, color in [("remarketing","#636EFA"),
                       ("third party","#EF5538"),
                       ("datacap","#00CC96")]:
        # line
        fig.add_trace(go.Scatter(
            x=pdf_type["date"], y=pdf_type[col],
            name=col.title(), mode="lines+markers",
            line=dict(color=color, width=2), marker=dict(size=4),
            visible=(branch == "All"),
            legendgroup=col,
            legendgrouptitle_text="Source type" if branch == "All" else None,
            showlegend=(branch == "All"),
        ), row=1, col=1)
        traces_meta.append((branch, True, True))

        # bar
        fig.add_trace(go.Bar(
            x=pdf_type["date"], y=pdf_type[col],
            name=col.title(), marker_color=color,
            visible=False,
            legendgroup=col, showlegend=False,
        ), row=1, col=1)
        traces_meta.append((branch, True, False))

    # ── Graph 2 ──
    pdf_s2 = (
        df_b.groupBy("date", "source_type", "source_type2_viz")
        .agg(F.sum("count").alias("cnt"))
        .toPandas()
    )
    pdf_s2["date"] = pd.to_datetime(pdf_s2["date"])
    pdf_s2 = pdf_s2.sort_values("date")
    date_vals = (pdf_s2["date"].dt.strftime("%Y-%m-%d")
                 .sort_values().unique().tolist())

    for src in ["remarketing", "third party", "datacap"]:
        subs = (pdf_s2[pdf_s2["source_type"] == src]["source_type2_viz"]
                .dropna().unique().tolist())
        for sg in subs:
            yv = [
                int(pdf_s2[
                    (pdf_s2["date"].dt.strftime("%Y-%m-%d") == d) &
                    (pdf_s2["source_type"] == src) &
                    (pdf_s2["source_type2_viz"] == sg)
                ]["cnt"].sum())
                for d in date_vals
            ]
            c = palette.get(sg, palette.get(src, "#777"))
            # line
            fig.add_trace(go.Scatter(
                x=date_vals, y=yv,
                name=f"{sg} ({src})",
                mode="lines+markers",
                line=dict(width=2, color=c), marker=dict(size=4),
                visible=(branch == "All"),
                legendgroup=f"g2_{src}",
                legendgrouptitle_text=src.title() if branch == "All" else None,
                showlegend=(branch == "All"),
            ), row=2, col=1)
            traces_meta.append((branch, False, True))

            # bar
            fig.add_trace(go.Bar(
                x=date_vals, y=yv,
                name=f"{sg} ({src})",
                marker_color=c, visible=False,
                legendgroup=f"g2_{src}", showlegend=False,
            ), row=2, col=1)
            traces_meta.append((branch, False, False))

total = len(fig.data)

# ════════════════════════════════════════
# BOTONES
# ════════════════════════════════════════

# ── Branch dropdown — un solo filtro ──
branch_buttons = []
for branch in all_branches:
    vis = [
        b == branch and is_line
        for b, _, is_line in traces_meta
    ]
    branch_buttons.append(dict(
        label=branch,
        method="update",
        args=[
            {"visible": vis},
            {"title": f"Forces VIZ  ·  Branch: <b>{branch}</b>"}
        ]
    ))

# ── Graph 1: Lines / Bars ──
def g1_toggle(show_lines, active_branch="All"):
    return [
        b == active_branch and is_g1 and (is_line == show_lines)
        or (not is_g1 and b == active_branch and is_line)
        for b, is_g1, is_line in traces_meta
    ]

btns_g1 = [
    dict(label="● Lines", method="update",
         args=[{"visible": g1_toggle(True)}]),
    dict(label="▮ Bars",  method="update",
         args=[{"visible": g1_toggle(False)}]),
]

# ── Graph 2: por source_type ──
def g2_toggle(src_filter, show_lines, active_branch="All"):
    vis = []
    for b, is_g1, is_line in traces_meta:
        if b != active_branch:
            vis.append(False)
        elif is_g1:
            vis.append(is_line)          # mantiene graph1 visible
        else:
            vis.append(is_line == show_lines)
    return vis

btns_g2 = [
    dict(label="● All", method="update",
         args=[{"visible": g2_toggle("all", True)}]),
]
for src in ["remarketing", "third party", "datacap"]:
    btns_g2.append(dict(
        label=f"● {src.title()}",
        method="update",
        args=[{"visible": g2_toggle(src, True)}]
    ))
    btns_g2.append(dict(
        label=f"▮ {src.title()}",
        method="update",
        args=[{"visible": g2_toggle(src, False)}]
    ))

# ════════════════════════════════════════
# LAYOUT
# ════════════════════════════════════════
fig.update_layout(
    title=dict(
        text="Forces VIZ  ·  Branch: <b>All</b>",
        x=0.5, xanchor="center", font=dict(size=15)
    ),
    template="plotly_white",
    height=860,
    hovermode="x unified",          # <-- hover linkea los 2 subplots
    margin=dict(t=130, b=40, l=70, r=200),

    yaxis=dict(title="Count", type="log", showgrid=True, gridcolor="#f0f0f0"),
    yaxis2=dict(title="Count", type="log", showgrid=True, gridcolor="#f0f0f0"),
    xaxis=dict(showticklabels=False),
    xaxis2=dict(title="Date"),

    legend=dict(
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#e0e0e0", borderwidth=1,
        tracegroupgap=10,
        font=dict(size=11),
        x=1.01, y=1, xanchor="left",
    ),

    updatemenus=[
        # ── Branch dropdown (arriba izquierda) ──
        dict(
            buttons=branch_buttons,
            direction="down",
            showactive=True,
            x=0.0, xanchor="left",
            y=1.10, yanchor="top",
            bgcolor="#5B6EE1",
            font=dict(color="white", size=12),
            bordercolor="#4a5bc9", borderwidth=1,
        ),
        # ── G1 Lines/Bars (arriba centro-izq) ──
        dict(
            buttons=btns_g1,
            type="buttons", direction="right",
            showactive=True,
            x=0.30, xanchor="left",
            y=1.10, yanchor="top",
            bgcolor="#f0f0f0",
            activecolor="#5B6EE1",
            font=dict(size=12),
            bordercolor="#ccc", borderwidth=1,
            pad=dict(r=4, t=4, b=4),
        ),
        # ── G2 source_type (mitad de página) ──
        dict(
            buttons=btns_g2,
            type="buttons", direction="right",
            showactive=True,
            x=0.0, xanchor="left",
            y=0.44, yanchor="top",
            bgcolor="#f0f0f0",
            activecolor="#2a2a2a",
            font=dict(size=11),
            bordercolor="#ccc", borderwidth=1,
            pad=dict(r=4, t=4, b=4),
        ),
    ],
    annotations=[
        dict(text="Branch:", x=-0.02, y=1.13,
             xref="paper", yref="paper",
             showarrow=False, font=dict(size=11, color="#666")),
        dict(text="G1:", x=0.28, y=1.13,
             xref="paper", yref="paper",
             showarrow=False, font=dict(size=11, color="#666")),
    ]
)

fig.show()

# ── Export HTML ──
OUTPUT_PATH = "/Workspace/Users/TU_EMAIL@dominio.com/forces_viz.html"
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
fig.write_html(
    OUTPUT_PATH,
    include_plotlyjs="cdn",
    full_html=True,
    config={
        "scrollZoom": True,
        "displayModeBar": True,
        "toImageButtonOptions": {
            "filename": "forces_viz", "scale": 2
        }
    }
)
print(f"✅ {OUTPUT_PATH}")



#########################################################################
#########################################################################
#########################################################################
#########################################################################

