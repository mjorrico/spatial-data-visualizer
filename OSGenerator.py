from datetime import datetime
from copy import deepcopy
from tqdm import tqdm

import networkx as nx
import json
import re


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

    def get_visittime(self, user: int, placeid: int):
        return self.graph[user][placeid]["checksin_at"]["time"]

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

    def get_visitor(self, placeid: int):
        return list(self.graph.neighbors(1946746))

    def get_object_summary(self, user: int, prettify: bool = False):
        os = {"user": user}
        os["friends"] = self.get_friends(user)
        os["checksin_at"] = [
            {
                "placeid": pid,
                "time": self.get_visittime(user, pid),
                "visitors": self.get_visitor(pid),
                "lat": self.get_placeinfo(pid)["lat"],
                "lng": self.get_placeinfo(pid)["lng"],
            }
            for pid in self.get_checkins(user)
        ]

        if prettify:
            pretty = deepcopy(os)
            for place in pretty["checksin_at"]:
                place["time"] = [
                    t.strftime("%d-%M-%Y %H:%m:%s") for t in place["time"]
                ]
            print(json.dumps(pretty, indent=4))

        return os
