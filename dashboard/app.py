import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

def load_data():
    scores = pd.read_sql("SELECT * FROM protocol_risk_scores WHERE tvl IS NOT NULL ORDER BY tvl DESC LIMIT 100", engine)
    anomalies = pd.read_sql("SELECT * FROM anomaly_alerts LIMIT 50", engine)
    scores["tvl_billions"] = (scores["tvl"] / 1e9).round(3)
    scores["tvl_display"] = scores["tvl"].apply(lambda x: f"${x/1e9:.2f}B" if x >= 1e9 else f"${x/1e6:.1f}M")
    return scores, anomalies

scores, anomalies = load_data()

CARD_STYLE = {
    "background": "#0d1117",
    "border": "1px solid #21262d",
    "borderRadius": "8px",
    "padding": "20px",
    "marginBottom": "20px"
}

HEADER_STYLE = {
    "background": "linear-gradient(135deg, #0d1117 0%, #161b22 100%)",
    "borderBottom": "1px solid #21262d",
    "padding": "20px 30px",
    "marginBottom": "30px"
}

app.layout = html.Div(style={"background": "#010409", "minHeight": "100vh", "fontFamily": "Inter, sans-serif"}, children=[

    # Header
    html.Div(style=HEADER_STYLE, children=[
        html.Div(style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"}, children=[
            html.Div(children=[
                html.H1("ARGUS", style={"color": "#58a6ff", "margin": 0, "fontSize": "28px", "fontWeight": "700", "letterSpacing": "4px"}),
                html.P("DeFi Risk Intelligence Platform", style={"color": "#8b949e", "margin": 0, "fontSize": "13px", "letterSpacing": "1px"})
            ]),
            html.Div(style={"display": "flex", "gap": "30px"}, children=[
                html.Div(style={"textAlign": "center"}, children=[
                    html.P(f"{len(scores)}", style={"color": "#58a6ff", "margin": 0, "fontSize": "24px", "fontWeight": "700"}),
                    html.P("Protocols Tracked", style={"color": "#8b949e", "margin": 0, "fontSize": "11px"})
                ]),
                html.Div(style={"textAlign": "center"}, children=[
                    html.P(f"{len(anomalies)}", style={"color": "#f85149", "margin": 0, "fontSize": "24px", "fontWeight": "700"}),
                    html.P("Active Alerts", style={"color": "#8b949e", "margin": 0, "fontSize": "11px"})
                ]),
                html.Div(style={"textAlign": "center"}, children=[
                    html.P(f"{scores['risk_score'].mean():.0f}", style={"color": "#3fb950", "margin": 0, "fontSize": "24px", "fontWeight": "700"}),
                    html.P("Avg Risk Score", style={"color": "#8b949e", "margin": 0, "fontSize": "11px"})
                ]),
            ])
        ])
    ]),

    html.Div(style={"padding": "0 30px"}, children=[

        # Risk Score Table + Scatter Plot
        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "marginBottom": "20px"}, children=[

            # Protocol Table
            html.Div(style=CARD_STYLE, children=[
                html.H3("Protocol Risk Scores", style={"color": "#e6edf3", "margin": "0 0 15px 0", "fontSize": "16px", "fontWeight": "600"}),
                html.P("Click a row to inspect", style={"color": "#8b949e", "fontSize": "12px", "margin": "0 0 15px 0"}),
                dash_table.DataTable(
                    id="protocol-table",
                    columns=[
                        {"name": "Protocol", "id": "name"},
                        {"name": "TVL", "id": "tvl_display"},
                        {"name": "7d %", "id": "change_7d", "type": "numeric", "format": {"specifier": ".1f"}},
                        {"name": "Risk Score", "id": "risk_score", "type": "numeric", "format": {"specifier": ".0f"}},
                    ],
                    data=scores[["name", "tvl_display", "change_7d", "risk_score"]].to_dict("records"),
                    row_selectable="single",
                    style_table={"height": "400px", "overflowY": "auto"},
                    style_header={"backgroundColor": "#161b22", "color": "#8b949e", "border": "1px solid #21262d", "fontWeight": "600", "fontSize": "12px"},
                    style_cell={"backgroundColor": "#0d1117", "color": "#e6edf3", "border": "1px solid #21262d", "fontSize": "13px", "padding": "10px"},
                    style_data_conditional=[
                        {"if": {"filter_query": "{risk_score} >= 80"}, "color": "#3fb950"},
                        {"if": {"filter_query": "{risk_score} >= 50 && {risk_score} < 80"}, "color": "#d29922"},
                        {"if": {"filter_query": "{risk_score} < 50"}, "color": "#f85149"},
                        {"if": {"state": "selected"}, "backgroundColor": "#1f2937", "border": "1px solid #58a6ff"},
                    ],
                    page_action="none",
                )
            ]),

            # Scatter Plot
            html.Div(style=CARD_STYLE, children=[
                html.H3("Risk vs TVL", style={"color": "#e6edf3", "margin": "0 0 15px 0", "fontSize": "16px", "fontWeight": "600"}),
                html.P("Bubble size = TVL. Top right = safest & largest", style={"color": "#8b949e", "fontSize": "12px", "margin": "0 0 15px 0"}),
                dcc.Graph(
                    id="scatter-plot",
                    figure=px.scatter(
                        scores.head(50),
                        x="risk_score",
                        y="tvl_billions",
                        hover_name="name",
                        size="tvl_billions",
                        color="risk_score",
                        color_continuous_scale=["#f85149", "#d29922", "#3fb950"],
                        labels={"risk_score": "Risk Score", "tvl_billions": "TVL (Billions USD)"},
                        size_max=40
                    ).update_layout(
                        paper_bgcolor="#0d1117",
                        plot_bgcolor="#0d1117",
                        font_color="#e6edf3",
                        coloraxis_showscale=False,
                        margin=dict(l=10, r=10, t=10, b=10),
                        xaxis=dict(gridcolor="#21262d", zerolinecolor="#21262d"),
                        yaxis=dict(gridcolor="#21262d", zerolinecolor="#21262d"),
                        height=400
                    ),
                    config={"displayModeBar": False}
                )
            ]),
        ]),

        # Protocol Detail Card
        html.Div(id="protocol-detail", style={"display": "none"}, children=[
            html.Div(style={**CARD_STYLE, "borderColor": "#58a6ff"}, children=[
                html.H3("Protocol Detail", style={"color": "#58a6ff", "margin": "0 0 15px 0", "fontSize": "16px", "fontWeight": "600"}),
                html.Div(id="detail-content")
            ])
        ]),

        # TVL Bar Chart
        html.Div(style=CARD_STYLE, children=[
            html.H3("Top 20 Protocols by TVL", style={"color": "#e6edf3", "margin": "0 0 15px 0", "fontSize": "16px", "fontWeight": "600"}),
            dcc.Graph(
                figure=go.Figure(
                    data=[go.Bar(
                        x=scores.head(20)["name"],
                        y=scores.head(20)["tvl_billions"],
                        marker_color=scores.head(20)["risk_score"].apply(
                            lambda x: "#3fb950" if x >= 80 else "#d29922" if x >= 50 else "#f85149"
                        ),
                        hovertemplate="<b>%{x}</b><br>TVL: $%{y:.2f}B<extra></extra>"
                    )]
                ).update_layout(
                    paper_bgcolor="#0d1117",
                    plot_bgcolor="#0d1117",
                    font_color="#e6edf3",
                    margin=dict(l=10, r=10, t=10, b=100),
                    xaxis=dict(gridcolor="#21262d", tickangle=-45),
                    yaxis=dict(gridcolor="#21262d", title="TVL (Billions USD)"),
                    height=350,
                    showlegend=False
                ),
                config={"displayModeBar": False}
            )
        ]),

        # Anomaly Alerts
        html.Div(style=CARD_STYLE, children=[
            html.H3("Live Anomaly Alerts", style={"color": "#f85149", "margin": "0 0 15px 0", "fontSize": "16px", "fontWeight": "600"}),
            html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)", "gap": "12px"}, children=[
                html.Div(
                    style={
                        "background": "#161b22",
                        "border": f"1px solid {'#f85149' if 'CRITICAL' in str(row.get('alert_type','')) else '#d29922' if 'WARNING' in str(row.get('alert_type','')) else '#58a6ff'}",
                        "borderRadius": "6px",
                        "padding": "14px"
                    },
                    children=[
                        html.P(row["name"], style={"color": "#e6edf3", "margin": "0 0 6px 0", "fontWeight": "600", "fontSize": "13px"}),
                        html.P(row["alert_type"], style={
                            "margin": "0 0 8px 0",
                            "fontSize": "11px",
                            "color": "#f85149" if "CRITICAL" in str(row.get("alert_type","")) else "#d29922" if "WARNING" in str(row.get("alert_type","")) else "#58a6ff"
                        }),
                        html.Div(style={"display": "flex", "gap": "12px"}, children=[
                            html.P(f"1d: {row['change_1d']:.1f}%" if row['change_1d'] else "1d: N/A",
                                   style={"color": "#8b949e", "margin": 0, "fontSize": "11px"}),
                            html.P(f"7d: {row['change_7d']:.1f}%" if row['change_7d'] else "7d: N/A",
                                   style={"color": "#8b949e", "margin": 0, "fontSize": "11px"}),
                        ])
                    ]
                ) for _, row in anomalies.head(12).iterrows()
            ])
        ]),
    ]),
])

