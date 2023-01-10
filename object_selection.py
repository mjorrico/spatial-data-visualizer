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
    unselected = [pid for pid in df_place.place_id if pid not in selected]

    return (selected, unselected)


def greedy_sos(
    df_maxheap: pd.DataFrame,
    df_all_places: list,
    d_visitor: dict,
    k: int,
    min_distance: float,
    S: list,
    G: list,
):
    df_maxheap["score_diff"] = [
        set_sim(df_all_places, S + [pid], d_visitor)
        for pid in df_maxheap.place_id
    ]
    df_maxheap["iter"] = [len(S)] * len(df_maxheap)
    df_maxheap = df_maxheap.sort_values(
        "score_diff", ignore_index=True, ascending=False
    )

    while len(S) < k and len(df_maxheap) > 0:
        top = df_maxheap.iloc[:1, :].copy().reset_index(drop=True)
        df_maxheap = df_maxheap.iloc[1:, :]

        while top.loc[0, "iter"] != len(S):
            top.loc[0, "score_diff"] = (
                set_sim(df_all_places, S + [top.loc[0, "place_id"]], d_visitor)
                - top.loc[0, "score_diff"]
            )
            top.loc[0, "iter"] = len(S)

            try:
                insert_idx = next(
                    i
                    for i, v in enumerate(df_maxheap.score_diff.to_list())
                    if v >= top.loc[0, "score_diff"]
                )
            except StopIteration:
                insert_idx = len(df_maxheap)

            try:
                df_maxheap = pd.concat(
                    [
                        df_maxheap.iloc[:insert_idx, :],
                        top,
                        df_maxheap.iloc[insert_idx:, :],
                    ]
                )
            except pd.errors.InvalidIndexError:
                print(insert_idx)

            top = df_maxheap.iloc[:1, :].copy().reset_index(drop=True)
            df_maxheap = df_maxheap.iloc[1:, :]

        S.append(top.loc[0, "place_id"])

        lat2 = df_maxheap["lat"].to_numpy()
        lon2 = df_maxheap["lon"].to_numpy()
        lat1 = [top.loc[0, "lat"]] * len(df_maxheap)
        lon1 = [top.loc[0, "lon"]] * len(df_maxheap)
        is_kept = haversine(lat1, lon1, lat2, lon2) > min_distance
        df_maxheap = df_maxheap[is_kept]

    return S


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

    separation_distance = haversine(lat1, lon1, lat2, lon1) * 0.1  # width / 10

    is_zoomin = (lat1p < lat1 < lat2 < lat2p) & (lon1p < lon1 < lon2 < lon2p)
    is_zoomout = (lat1 < lat1p < lat2p < lat2) & (lon1 < lon1p < lon2p < lon2)
    is_panning = not (is_zoomin or is_zoomout)

    df_maxheap = df_place[
        (df_place["lat"].between(lat1, lat2))
        & (df_place["lon"].between(lon1, lon2))
    ][
        ["place_id", "lat", "lon", "weight"]
    ]  # selects objects located within current border

    df_all_places = df_maxheap[["place_id", "weight"]].copy()
    df_maxheap = df_maxheap.drop("weight", axis="columns")

    print(len(df_all_places))

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

    # if len(S) + len(df_maxheap) <= k:
    #     print("Shortcut triggered")
    #     return (S + df_maxheap.place_id.to_list(), [])
    # elif len(S) > k:
    #     raise RuntimeError("This isn't supposed to happen")

    new_S = greedy_sos(
        df_maxheap, df_all_places, d_visitor, 10, separation_distance, S, G
    )

    return (new_S, [pid for pid in df_all_places.place_id if pid not in new_S])


def obj_sim(obj: int, list_of_objs: list[int], visitors: dict):
    visitor_obj = visitors[obj]
    jaccard_vals = [
        jaccard(visitor_obj, visitors[s_obj]) for s_obj in list_of_objs
    ]
    return np.max(jaccard_vals)


def set_sim(all_objects: pd.DataFrame, list_of_objs: list[int], visitors):
    sim = [
        obj_sim(tup.place_id, list_of_objs, visitors)
        for tup in all_objects.itertuples()
    ]
    return np.dot(all_objects.weight, sim) / len(all_objects)
