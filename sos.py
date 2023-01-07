"""
sos.py: A module that implements Spatial Object Selection (SOS)

1. set_of_objects
2. dict_of_visitors
2. border prev
3. border after
4. k integer (n of objects)
5. D (List of items that have to be displayed)
6. G (List of items that were within map border but not shown)
"""

from metrics import jaccard, haversine
import pandas as pd
import numpy as np


def spatial_object_selection(
    df_place: pd.DataFrame,
    d_visitor: dict,
    border_prev: list,
    border_now: list,
    k: int = 10,
    D: list = [],
    G: list = [],
):
    [lat1, lon1], [lat2, lon2] = border_now  # [bottom left] [upper right]
    [lat1p, lon1p], [lat2p, lon2p] = border_prev

    separation_distance = haversine(lat1, lon1, lat2, lon2) / 15

    df_place = df_place[
        (df_place["lat"].between(lat1, lat2))
        & (df_place["lon"].between(lon1, lon2))
    ]  # selects objects located within current border

    is_zoomin = (lat1p < lat1 < lat2 < lat2p) & (lon1p < lon1 < lon2 < lon2p)
    is_zoomout = (lat1 < lat1p < lat2p < lat2) & (lon1 < lon1p < lon2p < lon2)
    is_panning = not (is_zoomin or is_zoomout)

    if is_zoomin:
        S = [d for d in D if d in df_place["place_id"]]
        G = []
        df_place = df_place[(~df_place["place_id"].isin(S))]
    elif is_zoomout:
        S = []
        G = [g for g in G if g in df_place["place_id"]]
        df_place = df_place[(~df_place["place_id"].isin(G))]
    elif is_panning:
        S = [d for d in D if d in df_place["place_id"]]
        G = [g for g in G if g in df_place["place_id"]]
        df_place = df_place[
            (~df_place["place_id"].isin(S)) & (~df_place["place_id"].isin(G))
        ]

    print(df_place.head(5).to_numpy())


if __name__ == "__main__":
    pass
