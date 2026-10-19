from pathlib import Path
from src.recommenders.data import load_cached_recommender_data
from src.recommenders.als import ExplicitALS
import numpy as np

CACHE_DIR = Path("artifacts/recommender")
USERNAME = "xaxamlo"

def main() -> None:
    data = load_cached_recommender_data(CACHE_DIR)

    model = ExplicitALS(
        n_factors=32,
        regularization=10.0,
        n_iterations=20
    )

    model.fit(data.ratings)

    user_idx = data.user_to_idx[USERNAME]

    recommendations = model.recommend(
        user_idx=user_idx,
        ratings=data.ratings,
        n_recommendations=20
    )

    film_rating_counts = np.diff(
        data.ratings.tocsc().indptr
    )

    for rank, film_idx in enumerate(recommendations, start=1):
        print(f"{rank:>2}. {str(data.films[film_idx]):<45} score= {model.predict(user_idx,film_idx):.2f} ratings={film_rating_counts[film_idx]}")

if __name__ == "__main__":
    main()