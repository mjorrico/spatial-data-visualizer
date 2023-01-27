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

from metrics import jaccard, euclidean
import pandas as pd
import numpy as np
from maxheap import Maxheap


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

    separation_distance = euclidean(lat1, lon1, lat2, lon1) * 0.1
    print(f"Separation distance: {separation_distance} degrees")

    is_zoomin = (lat1p < lat1 < lat2 < lat2p) & (lon1p < lon1 < lon2 < lon2p)
    is_zoomout = (lat1 < lat1p < lat2p < lat2) & (lon1 < lon1p < lon2p < lon2)
    is_panning = not (is_zoomin or is_zoomout)

    df_place = df_place[
        (df_place["lat"].between(lat1, lat2))
        & (df_place["lon"].between(lon1, lon2))
    ].drop(
        columns=["country_id", "is_direct"]
    )  # selects objects located within current border [pid, lat, lon, cid, isdirect, w]
    print(f"# objects in current window: {len(df_place)}")

    df_place_placeid = df_place["place_id"].to_list()
    if is_zoomin:
        S = [d for d in D if d in df_place_placeid]
        G = []
        print("Zoomin registered")
    elif is_zoomout:
        S = []
        G = [g for g in G if g in df_place_placeid]
        print("Zoomout registered")
    elif is_panning:
        S = [d for d in D if d in df_place_placeid]
        G = [g for g in G if g in df_place_placeid]
        print("Panning registered")

    print(f"initial S: {S}")

    print(len(df_place))
    df_maxheap = df_place[~(df_place["place_id"].isin(G))]
    print(len(df_maxheap))

    # removing all points that are close to already chosen points from previous frame
    for s in S:
        maxheap_lats = df_maxheap.lat.values
        maxheap_lons = df_maxheap.lon.values

        s_lat = df_place[df_place.place_id == s].lat.values[0]
        s_lon = df_place[df_place.place_id == s].lon.values[0]
        keep_idx = (
            euclidean(s_lat, s_lon, maxheap_lats, maxheap_lons)
            > separation_distance
        )

        if np.sum(keep_idx) != len(keep_idx):
            print(
                f"Pruned {len(keep_idx) - np.sum(keep_idx)} points too close to {s}"
            )

        df_maxheap = df_maxheap[keep_idx]

    maxheap_data = [
        df_maxheap["place_id"].to_numpy(),
        df_maxheap["lat"].to_numpy(),
        df_maxheap["lon"].to_numpy(),
    ]
    del df_maxheap

    new_S = greedy_sos(
        maxheap_data,
        df_place,
        d_visitor,
        k,
        separation_distance,
        S,
    )

    new_G = [pid for pid in df_place.place_id if pid not in new_S]
    return (new_S, new_G)


def greedy_sos(
    maxheap_data: list,
    df_place: pd.DataFrame,  # [pid, lat, lon, w]
    d_visitor: dict,
    k: int,
    min_distance: float,
    S: list,
):
    place_order = df_place.place_id.to_list()
    weights = df_place.weight.to_numpy()

    id_maxheap = maxheap_data[0]
    iter_maxheap = np.ones_like(maxheap_data[0]) * len(S)

    lat_maxheap = maxheap_data[1]
    lon_maxheap = maxheap_data[2]

    # Calculates sim(o, S) \forall o \in O, a set of size len(place_id_list)
    sim_oS = np.zeros(len(place_order))
    for s in S:
        sim_oS = update_sim_oS(sim_oS, s, place_order, d_visitor)

    # Calculates score(S|O)
    score_S = calc_score_OS(weights, sim_oS)  # scalar

    # calculates calculates Score(Suo|O) \forall o \in O
    score_Suo = calc_initial_score_Suo(
        sim_oS,
        id_maxheap,
        place_order,
        d_visitor,
        weights,
    )  # array

    # Score(S \cup o|O) - Score(S|O) for all o \in O
    gain_maxheap = score_Suo - score_S  # array - scalar

    maxheap = Maxheap(
        id_maxheap,
        lat_maxheap,
        lon_maxheap,
        gain_maxheap,
        iter_maxheap,
    )

    while len(S) < k and len(maxheap) > 0:
        # t_ints = [[`t_place_id`, `t_iter`]]
        # t_float = [[`t_lat`, `t_lon`, `t_score_gain`]]
        t_ints, t_floats = maxheap.poptop()
        new_sim_oS, new_score_S = sim_oS, score_S

        while t_ints[0, 1] != len(S):
            new_sim_oS = update_sim_oS(
                sim_oS,
                t_ints[0, 0],
                place_order,
                d_visitor,
            )
            new_score_S = calc_score_OS(weights, new_sim_oS)

            t_floats[0, 2] = new_score_S - score_S
            t_ints[0, 1] = len(S)
            maxheap.insert(t_ints, t_floats)
            t_ints, t_floats = maxheap.poptop()

        sim_oS, score_S = new_sim_oS, new_score_S
        S.append(t_ints[0, 0])

        # Remove all locations within the distance of \theta from `t` from maxheap
        t_lat, t_lon = t_floats[0, :2]
        maxheap.delete_neighbors(t_lat, t_lon, min_distance)

    print(f"Score of the new S: {score_S}")

    return S


def calc_initial_score_Suo(
    sim_oS,
    maxheap_place_id,
    place_id_order,
    d_visitor,
    weights,
):
    sim_OSuo = [
        calc_score_OS(
            weights,
            update_sim_oS(
                sim_oS,
                o,
                place_id_order,
                d_visitor,
            ),
        )
        for o in maxheap_place_id
    ]

    return np.array(sim_OSuo)


def calc_score_OS(weights, oS):
    return (1 / len(weights)) * np.dot(weights, oS)


def update_sim_oS(old_oS, new_place_id, place_id_order, d_visitor):
    new_oS = calc_sim_oS(new_place_id, place_id_order, d_visitor)
    return np.max(np.stack([old_oS, new_oS]), axis=0)


def calc_sim_oS(new_place_id, place_id_order, d_visitor):
    new_visitor = d_visitor[new_place_id]
    oS = np.array([jaccard(d_visitor[o], new_visitor) for o in place_id_order])
    return oS


# if __name__ == "__main__":
#     np.set_printoptions(suppress=True)
#     import matplotlib.pyplot as plt
#     from time import time

#     def random_visitor():
#         return np.random.choice(
#             range(101, 151),
#             np.random.randint(5, 10),
#             False,
#         )

#     n = 900

#     pid = np.random.randint(0, 100000, n)
#     lat = np.random.random(n) * 6 + 4
#     lon = np.random.random(n) * 8 + 2
#     weight = np.random.random(n)
#     lat[0], lon[0] = 0.1, 0.1
#     lat[1], lon[1] = 2.1, 0.15
#     plt.scatter(lon, lat)
#     plt.savefig("scatter.png")

#     S = list(pid[:2])

#     df_place = pd.DataFrame()
#     df_place["place_id"] = pid
#     df_place["weight"] = weight
#     df_place["lat"] = lat
#     df_place["lon"] = lon

#     df_maxheap = df_place.iloc[2:, :]
#     maxheap_data = [
#         df_maxheap["place_id"].to_numpy(),
#         df_maxheap["lat"].to_numpy(),
#         df_maxheap["lon"].to_numpy(),
#     ]

#     d_visitor = {k: random_visitor().tolist() for k in df_place.place_id}

#     start = time()
#     new_S = greedy_sos(
#         maxheap_data,
#         df_place,
#         d_visitor,
#         10,
#         111,
#         S,
#     )

#     print(f"Time elapsed: {time() - start} second(s)")
#     print(new_S)
