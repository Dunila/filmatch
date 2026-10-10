from pathlib import Path

from src.recommenders.data import load_recommender_data, save_recommender_data


DB_PATH = Path("data/parsed_data.db")
CACHE_DIR = Path("artifacts/recommender")

def main() -> None:
    #load data for recs (RecommenderData class)
    data = load_recommender_data(DB_PATH)

    #save data in .npz and .npy
    save_recommender_data(
        data=data,
        cache_dir=CACHE_DIR
    )

if __name__ == "__main__":
    main()