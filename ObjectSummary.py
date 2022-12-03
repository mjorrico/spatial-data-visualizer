from copy import deepcopy
from tqdm import tqdm

import networkx as nx
import datetime


def jaccard(seq1, seq2):
    set1, set2 = set(seq1), set(seq2)
    return len(set1 & set2) / float(len(set1 | set2))


class ObjectSummary:
    def __init__(self) -> None:
        self.graph = nx.Graph()
        self.place_info = {}  # {key: placeid, value: {lat, lng, visitors}}

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
                infile, desc="Building graph (1/2)", total=n_friends
            ):
                u, v = [int(num) for num in line.strip().split(friends_delim)]
                self.graph.add_edge(u, v)

        with open(filepath_to_checkins) as infile:
            prev_user = -1
            checkin_list = []
            for line in tqdm(
                infile,
                desc="Adding attributes (2/2)",
                total=n_chedckins,
            ):
                usr, t, lat, lng, placeid = line.strip().split(checkins_delim)
                usr = int(usr)
                placeid = int(placeid)
                if placeid in self.place_info.keys():
                    self.place_info[placeid]["users"].add(usr)
                else:
                    self.place_info[placeid] = {
                        "lat": float(lat),
                        "lng": float(lng),
                        "users": {usr},
                    }

                if prev_user != usr:
                    nx.set_node_attributes(
                        self.graph, {prev_user: {"checkins": checkin_list}}
                    )
                    checkin_list = []

                t = datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%SZ")
                checkin_list.append({"placeid": placeid, "time": t})
                prev_user = usr

            nx.set_node_attributes(self.graph, {usr: checkin_list})

            for k in self.place_info.keys():
                self.place_info[k]["users"] = list(self.place_info[k]["users"])

    def get_friends(self, user: int):
        return {
            "user": user,
            "friends": [f for f in self.graph.neighbors(user)],
        }

    def get_checkins(self, user: int):
        return {"user": user, "checkins": self.graph.nodes[user]["checkins"]}

    def get_place(self, placeid: int):
        output = self.place_info[placeid]
        output["placeid"] = placeid
        return output

    def show(self, user: int, as_json: bool = False):
        os = {"user": user}
        os["friends"] = self.get_friends(user)["friends"]
        os["checkedin_at"] = [
            {
                "placeid": p["placeid"],
                "time": p["time"].strftime("%d-%M-%Y %H:%m:%s")
                if as_json
                else p["time"],
                "visitors": self.place_info[p["placeid"]]["users"],
                "lat": self.place_info[p["placeid"]]["lat"],
                "lng": self.place_info[p["placeid"]]["lng"],
            }
            for p in self.get_checkins(user)["checkins"]
        ]
        return os
