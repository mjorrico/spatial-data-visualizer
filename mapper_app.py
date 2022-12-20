from dash import Dash, dcc, html, Input, Output, State, DiskcacheManager
from dash.exceptions import PreventUpdate
import dash_leaflet as dl
import diskcache
import pandas as pd
import numpy as np
from osgenerator import OSGenerator
import json

from time import sleep

osgen = OSGenerator()
osgen.read_from_file(
    "data/friends.csv",
    "data/checkins.csv",
    "data/places.csv",
    "data/countries.csv",
)

layout = html.Div(
    [
        dcc.Input(
            id="textbox-user",
            type="number",
            # placeholder="Enter user ID",
        ),
        html.Button(
            "Load Object Summary",
            id="generate-places-button",
            n_clicks=0,
        ),
        html.Button(
            "Cancel Search",
            id="cancel-generate-button",
            n_clicks=0,
        ),
        html.Button(
            "Show user info",
            id="user-info-button",
            n_clicks=0,
        ),
        html.Button(
            "Show on map",
            id="map-button",
            n_clicks=0,
        ),
        html.Br(),
        html.P(
            id="selected-user",
            children=f"Selected user: N/A",
        ),
        html.Br(),
        html.Div(
            [
                dl.Map(
                    [dl.TileLayer(), dl.LayerGroup(id="layer")],
                    id="map",
                    style={"width": "600px", "height": "400px", "flex": 1},
                ),
                html.Div(
                    html.Pre(id="os-string"),
                    id="user-info",
                    style={"flex": 1, "overflow": "auto"},
                ),
            ],
            style={"display": "flex", "flex-direction": "row"},
        ),
        html.P(id="text-coords"),
        # Data Storage
        dcc.Store(id="place-storage"),
    ]
)

cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)
app = Dash(__name__, background_callback_manager=background_callback_manager)

app.layout = layout


@app.callback(
    output=[
        (Output("place-storage", "data")),
        (Output("selected-user", "children")),
        (Output("os-string", "children")),
    ],
    inputs=[
        (Input("generate-places-button", "n_clicks")),
        (State("textbox-user", "value")),
    ],
    background=True,
    running=[
        (Output("user-info-button", "disabled"), True, False),
    ],
)
def load_os(n_clicks, value):
    if value not in osgen.df_friends["user_id"]:
        raise PreventUpdate
    places = osgen.get_relevant_place(value)
    # os_string = osgen.get_object_summary(value)
    os_string = "a"
    return [
        (places.reset_index().to_json(orient="split")),
        (f"Selected user: {value}"),
        (str(os_string)),
    ]


@app.callback(
    output=[
        (Output("layer", "children")),
    ],
    inputs=[
        Input("user-info-button", "n_clicks"),
        State("place-storage", "data"),
        State("map", "bounds"),
    ],
    prevent_initial_call=True,
    background=True,
    running=[
        (Output("user-info-button", "disabled"), True, False),
    ],
)
def display_os_on_map(n_clicks, data, bounds):
    if data is None:
        raise PreventUpdate
    [lat1, lon1], [lat2, lon2] = bounds
    df_places = pd.read_json(data, orient="split")[
        ["place_id", "lat", "lon", "country_id"]
    ].astype(
        {
            "place_id": int,
            "lat": np.float32,
            "lon": np.float32,
            "country_id": int,
        }
    )
    coordinates = df_places.iloc[:, :3].to_numpy()
    points = [
        dl.Marker(position=[lat, lon], children=dl.Tooltip(f"{int(id)}"))
        for id, lat, lon in coordinates
    ]
    return [(points)]


@app.callback(Output("text-coords", "children"), Input("map", "bounds"))
def log_bounds(bounds):
    return json.dumps(bounds)


if __name__ == "__main__":
    app.run_server(debug=True)
