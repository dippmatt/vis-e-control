from dash import Dash, dcc, html, Input, Output
import plotly.express as px
from pathlib import Path

from anlagenregister import Anlagenregister

this_file = Path(__file__).parent.resolve()
dataset = this_file / Path("..", "dataset")
anlagenregister = Anlagenregister(dataset)

photovoltaic_data = anlagenregister.photovoltaic_production_by_gcd
map_geojson = anlagenregister.gemeinden_austria_geojson
color_threshold = 0
for year in ["2024", "2023", "2022", "2021", "2020", "2019"]:
    #value = photovoltaic_data[f"Eingespeister Strom (kWh) {year}"].quantile(0.9)
    value = photovoltaic_data[f"Eingespeister Strom (kWh) {year}"].max()
    if value > color_threshold:
        color_threshold = value

app = Dash(__name__)

# create a dash app
# visit http://127.0.0.1:8050/ to view the app

app.layout = html.Div([
    html.H4('Photovoltaic production in kWh in Austria by Gemeinde'),
    html.P("Select a year:"),
    dcc.RadioItems(
        id='year', 
        options=["Eingespeister Strom (kWh) 2024", 
                 "Eingespeister Strom (kWh) 2023", 
                 "Eingespeister Strom (kWh) 2022", 
                 "Eingespeister Strom (kWh) 2021", 
                 "Eingespeister Strom (kWh) 2020", 
                 "Eingespeister Strom (kWh) 2019"],
        value="Eingespeister Strom (kWh) 2024",
        inline=True
    ),
    dcc.Graph(id="graph"),
    html.Br(),
    html.Label('Max Color threshold [GWh]:'),
    dcc.Slider(
        id='threshold', 
        min=0,
        max=int(color_threshold * 1.1 / 1000000),
        marks={i: f'{i * 2}' for i in range(1, int(color_threshold * 1.1 / 1000000 / 2))},
        value=5,
    ),
])


@app.callback(
    Output("graph", "figure"), 
    Input("year", "value"),
    Input("threshold", "value"))
def display_choropleth(year, threshold):
    df = photovoltaic_data
    geojson = map_geojson

    fig = px.choropleth_mapbox(
        df, geojson=geojson, color=year,
        color_continuous_scale="Viridis",
        locations="gcd",
        center={"lat": 47.69, "lon": 13.34}, zoom=6,
        mapbox_style="open-street-map",
        range_color=[0, threshold*1000000],
        opacity=0.5,
        labels={year: "Energy produced in kWh"})
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return fig


app.run_server(debug=True)