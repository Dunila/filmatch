import pandas as pd
import numpy as np
from pathlib import Path
from scipy.sparse import csr_matrix
from sklearn.preprocessing import StandardScaler, normalize
from src.recommenders.data import load_user_ratings
import sqlite3


NUMERIC_FEATURES = [
    "year",
    "duration",
    "rating",
    "watched",
    "liked"
]

CATEGORICAL_SET_FEATURES = [
    "studio",
    "country",
    "genres",
    "themes"
]

CREW_FEATURES = [
    "director",
    "writer",
    "producer",
    "cinematography",
    "composer"
]

CREW_SET_FEATURES = ["actors"]

DB_PATH = Path("data/parsed_data.db")


def convert_srt_to_int(value):
    if isinstance(value, str):
        if "K" in value:
            return int(float(value.replace("K", ""))* 1e3) 
        elif "M" in value:
            return int(float(value.replace("M", ""))* 1e6) 
        else:
            return int(value)
    return value

def person_encode(
    df: pd.DataFrame,
    feature_person: str,
    aggregating: dict = {"watched": "mean", "rating": "mean", "duration": "count"}
) -> pd.DataFrame:
    persons = df.groupby(by=feature_person).agg(aggregating)
    persons.rename(columns={"duration": f"count_{feature_person}"}, inplace=True)
    return persons

def crew_dummies(
        df: pd.DataFrame,
        feature_person: str
) -> pd.DataFrame:
    persons = pd.get_dummies(
        df[feature_person],
        prefix = feature_person
    )
    return persons


