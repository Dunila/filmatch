from pathlib import Path

from src.recommenders.data import load_recommender_data
from src.recommenders.user_cf import find_similar_user, recommend


DB_PATH = Path("data/parsed_data.db")

USERNAME = "xaxamlo"

def main() -> None:
    data = load_recommender_data(DB_PATH)

    user_idx = data.user_to_idx[USERNAME]

    print()
    print(f"User: {USERNAME}")
    print(
        f"Ratings: \n{data.ratings[user_idx].nnz:,}"
    )

    similar_users = find_similar_user(
        data=data,
        username=USERNAME,
        n_neighbors=20,
        min_common_films=20
    )

    print("Similar users")
    print("_" * 50)
    for rank, user in enumerate(similar_users, start=1):
        print(f"{rank:>2}. {user['user']:<30} similarity={user['similarity']:.4f} \ncommon={user['common_films']:,}")
        print("_________________")

    recommendations = recommend(
        data=data,
        username=USERNAME,
        n_recommendations=20,
        n_neighbors=50,
        min_common_films=20,
        min_neighbor_ratings=3
    )

    print()
    print("_" * 70)
    print("RECOMMENDATIONS")

    for rank, rec in enumerate(recommendations, start=1):
        print(f"{rank:>2}. {rec['film']:<45} score={rec['predicted_rating']:.2f}")
        print(f"neighbors: {rec['neighbor_ratings']}")
        print()

if __name__ == "__main__":
    main()