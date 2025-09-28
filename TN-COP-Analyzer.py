from dash import Dash, html, dash_table, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
import TnLlmTools

app = Dash()
app.title = "TN/C2X COP Analyzer"
# Requires Dash 2.17.0 or later
# First, gether summary data from TN COPs


df = None
fig = px.scatter_geo(
    df,
    locations="iso_alpha",
    size="pop",
    projection="equirectangular",
    width=1700,
    height=850,
)

app.layout = html.Div(
    children=[
        html.Div(
            [
                dash_table.DataTable(
                    id="table",
                    columns=[{"name": col, "id": col} for col in df.columns],
                    data=df.to_dict("records"),
                    style_table={
                        "overflowX": "auto"
                    },  # Horizontal scroll for wide tables
                    style_cell={"textAlign": "left"},  # Align text to the left
                )
            ]
        ),
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
