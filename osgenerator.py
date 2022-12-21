from metrics import jaccard, overlap_coeff
from datetime import datetime
from tqdm import tqdm
from math import sqrt

import networkx as nx
import pandas as pd
import numpy as np
import re


class OS:
    def __init__(
        self, df_user, df_friend, df_checkin, df_location, df_countries
    ):
        self.df_user = df_user
        self.df_friend = df_friend
        self.df_checkin = df_checkin
        self.df_location = df_location
        self.df_country = df_countries

        self.visited_place = self.df_location["place_id"].unique().tolist()
        self.visited_country = self.df_country["country_id"].unique().tolist()
        self.friend = self.df_friend["friend_id"].unique().tolist()

    def __str__(self):
        n_friend = min(5, len(self.df_friend))
        n_checkin = min(5, len(self.df_checkin))
        n_location = min(5, len(self.df_location))
        n_country = min(5, len(self.df_country))

        friend_overflow = len(self.df_friend) - n_friend
        checkin_overflow = len(self.df_checkin) - n_checkin
        location_overflow = len(self.df_location) - n_location
        country_overflow = len(self.df_country) - n_country

        s_user = self.df_user.to_string(index=False)
        s_friend = self.df_friend.to_string(index=False)
        s_checkin = self.df_checkin.to_string(index=False)
        s_location = self.df_location.to_string(index=False)
        s_country = self.df_country.to_string(index=False)

        s_user = "|" + s_user.replace("\n", "\n|")
        s_friend = "|    " + s_friend.replace("\n", "\n|    ")
        s_checkin = "    |" + s_checkin.replace("\n", "\n    |")
        s_location = "        |" + s_location.replace("\n", "\n        |")
        s_country = "             " + s_country.replace(
            "\n", "\n             "
        )

        if friend_overflow > 0:
            s_friend = "\n".join(s_friend.split("\n")[:6])
            s_friend += f"\n|    There are {friend_overflow} row(s) omitted"
        if checkin_overflow > 0:
            s_checkin = "\n".join(s_checkin.split("\n")[:6])
            s_checkin += f"\n    | There are {checkin_overflow} row(s) omitted"
        if location_overflow > 0:
            s_location = "\n".join(s_location.split("\n")[:6])
            s_location += (
                f"\n        | There are {location_overflow} row(s) omitted"
            )
        if country_overflow > 0:
            s_location = "\n".join(s_location.split("\n")[:6])
            s_location += (
                f"\n              There are {country_overflow} row(s) omitted"
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
            + "\n        |\n        |---[COUNTRY]\n"
            + s_country
        )


class OSGenerator:
    def __init__(self) -> None:
        self.df_friends = None
        self.df_checkins = None
        self.df_places = None
        self.df_countries = None

    @property
    def n_user(self):
        return len(np.unique(self.df_friends["user_id"]))

    @property
    def n_place(self):
        return len(np.unique(self.df_places["place_id"]))

    @property
    def n_checkin(self):
        return len(self.df_checkins)

    def read_from_dataframe(
        self, df_friend, df_checkin, df_place, df_country
    ) -> None:
        self.df_friends = df_friend
        self.df_checkins = df_checkin
        self.df_places = df_place
        self.df_countries = df_country

    def read_from_file(
        self,
        filepath_to_friends: str,
        filepath_to_checkins: str,
        filepath_to_places: str,
        filepath_to_countries: str,
    ) -> None:
        self.df_friends = pd.read_csv(filepath_to_friends)
        self.df_checkins = pd.read_csv(filepath_to_checkins)
        self.df_places = pd.read_csv(filepath_to_places)
        self.df_countries = pd.read_csv(filepath_to_countries)

    def get_user_friend(self, user: int) -> pd.Series:  # ok
        if user not in self.df_friends["user_id"]:
            raise KeyError(f"User {user} cannot be found.")
        return (
            self.df_friends[self.df_friends["user_id"] == user]["friend_id"]
            .unique()
            .tolist()
        )

    def get_user_relevant_friend(self, user: int) -> pd.DataFrame:
        friends = np.array(self.get_user_friend(user))
        n_friends = int((len(friends) + 0.5) ** (1 / 3))
        np.random.shuffle(friends)
        friend_similarity_scores = np.array(
            [
                jaccard(
                    friends.tolist() + [user],
                    self.get_user_friend(friend_id) + [friend_id],
                )
                for friend_id in friends
            ]
        )
        ranked_sim_index = np.argsort(friend_similarity_scores)[-n_friends:]
        selected_friends = friends[ranked_sim_index]
        selected_scores = np.array(friend_similarity_scores)[ranked_sim_index]
        df_friend = pd.DataFrame()
        df_friend["user_id"] = [user] * len(selected_friends)
        df_friend["friend_id"] = selected_friends
        df_friend["similarity"] = selected_scores
        df_friend = df_friend.sort_values(
            "similarity", ascending=False, ignore_index=True
        )

        return df_friend

    def get_visitor(self, placeid: int):  # ok
        if placeid not in self.df_places["place_id"].to_list():
            raise KeyError(f"Place {placeid} cannot be found.")
        return (
            self.df_checkins[self.df_checkins["place_id"] == placeid][
                "user_id"
            ]
            .unique()
            .tolist()
        )

    def get_checkin_time(self, user: int, placeid: int):  # ok
        return self.df_checkins[
            (self.df_checkins["user_id"] == user)
            & (self.df_checkins["place_id"] == placeid)
        ]

    def get_user_checkin(self, user):  # ok
        if isinstance(user, int):
            return self.df_checkins[self.df_checkins["user_id"] == user]
        elif isinstance(user, list):
            return self.df_checkins[self.df_checkins["user_id"].isin(user)]

    def get_user_place(self, user):
        places = self.get_user_checkin(user)["place_id"].tolist()
        return self.df_places[self.df_places["place_id"].isin(places)]

    def get_relevant_place(self, user):
        df_direct_visit = self.get_user_place(user)
        selected_friends = self.get_user_relevant_friend(user)[
            "friend_id"
        ].to_list()
        df_friend_visit = self.get_user_place(selected_friends)
        return pd.concat(
            (df_direct_visit, df_friend_visit), ignore_index=True
        ).drop_duplicates("place_id")

    def get_place_info(self, placeid: int):  # ok
        return self.df_places[self.df_places["place_id"] == placeid]

    def get_object_summary(self, user: int):
        df_user = pd.DataFrame([user], columns=["user_id"])

        df_friend = self.get_user_relevant_friend(user)

        places = self.get_user_checkin(user)["place_id"].unique().tolist()
        df_location = self.df_places[self.df_places["place_id"].isin(places)]

        df_checkin = self.df_checkins[
            (self.df_checkins["user_id"] == user)
            & (self.df_checkins["place_id"].isin(places))
        ]

        countries = df_location["country_id"].unique().tolist()
        df_countries = self.df_countries[
            self.df_countries["country_id"].isin(countries)
        ]

        return OS(df_user, df_friend, df_checkin, df_location, df_countries)
