
# Dataset Directory

All datasets are to be placed here. Gowalla datasets can be obtained 
here [[E. Cho, 2011]](https://snap.stanford.edu/data/loc-gowalla.html). 
Both checkins and friends network dataset must be renamed to `checkins.txt` 
and `friends.txt` respectively.

| File Name      | Compressed Name                    | MD5 Hash                           |
| -------------- | ---------------------------------- | ---------------------------------- |
| `friends.txt`  | `loc-gowalla_edges.txt.gz`         | `e01bc5bdd3282036d7150865fa17797b` |
| `checkins.txt` | `loc-gowalla_totalCheckins.txt.gz` | `15bd6d99b85ee4b48fa980082286d5a2` |

## Checking File Integrity

To ensure datasets are correct, run

```bash
  $ md5sum [.txt dataset to check]
```