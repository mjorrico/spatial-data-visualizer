
# Dataset Directory

All datasets are to be placed here. Cleansed Gowalla datasets can be obtained 
[here](https://uppsalauniversitet-my.sharepoint.com/:f:/g/personal/misaeljordan_enrico_6037_student_uu_se/EmroTZTnO9dGiF3Zz_OB_hwBTHM-weFzmNCnpNwI3Bh9Ng?e=bfmWBx) while the raw data is from [[E. Cho, 2011]](https://snap.stanford.edu/data/loc-gowalla.html). 
There are four `.csv` files required.

| File Name       | Size     | MD5 Hash                           |
| --------------- | -------- | ---------------------------------- |
| `friends.csv`   | 22.1 MB  | `260a822894789de5efee8edaad46e14e` |
| `checkins.csv`  | 219.2 MB | `f770d4772bae26db65d0a1ce394bad44` |
| `places.csv`    | 48.3 MB  | `e35b92f8a9b88ea0ac92404150cdbaa3` |
| `countries.csv` | 2.6 kB   | `24ea180a909c4c4115c7c8a27902a1ab` |

## Checking File Integrity

To ensure datasets are correct, run

```bash
  $ md5sum [.csv dataset to check]
```