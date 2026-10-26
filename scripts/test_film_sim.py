from pathlib import Path
import pandas as pd
import numpy as np
from src.recommenders.film_similarity import *

DB_PATH = Path("data/films.json")
COLUMNS1 = [
    'year', 'rating', 'watched', 'liked', 'duration', 'actors', 
    'director',  'studio', 'country', 'genres', 'themes'
]
COLUMNS = [
    "rating", "genres", "themes"
]

def main():
    original_df = pd.read_json(DB_PATH)

    df = original_df[COLUMNS]

    df = prepare_films(
        df,
        drop_obvious_features=False
    )

    df = df.fillna(df.mean())

    df = standardize_films(df)

    df = df.reset_index(drop=True)

    print(df.index)

    film_matrix = build_film_matrix(df)

    print("Matrix shape: ", film_matrix.shape)

    # similar = find_similar_films(
    #     film_idx=71, # 71 - LOTR: Followship of the Ring
    #     film_matrix=film_matrix,
    #     n_neighbors=50
    # )

    # for film in similar:
    #     print(film)
    #     print()

    # print(
    #     explain_similarity(
    #         df,
    #         film_idx_1=71,
    #         film_idx_2=643
    #     ).to_string(index=False)
    # )

    print(recommend(
        original_df,
        film_matrix,
        "xaxamlo"
    ), sep="\n")



if __name__ == "__main__":
    main()