def prepare_films(
    original_df: pd.DataFrame,
    drop_na: bool = True,
    make_decade: bool = True,
    year_filter: tuple = (1920, 2024),
    watched_log: bool = False,
    watched_filter: int | None = 2000,
    liked_log: bool = False,
    duration_filter: tuple | None = (60, 240),
    to_encode_persons: bool = True,
    drop_obvious_features: bool = False #drop rating, watched, liked
) -> pd.DataFrame:
    df = original_df.copy()

    #convert str in watched and liked to int
    if "watched" in df.columns:
        df["watched"] = df["watched"].map(convert_srt_to_int)
    if "liked" in df.columns:
        df["liked"] = df["liked"].map(convert_srt_to_int)

    if drop_na:
        if "year" in df.columns:
            df = df.dropna(subset=["year"])
        if "director" in df.columns:
            df = df.dropna(subset=["director"])

    if year_filter and "year" in df.columns:
        df = df[
            (df["year"] >= year_filter[0]) & (df["year"] <= year_filter[1])
        ]

    if make_decade and "year" in df.columns:
        df["decade"] = (df["year"]//10*10).astype(int)
        df_decades = pd.get_dummies(
            df["decade"],
            prefix="decade"
        ).astype(int)
        df = df.merge(
            df_decades,
            how="left",
            right_index=True,
            left_index=True
        )
        df = df.drop(columns=["decade"])

    if watched_filter and "watched" in df.columns:
        df = df[df["watched"] >= watched_filter]

    #watched has large right tail, so log could help to normalize
    if watched_log and "watched" in df.columns:
        df["watched"] = df["watched"].apply(np.log)

    if liked_log and "liked" in df.columns:
        df["liked"] = df["liked"].apply(np.log)

    if duration_filter and "duration" in df.columns:
        df = df[(df["duration"] >= duration_filter[0]) & (df["duration"] <= duration_filter[1])]

    for crew_member_feature in CREW_FEATURES:
        if crew_member_feature in df.columns:
            if to_encode_persons:
                    persons = person_encode(df, crew_member_feature)
                    df = df.merge(
                        persons,
                        left_on=crew_member_feature,
                        right_index=True,
                        how="left",
                        suffixes=("", f"_{crew_member_feature}")
                    )
                    df = df.drop(columns=[crew_member_feature])
                    for col in df.columns:
                        if crew_member_feature in col:
                            col_mean = df[col].mean()
                            df[col] = df[col].fillna(col_mean)
            else:
                persons = crew_dummies(df, crew_member_feature)
                df = df.merge(
                    persons,
                    left_on=crew_member_feature,
                    right_index=True,
                    suffixes=("", f"_{crew_member_feature}")
                )

    if "actors" in df.columns:
        df_actors = df["actors"].explode().reset_index()
        if to_encode_persons:
            df_actors = df_actors.merge(
                df[["watched", "rating"]],
                how="left",
                left_on="index",
                right_index=True
            )
            actors = df_actors.groupby(by="actors").mean()[["watched", "rating"]]
            df_actors = df_actors.merge(
                actors,
                how="left",
                left_on="actors",
                right_index=True,
                suffixes=("", "_actors")
            ).groupby(by="index").max()[["watched_actors", "rating_actors"]]
            df = df.merge(
                df_actors,
                how="left",
                right_index=True,
                left_index=True
            )
        df = df.drop(columns=["actors"])

    if "studio" in df.columns:
        df["studio"] = df["studio"].apply(lambda x: x[0] if len(x) >= 1 else np.nan)
        studio_list = df[["studio", "watched"]].groupby(by="studio").count()["watched"].sort_values(ascending=False)[:50].index
        df["studio"] = df["studio"].apply(lambda x: x if x in studio_list else "another")
        studios = pd.get_dummies(
            df["studio"],
            prefix = "studio"
        ).astype(int)
        df=df.merge(
            studios,
            how="left",
            right_index=True,
            left_index=True
        )
        df = df.drop(columns=["studio"])

    if "country" in df.columns:
        df["country"] = df["country"].apply(lambda x: x[0] if len(x) >= 1 else np.nan)
        countries_list = df[["country", "watched"]].groupby(by="country").count()["watched"].sort_values(ascending=False)[:25].index
        df["country"] = df["country"].apply(lambda x: x if x in countries_list else "another")
        countries = pd.get_dummies(
            df["country"],
            prefix = "country"
        ).astype(int)
        df=df.merge(
            countries,
            how="left",
            right_index=True,
            left_index=True
        )
        df = df.drop(columns=["country"])
    
    if "genres" in df.columns:
        df_genres = df["genres"].explode().reset_index()
        df_genres = pd.get_dummies(df_genres).astype(int).groupby(by="index").max()
        df = df.merge(
            df_genres,
            how="left",
            right_index=True,
            left_index=True
        )
        df = df.drop(columns=["genres"])

    if "themes" in df.columns:
        df_themes = df["themes"].explode().reset_index()
        df_themes = pd.get_dummies(df_themes).astype(int).groupby(by="index").max()
        df = df.merge(
            df_themes,
            how="left",
            right_index=True,
            left_index=True
        )
        df = df.drop(columns=["themes"])

    if drop_obvious_features:
        df = df.drop(columns=["watched", "liked", "rating"])

    return df

def standardize_films(
    df: pd.DataFrame
) -> pd.DataFrame:
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            sc = StandardScaler()
            df[col] = sc.fit_transform(np.array(df[col]).reshape(-1, 1))
    for crew_feature in CREW_FEATURES + ["actors"]:
        for col in [x for x in df.columns if f"_{crew_feature}" in x]:
            sc = StandardScaler()
            df[col] = sc.fit_transform(np.array(df[col]).reshape(-1, 1))
    return df

def build_film_matrix(
        df: pd.DataFrame
) -> csr_matrix:
    features = df.select_dtypes(
        include=["number", "bool"]
    )

    matrix = csr_matrix(
        features.to_numpy(dtype=np.float32)
    )

    matrix = normalize(
        matrix,
        norm="l2",
        axis=1
    )

    return matrix

def find_similar_films(
        film_idx: int,
        film_matrix: csr_matrix,
        n_neighbors: int = 20,
        ban_list: list = []
) -> list[dict]:
    target = film_matrix[film_idx]

    if len(ban_list) >= 1:
        indices = list(set(range(film_matrix.shape[0])).difference(set(ban_list)))
        film_matrix = film_matrix[indices]

    similarities = (
        film_matrix @ target.T
    ).toarray().ravel()

    first_index = 0 if len(ban_list) >= 1 else 1

    top_indices = np.argsort(
        similarities
    )[::-1][first_index:n_neighbors + first_index]

    return [{"film_idx": int(idx), "similarity": float(similarities[idx])} for idx in top_indices]

def recommend(
        dataframe_films: pd.DataFrame,
        films_matrix: csr_matrix,
        username: str,
        top_user_films: int = 10,
        users_rating: int | None = None,
        n_neighbors: int = 10,
        n_recommendations: int = 10
) -> list[dict]:

    with sqlite3.Connection(DB_PATH) as conn:  
        films = load_user_ratings(
            conn,
            username=username
        )

       

def recommend_from_ratings(
    film_matrix: csr_matrix,
    ratings: dict[int, float],
    top_user_films: int = 50,
    n_neighbors: int = 50,
    n_recommendations: int = 20,
) -> list[int]:

    if not ratings:
        return []

    top_films = sorted(
        ratings.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_user_films]

    rated_films = set(ratings)
    scores = {}

    for film_idx, rating in top_films:
        neighbors = find_similar_films(
            film_idx=film_idx,
            film_matrix=film_matrix,
            n_neighbors=n_neighbors,
            ban_list=list(rated_films)
        )

        for neighbor in neighbors:
            idx = neighbor["film_idx"]

            scores[idx] = (
                scores.get(idx, 0.0)
                + neighbor["similarity"] * rating / 10
            )

    return [
        idx
        for idx, score in sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n_recommendations]
    ]