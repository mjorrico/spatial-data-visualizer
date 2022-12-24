import numpy as np


def jaccard(seq1, seq2):
    set1, set2 = set(seq1), set(seq2)
    n_intersect = len(set1 & set2)
    n_union = len(seq1) + len(seq2) - n_intersect
    return n_intersect / n_union


def overlap_coeff(seq1, seq2):
    set1, set2 = set(seq1), set(seq2)
    return len(set1 & set2) / min(len(set1), len(set2))


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    )
    c = 2 * np.arcsin(np.sqrt(a))
    km = 6371 * c

    return km
