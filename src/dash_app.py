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

# Use the following function when accessing the value of 'my-slider'
# in callbacks to transform the output value to logarithmic
def transform_value(value):
    return 10 ** value

app.layout = html.Div([
    html.H1('Austrian photovoltaic energy production in kWh by Gemeinde', style={"font-family": "Arial"}),
    html.H3("Select a year:", style={"font-family": "Arial"}),
    dcc.RadioItems(
        id='year', 
        options=["2024", 
                 "2023", 
                 "2022", 
                 "2021", 
                 "2020", 
                 "2019"],
        value="2023",
        inline=True,
        style={"font-family": "Arial"}
    ),
    html.Br(),
    dcc.Graph(id="graph"),
    html.Br(),
    html.H3('Color scale range [GWh]:', style={"font-family": "Arial"}),
    dcc.Slider(
        id='threshold', 
        min=0,
        max=int(color_threshold * 1.1 / 1000000),
        step=int(color_threshold * 1.1 / 1000000) / 10,
        #marks={i: '{}'.format(10 ** i) for i in range(10)},
        #marks={i: str(i) for i in range(0, int(color_threshold * 1.1 / 1000000), 1)},        
        value=5,
    ),
    #html.P("Source:", style={"font-family": "Arial"}),
    html.A("Source: Anlagenregister E-Control", href='https://anlagenregister.at/', target="_blank")
])


@app.callback(
    Output("graph", "figure"), 
    Input("year", "value"),
    Input("threshold", "value"))
def display_choropleth(year, threshold):
    df = photovoltaic_data
    geojson = map_geojson
    year_key = "Eingespeister Strom (kWh) " + year

    fig = px.choropleth_mapbox(
        df, geojson=geojson, color=year_key,
        color_continuous_scale="Viridis",
        locations="gcd",
        center={"lat": 47.69, "lon": 13.34}, zoom=6,
        mapbox_style="open-street-map",
        #range_color=[0, transform_value(threshold*1000000)],
        range_color=[0, threshold*1000000],
        opacity=0.5,
        labels={year_key: "kWh"},
        hover_data={"Gemeindename": True, "PLZ": True, year_key: True})
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    # also add the label for "Gemeindename"
    

    return fig


app.run_server(debug=True)