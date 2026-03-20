import os
from pathlib import Path
import pandas as pd

from utils import read_csv_safe, normalize_text, clean_artist_field


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
INTERIM_DATA_DIR = PROJECT_ROOT / "data" / "interim"

INTERIM_DATA_DIR.mkdir(parents=True, exist_ok=True)


def standardize_dataset_1(df: pd.DataFrame) -> pd.DataFrame:
    """
    Popular_Spotify_Songs.csv
    """
    required = ["track_name", "artist(s)_name"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset 1 missing columns: {missing}")

    df_std = df.copy()

    df_std["track_name_raw"] = df_std["track_name"].astype(str)
    df_std["artist_name_raw"] = df_std["artist(s)_name"].apply(clean_artist_field)

    df_std["track_name_norm"] = df_std["track_name_raw"].apply(normalize_text)
    df_std["artist_name_norm"] = df_std["artist_name_raw"].apply(normalize_text)
    df_std["track_artist_key"] = df_std["track_name_norm"] + " | " + df_std["artist_name_norm"]

    return df_std


def standardize_dataset_2(df: pd.DataFrame) -> pd.DataFrame:
    """
    spotify_tracks.csv
    """
    required = ["name", "artists"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset 2 missing columns: {missing}")

    df_std = df.copy()

    df_std["track_name_raw"] = df_std["name"].astype(str)
    df_std["artist_name_raw"] = df_std["artists"].apply(clean_artist_field)

    df_std["track_name_norm"] = df_std["track_name_raw"].apply(normalize_text)
    df_std["artist_name_norm"] = df_std["artist_name_raw"].apply(normalize_text)
    df_std["track_artist_key"] = df_std["track_name_norm"] + " | " + df_std["artist_name_norm"]

    return df_std


def main():
    dataset1_path = RAW_DATA_DIR / "Popular_Spotify_Songs.csv"
    dataset2_path = RAW_DATA_DIR / "spotify_tracks.csv"

    print("Loading raw Spotify datasets...")
    df1 = read_csv_safe(dataset1_path)
    df2 = read_csv_safe(dataset2_path)

    print("Standardizing dataset 1...")
    df1_std = standardize_dataset_1(df1)

    print("Standardizing dataset 2...")
    df2_std = standardize_dataset_2(df2)

    out1 = INTERIM_DATA_DIR / "spotify_music_standardized.csv"
    out2 = INTERIM_DATA_DIR / "spotify_tracks_standardized.csv"

    df1_std.to_csv(out1, index=False)
    df2_std.to_csv(out2, index=False)

    print(f"✓ Saved: {out1}")
    print(f"✓ Saved: {out2}")

    print("\nSample keys from dataset 1:")
    print(df1_std[["track_name_raw", "artist_name_raw", "track_artist_key"]].head(5).to_string(index=False))

    print("\nSample keys from dataset 2:")
    print(df2_std[["track_name_raw", "artist_name_raw", "track_artist_key"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()