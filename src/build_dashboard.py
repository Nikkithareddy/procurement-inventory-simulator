"""Build a self-contained interactive HTML dashboard (Power BI-style views)."""
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

df = pd.read_csv("data/inventory_working_capital.csv")
slow = pd.read_csv("data/slow_moving_skus.csv")
with open("data/summary_metrics.json") as f:
    summary = json.load(f)

wc_by_cat = df.groupby("category")[["working_capital_actual_usd", "working_capital_optimal_usd"]].sum()
savings_by_cat = df.groupby("category")["potential_annual_savings"].sum().sort_values(ascending=False)

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Working Capital: Actual vs. EOQ-Optimal (by category)",
        "Potential Annual Savings by Category",
        "Top 10 Slow-Moving SKUs (lowest turnover)",
        "Actual Order Qty vs. EOQ (all SKUs)",
    ),
    specs=[[{"type": "bar"}, {"type": "bar"}],
           [{"type": "bar"}, {"type": "scatter"}]],
    vertical_spacing=0.15, horizontal_spacing=0.10,
)

fig.add_trace(go.Bar(x=wc_by_cat.index, y=wc_by_cat["working_capital_actual_usd"],
                      name="Actual", marker_color="#c96a6a"), row=1, col=1)
fig.add_trace(go.Bar(x=wc_by_cat.index, y=wc_by_cat["working_capital_optimal_usd"],
                      name="EOQ-optimal", marker_color="#2f6db5"), row=1, col=1)

fig.add_trace(go.Bar(x=savings_by_cat.index, y=savings_by_cat.values, marker_color="#4caf7d",
                      showlegend=False), row=1, col=2)

top_slow = slow.head(10)
fig.add_trace(go.Bar(x=top_slow["sku_id"], y=top_slow["inventory_turnover"], marker_color="#e0a336",
                      showlegend=False), row=2, col=1)

fig.add_trace(go.Scatter(x=df["eoq_units"], y=df["actual_avg_order_qty"], mode="markers",
                          marker=dict(size=8, color="#7a52a3", opacity=0.6),
                          text=df["sku_id"], showlegend=False), row=2, col=2)
max_ax = max(df["eoq_units"].max(), df["actual_avg_order_qty"].max())
fig.add_trace(go.Scatter(x=[0, max_ax], y=[0, max_ax], mode="lines",
                          line=dict(color="gray", dash="dash"), showlegend=False), row=2, col=2)

fig.update_layout(
    title=dict(text="Procurement Cycle & Inventory Working Capital Simulator", x=0.5, font=dict(size=20)),
    height=860, width=1180, template="plotly_white", barmode="group", margin=dict(t=90),
)
fig.update_yaxes(title_text="USD", row=1, col=1)
fig.update_yaxes(title_text="USD / year", row=1, col=2)
fig.update_yaxes(title_text="Turnover (x/year)", row=2, col=1)
fig.update_xaxes(tickangle=-35, row=2, col=1)
fig.update_xaxes(title_text="EOQ units", row=2, col=2)
fig.update_yaxes(title_text="Actual avg order qty", row=2, col=2)

kpi_html = f"""
<div style="display:flex;gap:24px;justify-content:center;font-family:Arial;margin:18px 0 6px;flex-wrap:wrap;">
  <div style="background:#eef8f0;border-radius:10px;padding:14px 22px;text-align:center;">
    <div style="font-size:24px;font-weight:700;color:#4caf7d;">${summary['total_potential_annual_savings_usd']:,.0f}</div>
    <div style="font-size:12px;color:#555;">Potential annual savings</div>
  </div>
  <div style="background:#eef4fb;border-radius:10px;padding:14px 22px;text-align:center;">
    <div style="font-size:24px;font-weight:700;color:#2f6db5;">${summary['total_working_capital_freed_usd']:,.0f}</div>
    <div style="font-size:12px;color:#555;">Working capital freed (EOQ-optimal)</div>
  </div>
  <div style="background:#fbeeee;border-radius:10px;padding:14px 22px;text-align:center;">
    <div style="font-size:24px;font-weight:700;color:#c96a6a;">{summary['slow_moving_sku_count']}</div>
    <div style="font-size:12px;color:#555;">Slow-moving SKUs ({summary['slow_moving_sku_share_pct']}%)</div>
  </div>
  <div style="background:#f5f0fb;border-radius:10px;padding:14px 22px;text-align:center;">
    <div style="font-size:24px;font-weight:700;color:#7a52a3;">{summary['total_skus_analyzed']}</div>
    <div style="font-size:12px;color:#555;">SKUs analyzed</div>
  </div>
</div>
"""

fig_html = fig.to_html(include_plotlyjs="cdn", full_html=False)
html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Procurement Cycle & Inventory Working Capital Simulator</title></head>
<body style="margin:0;background:#fafafa;">
{kpi_html}
{fig_html}
</body></html>"""

with open("dashboard/dashboard.html", "w") as f:
    f.write(html)
print("Dashboard written to dashboard/dashboard.html")
