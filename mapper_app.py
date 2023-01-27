from dash import Dash, dcc, html, Input, Output, State, DiskcacheManager
from dash.exceptions import PreventUpdate
import dash_leaflet as dl
import diskcache
import pandas as pd
import numpy as np
from osgenerator import OSGenerator
from object_selection import isos, random_selection

from time import time

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
            id="load-os-button",
            n_clicks=0,
        ),
        html.Button(
            "Search This Area",
            id="show-places-button",
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
        dcc.Store(id="last-bounds-storage", data=[[0, 0], [1, 1]]),
        dcc.Store(id="last-unselected-objects", data=[]),
        dcc.Store(id="last-selected-objects", data=[]),
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
    ],
    inputs=[
        (Input("load-os-button", "n_clicks")),
        (State("textbox-user", "value")),
    ],
    background=True,
    running=[
        (Output("show-places-button", "disabled"), True, False),
        (Output("load-os-button", "disabled"), True, False),
    ],
)
def load_os(n_clicks, value):
    if value not in osgen.df_friends["user_id"]:
        raise PreventUpdate

    df_places, d_visitor = osgen.get_relevant_place(value, True)
    os_string = osgen.get_object_summary(value)

    return [
        (f"Selected user: {value}"),
        (str(os_string)),
        (df_places.reset_index().to_json(orient="split")),
        (d_visitor),
    ]


@app.callback(
    output=[
        (Output("layer", "children")),
        (Output("last-bounds-storage", "data")),
        (Output("last-selected-objects", "data")),
        (Output("last-unselected-objects", "data")),
    ],
    inputs=[
        (Input("show-places-button", "n_clicks")),
        (State("map", "bounds")),
        (State("place-storage", "data")),
        (State("visitor-storage", "data")),
        (State("last-bounds-storage", "data")),
        (State("last-selected-objects", "data")),
        (State("last-unselected-objects", "data")),
    ],
    prevent_initial_call=True,
    running=[
        (Output("show-places-button", "disabled"), True, False),
        (Output("load-os-button", "disabled"), True, False),
    ],
)
def display_os_on_map(
    n_clicks,
    current_bounds,
    place_data,
    visitor_data,
    last_bounds,
    displayed_objs,
    undisplayed_objs,
):
    start = time()
    print(f"displayed places: {displayed_objs}")
    print(f"# hidden places: {len(undisplayed_objs)}")

    if place_data is None:
        raise PreventUpdate

    visitor_data = {int(k): visitor_data[k] for k in visitor_data.keys()}

    df_places = (
        pd.read_json(place_data, orient="split")
        .iloc[:, 1:]
        .astype(
            {
                "place_id": int,
                "lat": np.float32,
                "lon": np.float32,
                "country_id": int,
                "is_direct": int,
                "weight": np.float32,
            }
        )
    )

    start = time()
    new_selected, new_unselected = isos(
        df_places,
        visitor_data,
        last_bounds,
        current_bounds,
        10,
        displayed_objs,
        undisplayed_objs,
    )

    points = [
        dl.Marker(
            position=[lat, lon],
            children=dl.Tooltip(
                f"place_id: {int(id)}",
            ),
            opacity=1 if is_direct else 0.5,
        )
        for id, lat, lon, _, is_direct, _ in df_places[
            df_places["place_id"].isin(new_selected)
        ].itertuples(index=False)
    ]

    print(f"Time elapsed: {np.round(time()-start, 2)} second(s)")
    print(f"selected points: {new_selected}")
    print()

    return [
        (points),
        (current_bounds),
        (list(new_selected)),
        (list(new_unselected)),
    ]


@app.callback(Output("text-coords", "children"), Input("map", "bounds"))
def show_border(bounds):
    return str(bounds)


if __name__ == "__main__":
    app.run_server(debug=True)
    a = 12
    # 254891 9259 9066
