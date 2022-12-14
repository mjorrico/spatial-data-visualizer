def jaccard(seq1, seq2):
    set1, set2 = set(seq1), set(seq2)
    return len(set1 & set2) / float(len(set1 | set2))


def overlap_coeff(seq1, seq2):
    set1, set2 = set(seq1), set(seq2)
    return len(set1 & set2) / min(len(set1), len(set2))


if __name__ == "__main__":
    s1 = [1, 2, 3, 4]
    s2 = [2, 3, 4, 5]
    print(jaccard(s1, s2))
    print(overlap_coeff(s1, s2))

    s1 = [2, 3, 4]
    s2 = [2, 3, 4, 5, 1]
    print(jaccard(s1, s2))
    print(overlap_coeff(s1, s2))
