import numpy as np
from metrics import haversine, euclidean


class Maxheap:
    def __init__(self, id, lat, lon, gain, iter):
        sort_idx = np.argsort(gain)[::-1]

        self.float_stack = np.array([lat, lon, gain], dtype=np.float32).T
        self.int_stack = np.array([id, iter], dtype=np.int32).T  # place_id

        self.float_stack = self.float_stack[sort_idx]
        self.int_stack = self.int_stack[sort_idx]

    def __repr__(self):
        n = min(len(self), 40)
        return str(
            np.concatenate(
                [self.int_stack[:n], self.float_stack[:n, :]],
                axis=1,
            )
        )

    def __len__(self):
        return len(self.int_stack)

    def poptop(self):
        top = (self.int_stack[:1, :], self.float_stack[:1, :])
        self.int_stack = self.int_stack[1:, :]
        self.float_stack = self.float_stack[1:, :]
        return top

    def insert(self, int_arr, float_arr):
        if len(self.float_stack) == 0:
            insert_idx = 0
        elif self.float_stack[-1, 2] > float_arr[0, 2]:
            insert_idx = len(self)
        else:
            insert_idx = np.argmax(self.float_stack[:, 2] < float_arr[0, 2])

        self.int_stack = np.insert(self.int_stack, insert_idx, int_arr, 0)
        self.float_stack = np.insert(
            self.float_stack, insert_idx, float_arr, 0
        )

    def delete(self, arr):
        keep_idx = ~np.isin(self.int_stack[:, 0], arr)
        self.int_stack = self.int_stack[keep_idx]
        self.float_stack = self.float_stack[keep_idx]

    def delete_neighbors(self, lat, lon, radius):
        stack_lat = self.float_stack[:, 0]
        stack_lon = self.float_stack[:, 1]

        index_keep = euclidean(lat, lon, stack_lat, stack_lon) > radius

        self.int_stack = self.int_stack[index_keep]
        self.float_stack = self.float_stack[index_keep]
