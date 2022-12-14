from metrics import jaccard, overlap_coeff
from datetime import datetime
from tqdm import tqdm

import networkx as nx
import pandas as pd
import numpy as np
import re


class OS:
    def __init__(self, df_user, df_friend, df_checkin, df_location):
        self.df_user = df_user
        self.df_friend = df_friend
        self.df_checkin = df_checkin
        self.df_location = df_location

    def __str__(self):
        n_friend = min(5, len(self.df_friend))
        n_checkin = min(5, len(self.df_checkin))
        n_location = min(5, len(self.df_location))

        friend_overflow = len(self.df_friend) - n_friend
        checkin_overflow = len(self.df_checkin) - n_checkin
        location_overflow = len(self.df_location) - n_location

        s_user = self.df_user.to_string(index=False)
        s_friend = self.df_friend.to_string(index=False)
        s_checkin = self.df_checkin.to_string(index=False)
        s_location = self.df_location.to_string(index=False)

        s_user = "|" + s_user.replace("\n", "\n|")
        s_friend = "|   " + s_friend.replace("\n", "\n|   ")
        s_checkin = "    |" + s_checkin.replace("\n", "\n    |")
        s_location = "        " + s_location.replace("\n", "\n        ")

        if friend_overflow > 0:
            s_friend = "\n".join(s_friend.split("\n")[:6])
            s_friend += f"\n|    There are {friend_overflow} row(s) omitted"
        if checkin_overflow > 0:
            s_checkin = "\n".join(s_checkin.split("\n")[:6])
            s_checkin += f"\n    | There are {checkin_overflow} row(s) omitted"
        if location_overflow > 0:
            s_location = "\n".join(s_location.split("\n")[:6])
            s_location += (
                f"\n         There are {location_overflow} row(s) omitted"
            )

        return (
            "[USER]\n"
            + s_user
            + "\n|\n|---[FRIEND]\n"
            + s_friend
            + "\n|\n|---[CHECKIN]\n"
            + s_checkin
            + "\n    |\n    |---[LOCATION]\n"
            + s_location
        )


class OSGenerator:
    def __init__(self) -> None:
        self.graph = nx.MultiGraph()

    def build(
        self,
        filepath_to_friends: str,
        filepath_to_checkins: str,
        friends_delim="\t",
        checkins_delim="\t",
    ):
        n_friends = sum(1 for _ in open(filepath_to_friends))
        n_chedckins = sum(1 for _ in open(filepath_to_checkins))

        with open(filepath_to_friends) as infile:
            for line in tqdm(
                infile,
                desc="Building user graph (1/2)",
                total=n_friends,
                ncols=90,
            ):
                u, v = [int(num) for num in line.strip().split(friends_delim)]
                self.graph.add_edge(u, v, key="friends_with")

        with open(filepath_to_checkins) as infile:
            for line in tqdm(
                infile,
                desc="Building place graph (2/2)",
                total=n_chedckins,
                ncols=90,
            ):
                usr, t, lat, lng, placeid = line.strip().split(checkins_delim)
                usr = int(usr)
                placeid = int(placeid) + n_friends
                lat = float(lat)
                lng = float(lng)
                t = datetime(*[int(i) for i in re.split("\-|T|:", t[:-1])])

                self.graph.add_node(placeid, lat=lat, lng=lng)

                if not self.graph.has_edge(usr, placeid, "checksin_at"):
                    self.graph.add_edge(
                        usr, placeid, key="checksin_at", time=[]
                    )

                self.graph[usr][placeid]["checksin_at"]["time"].append(t)

    def get_friends(self, user: int):
        return [
            t[1]
            for t in self.graph.edges(user, keys=True)
            if t[2] == "friends_with"
        ]

    def get_visitors(self, placeid: int):
        return list(self.graph.neighbors(placeid))

    def get_checkintimes(
        self, user: int, placeid: int, readable: bool = False
    ):
        time_list = self.graph[user][placeid]["checksin_at"]["time"]
        if readable:
            return [t.strftime("%d-%m-%Y %H:%M:%s") for t in time_list]
        return time_list

    def get_checkins(self, user: int):
        return [
            t[1]
            for t in self.graph.edges(user, keys=True)
            if t[2] == "checksin_at"
        ]

    def get_placeinfo(self, placeid: int):
        return {
            "placeid": placeid,
            "lat": self.graph.nodes[placeid]["lat"],
            "lng": self.graph.nodes[placeid]["lng"],
        }

    def get_object_summary(
        self, user: int, friend_coefficient: float = 1, readable: bool = False
    ):
        df_user = pd.DataFrame([user], columns=["user_id"])

        friends = np.array(self.get_friends(user))
        np.random.shuffle(friends)
        friend_similarity_scores = [
            overlap_coeff(
                self.get_friends(user) + [user],
                self.get_friends(friend_id) + [friend_id],
            )
            for friend_id in friends
        ]
        n_friends = int(friend_coefficient * len(friends))
        n_friends = max(0, min(len(friends), n_friends))
        ranked_sim_index = np.argsort(friend_similarity_scores)[-n_friends:]
        selected_friends = friends[ranked_sim_index].tolist()
        df_friend = pd.DataFrame(columns=["user_id", "friend_id"])
        df_friend["user_id"] = [user] * len(selected_friends)
        df_friend["friend_id"] = selected_friends

        places = self.get_checkins(user)
        location_data = [
            [p, self.get_placeinfo(p)["lat"], self.get_placeinfo(p)["lng"]]
            for p in places
        ]
        df_location = pd.DataFrame(
            location_data, columns=["place_id", "latitude", "longitude"]
        )

        checkin_data = []
        for p in places:
            t_list = self.get_checkintimes(user, p, readable)
            for t in t_list:
                checkin_data.append([user, p, t])
        df_checkin = pd.DataFrame(
            checkin_data, columns=["user_id", "place_id", "time"]
        )

        return OS(df_user, df_friend, df_checkin, df_location)
