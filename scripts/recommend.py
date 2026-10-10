import argparse
from pathlib import Path
from time import perf_counter

from src.recommenders.data import load_cached_recommender_data
from src.recommenders.user_cf import recommend


CACHE_DIR = Path("artifacts/recommender")

def main() -> None:
    start = perf_counter()

    #parsing arguments from CLI
    parser = argparse.ArgumentParser(
        description="Filmatch movie recommender"
    )

    parser.add_argument(
        "--user",
        type=str,
        required=True,
        help="Letterboxd username"
    )

    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of recommendations"
    )

    args = parser.parse_args()

    #loading cached database TODO What if there is no cached database?
    data = load_cached_recommender_data(CACHE_DIR)

    username = args.user.lower()


    if username not in data.user_to_idx:
        print(f"User '{username}' not found in database")
        return None

    user_idx = data.user_to_idx[username]

    print()
    print(f"User {username}")
    print(f"Rated films: {data.ratings[user_idx].nnz:,}") #data ratings[user*film] matrix uid row .nnz - count non zero

    #generate recs
    recommendations = recommend(
        data=data,
        username=username,
        n_recommendations=args.top,
        n_neighbors=50,
        min_common_films=20,
        min_neighbor_ratings=3
    )

    print()
    print("RECOMMENDATIONS")
    print("_" * 50)

    if not recommendations:
        print("No recommendations found")
        return None

    #print recs
    for rank, rec in enumerate(recommendations, start=1):
        print(f"{rank:>2}. {rec['film']:<45} score={rec['predicted_rating']:.2f}")
        print(f"neighbors: {rec['neighbor_ratings']}")
        print()

    #checking performance time
    print("*************")
    print(f"Total time: {perf_counter() - start:.2f} sec")

if __name__ == "__main__":
    main()