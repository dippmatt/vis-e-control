import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as np
import json
import subprocess

# Load your GeoJSON data (replace 'austria_districts.geojson' with your filename)
this_file = Path(__file__).parent.resolve()
austria_simplifyed = this_file / Path("..", "third_party", "GeoJSON-TopoJSON-Austria", "2021", "simplified-99.5", "gemeinden_995_geo.json")


with open(austria_simplifyed) as f:
    polygons = json.load(f)

#number of districts
print(len(polygons['features']))

for i, elem in enumerate(polygons['features']):
    elem["id"] = elem['properties']['iso']

# create a df with the ids and a random value between 0 and 10
df = pd.DataFrame({
    "fips": [elem['id'] for elem in polygons['features']],
    "unemp": np.random.randint(0, 10, len(polygons['features']))
    })


fig = px.choropleth_mapbox(df, geojson=polygons, locations='fips', color='unemp',
                           color_continuous_scale="Viridis",
                           range_color=(0, 12),
                           mapbox_style="carto-positron",
                           zoom=3, center = {"lat": 37.0902, "lon": -95.7129},
                           opacity=0.5,
                           labels={'unemp':'unemployment rate'}
                          )
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()

import sys; sys.exit(0)

# create a DataFrame to randomply color the districts
# The geometry is stored in the polygons['features'][i]['geometry'] key
# The district name is stored in the polygons['features'][i]['properties']['name'] key
# Now craete a DataFrame with the district names and random values

districts = pd.DataFrame({
    "properties.DISTRICT": [elem['properties']['name'] for elem in polygons['features']],
    "properties.VALUE": np.random.randint(0, 100, len(polygons['features'])),
    "geojson": polygons['features']
})

# Assuming a 'DISTRICT' (or similar) column with district names in your GeoJSON data
fig = px.choropleth(districts, locations="properties.DISTRICT", color="properties.DISTRICT",
                   geojson=districts.geojson, scope="europe", title="Austria Districts")
fig.show()
import sys; sys.exit(0)
fig = px.choropleth(geojson=polygons)
fig.show()