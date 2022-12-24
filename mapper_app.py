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
            placeholder="Enter user ID",
        ),
        html.Button(
            "Load Object Summary",
            id="generate-places-button",
            n_clicks=0,
        ),
        html.Button(
            "Search This Area",
            id="user-info-button",
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
                    style={"flex": 1},
                ),
                html.Div(
                    html.Pre(id="os-string", style={"font-size": 15}),
                    id="user-info",
                    style={
                        "overflow": "auto",
                        "width": "500px",
                        "margin": "10px",
                    },
                ),
            ],
            style={
                "display": "flex",
                "flex-direction": "row",
                "height": "500px",
            },
        ),
        html.P(id="text-coords"),
        # Data Storage
        dcc.Store(id="place-storage"),
        dcc.Store(id="visitor-storage"),
        dcc.Store(id="last-bounds"),
    ]
)

cache = diskcache.Cache("./cache")
bcm = DiskcacheManager(cache)
app = Dash(__name__, background_callback_manager=bcm)

app.layout = layout


@app.callback(
    output=[
        (Output("selected-user", "children")),
        (Output("os-string", "children")),
        (Output("place-storage", "data")),
        (Output("visitor-storage", "data")),
        (Output("last-bounds", "data")),
    ],
    inputs=[
        (Input("generate-places-button", "n_clicks")),
        (State("map", "bounds")),
        (State("textbox-user", "value")),
    ],
    background=True,
    running=[
        (Output("user-info-button", "disabled"), True, False),
        (Output("generate-places-button", "disabled"), True, False),
    ],
)
def load_os(n_clicks, bounds, value):
    if value not in osgen.df_friends["user_id"]:
        raise PreventUpdate

    df_places, d_visitor = osgen.get_relevant_place(value)
    os_string = osgen.get_object_summary(value)

    return [
        (f"Selected user: {value}"),
        (str(os_string)),
        (df_places.reset_index().to_json(orient="split")),
        (d_visitor),
        (bounds),
    ]


@app.callback(
    output=[
        (Output("layer", "children")),
    ],
    inputs=[
        (Input("user-info-button", "n_clicks")),
        (State("map", "bounds")),
        (State("place-storage", "data")),
        (State("visitor-storage", "data")),
        (State("last-bounds", "data")),
    ],
    prevent_initial_call=True,
    running=[
        (Output("user-info-button", "disabled"), True, False),
        (Output("generate-places-button", "disabled"), True, False),
    ],
)
def display_os_on_map(
    n_clicks, current_bounds, place_data, visitor_data, last_bounds
):
    if place_data is None:
        raise PreventUpdate

    [lat1, lon1], [lat2, lon2] = current_bounds

    df_places = pd.read_json(place_data, orient="split")[
        ["place_id", "lat", "lon", "country_id"]
    ].astype(
        {
            "place_id": int,
            "lat": np.float32,
            "lon": np.float32,
            "country_id": int,
        }
    )
    df_places = df_places[
        (df_places.lat.between(lat1, lat2))
        & (df_places.lon.between(lon1, lon2))
    ]

    print(np.random.randint(0, 1000, (3, 3)))
    N = min(10, len(df_places))
    coordinates = df_places.sample(N).iloc[:, :3].to_numpy()
    points = [
        dl.Marker(position=[lat, lon], children=dl.Tooltip(f"{int(id)}"))
        for id, lat, lon in coordinates
    ]
    return [(points)]


if __name__ == "__main__":
    app.run_server(debug=True)
