from dash import Dash, html, dash_table, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import TnLlmTools as tnt

app = Dash()
app.title = "TN/C2X COP Analyzer"
# Requires Dash 2.17.0 or later
# First, gather summary data from TN COPs

result = tnt.query_tn("BQ24_COP", "* has *itude", 500, 0)

df = tnt.df_from_tns(result)
print(df.to_string())

fig = px.scatter_geo(
    df,
    projection="natural earth",  # "equirectangular",
    lat="latitude",
    lon="longitude",
    color="color",
    symbol="marker",
    width=1700,
    height=850,
)

fig.update_traces(marker=dict(size=10))

app.layout = html.Div(
    children=[
        html.Table(
            [
                html.Tr(
                    [
                        html.Td(
                            html.Div(
                                children="TN/C2X COP Browser/Analyzer",
                                style={
                                    "font-family": "Lato",
                                    "font-size": "24px",
                                    "font-style": "bold",
                                },
                            ),
                            style={
                                "text-align": "left",
                                "vertical-align": "middle",
                                "width": "80%",
                            },
                        ),
                        html.Td(
                            html.Img(
                                src=app.get_asset_url("c2xLogoPEO41-C.png"),
                                style={"width": "40%", "height": "40%"},
                            ),
                            style={
                                "width": "250px",
                                "height": "auto",
                                "align": "right",
                                "vertical-align": "middle",
                            },
                        ),
                    ],
                    style={"width": "100%"},
                )
            ],
            style={
                "width": "100%",
                "border": "none",
                "border-collapse": "collapse",
                "margin-bottom": "10px",
            },
        ),
        html.Hr(),
        html.Div(
            children=[dcc.Graph(id="example-graph", figure=fig)],
            style={"align": "left"},
        ),
    ]
)


if __name__ == "__main__":
    app.run(debug=True)
