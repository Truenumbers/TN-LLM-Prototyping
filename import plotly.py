import plotly.express as px
import pandas as pd

# Sample data
df = pd.DataFrame({"lat": [40, -10], "lon": [-50, 150]})

# Specify the custom tile server URL in `px.scatter_mapbox` or `px.line_mapbox`
fig = px.scatter_mapbox(
    df, lat="lat", lon="lon", zoom=1, height=500, title="OpenSeaMap Tiles"
)

# Use the OpenSeaMap tile server
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_layers=[
        {
            "below": "traces",
            "sourcetype": "raster",
            "sourceattribution": "© OpenSeaMap contributors",
            "source": ["https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png"],
        }
    ],
)

fig.show()