@app.callback(
    Output("protocol-detail", "style"),
    Output("detail-content", "children"),
    Input("protocol-table", "selected_rows")
)
def show_detail(selected_rows):
    if not selected_rows:
        return {"display": "none"}, []
    
    row = scores.iloc[selected_rows[0]]
    
    score = row["risk_score"]
    color = "#3fb950" if score >= 80 else "#d29922" if score >= 50 else "#f85149"
    label = "SAFE" if score >= 80 else "MODERATE" if score >= 50 else "RISKY"
    
    content = html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(4, 1fr)", "gap": "20px"}, children=[
        html.Div(children=[
            html.P("Protocol", style={"color": "#8b949e", "margin": "0 0 4px 0", "fontSize": "12px"}),
            html.P(row["name"], style={"color": "#e6edf3", "margin": 0, "fontWeight": "600"})
        ]),
        html.Div(children=[
            html.P("TVL", style={"color": "#8b949e", "margin": "0 0 4px 0", "fontSize": "12px"}),
            html.P(row["tvl_display"], style={"color": "#e6edf3", "margin": 0, "fontWeight": "600"})
        ]),
        html.Div(children=[
            html.P("7 Day Change", style={"color": "#8b949e", "margin": "0 0 4px 0", "fontSize": "12px"}),
            html.P(f"{row['change_7d']:.1f}%" if row['change_7d'] else "N/A",
                   style={"color": "#3fb950" if row['change_7d'] and row['change_7d'] > 0 else "#f85149", "margin": 0, "fontWeight": "600"})
        ]),
        html.Div(children=[
            html.P("Risk Score", style={"color": "#8b949e", "margin": "0 0 4px 0", "fontSize": "12px"}),
            html.P(f"{score:.0f} — {label}", style={"color": color, "margin": 0, "fontWeight": "700", "fontSize": "18px"})
        ]),
    ])
    
    return {"display": "block", "marginBottom": "20px"}, content

if __name__ == "__main__":
    app.run(debug=True)