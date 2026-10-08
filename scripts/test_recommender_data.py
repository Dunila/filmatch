from pathlib import Path
from src.recommenders.data import load_recommender_data

DB_PATH = Path("data/parsed_data.db")

def main() -> None:
    data = load_recommender_data(DB_PATH)

    print()
    print("Recomender data")
    print("=" * 50)

    print(f"Users: {len(data.users):,}")
    print(f"Films: {len(data.films):,}")

    print(f"Matrix shape: {data.ratings.shape}")
    print(f"Stored ratings: {data.ratings.nnz:,}")

    print()
    print("Matrix arrays:")
    print(f"data:    {data.ratings.data.dtype}")
    print(f"indices: {data.ratings.indices.dtype}")
    print(f"indptr:  {data.ratings.indptr.dtype}")

    memory_bytes = (
        data.ratings.data.nbytes
        + data.ratings.indices.nbytes
        + data.ratings.indptr.nbytes
    )

    print(
        f"Matrix memory: "
        f"{memory_bytes / 1024 ** 2:.2f} MB"
    )

    print()
    print("First users:")
    print(data.users[:5])

    print()
    print("First films:")
    print(data.films[:5])

if __name__ == "__main__":
    main()
