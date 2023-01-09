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


def random_selection(df_place: pd.DataFrame, bound: list, k: int):
    [lat1, lon1], [lat2, lon2] = bound  # [bottom left] [upper right]
    df_place = df_place[
        (df_place["lat"].between(lat1, lat2))
        & (df_place["lon"].between(lon1, lon2))
    ]  # selects objects located within current border

    N = min(k, len(df_place))
    selected = df_place["place_id"].sample(N).to_numpy()

    return selected


def greedy_sos(
    df_maxheap: pd.DataFrame,
    df_all_places: list,
    d_visitor: dict,
    k: int,
    min_distance: float,
    S: list,
    G: list,
):
    df_maxheap["score"] = [
        set_sim(df_all_places, S + [pid], d_visitor)
        for pid in df_maxheap.place_id
    ]
    df_maxheap["iter"] = [len(S)] * len(df_maxheap)
    df_maxheap = df_maxheap.sort_values(
        "score", ignore_index=True, ascending=False
    )


def isos(
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

    separation_distance = haversine(lat1, lon1, lat2, lon1) / 10  # width / 10

    is_zoomin = (lat1p < lat1 < lat2 < lat2p) & (lon1p < lon1 < lon2 < lon2p)
    is_zoomout = (lat1 < lat1p < lat2p < lat2) & (lon1 < lon1p < lon2p < lon2)
    is_panning = not (is_zoomin or is_zoomout)

    df_maxheap = df_place[
        (df_place["lat"].between(lat1, lat2))
        & (df_place["lon"].between(lon1, lon2))
    ][
        ["place_id", "lat", "lon", "weight"]
    ]  # selects objects located within current border

    df_all_places = df_maxheap[["place_id", "weight"]]
    df_maxheap = df_maxheap.drop("weight", axis="columns")
    if len(df_all_places) <= k:
        print("Shortcut triggered")
        return (df_all_places.place_id.to_list(), [])

    if is_zoomin:
        S = [d for d in D if d in df_maxheap["place_id"]]
        G = []
        df_maxheap = df_maxheap[(~df_maxheap["place_id"].isin(S))]
    elif is_zoomout:
        S = []
        G = [g for g in G if g in df_maxheap["place_id"]]
        df_maxheap = df_maxheap[(~df_maxheap["place_id"].isin(G))]
    elif is_panning:
        S = [d for d in D if d in df_maxheap["place_id"]]
        G = [g for g in G if g in df_maxheap["place_id"]]
        df_maxheap = df_maxheap[
            (~df_maxheap["place_id"].isin(S))
            & (~df_maxheap["place_id"].isin(G))
        ]
    else:
        raise SyntaxError("Map interaction type is not known...")

    if all([s in D for s in S]) and all([d in S for d in D]):
        print("Showing same points")
        return (S, [pid for pid in df_all_places.place_id if pid not in S])
    elif len(S) > k:
        raise RuntimeError("This isn't supposed to happen")

    selected = greedy_sos(
        df_maxheap, df_all_places, d_visitor, 10, separation_distance, S, G
    )

    return (df_all_places.sample(min(10, len(df_all_places)))["place_id"], [])


if __name__ == "__main__":
    pass


def obj_sim(obj: int, list_of_objs: list[int], visitors: dict):
    N = len(list_of_objs)
    jaccard_vals = [
        jaccard(visitors[str(obj)], visitors[str(list_of_objs[i])])
        for i in range(N)
    ]
    return np.max(jaccard_vals)


def set_sim(all_objects: pd.DataFrame, list_of_objs: list[int], visitors):
    sim = [
        obj_sim(tup.place_id, list_of_objs, visitors)
        for tup in all_objects.itertuples()
    ]
    return np.dot(all_objects.weight, sim) / len(all_objects)
