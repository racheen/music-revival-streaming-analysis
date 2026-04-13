from pathlib import Path
import numpy as np
import pandas as pd
from rapidfuzz import process, fuzz

from utils import map_loc_genre_to_bucket, map_spotify_genre_to_bucket


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INTERIM_DATA_DIR = PROJECT_ROOT / "data" / "interim"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------
# DEDUP
# ------------------------------------------------
def deduplicate_spotify_music(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["streams"] = pd.to_numeric(df["streams"], errors="coerce")
    df = df.sort_values(["streams"], ascending=False)
    return df.drop_duplicates(subset=["track_artist_key"])


def deduplicate_spotify_tracks(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce")
    df = df.sort_values(["popularity"], ascending=False)
    return df.drop_duplicates(subset=["track_artist_key"])


# ------------------------------------------------
# FUZZY MATCH FUNCTION
# ------------------------------------------------
def build_fuzzy_match(df1, df2):
    df2 = df2.copy()

    df2["combined_key"] = df2["track_name_norm"] + " " + df2["artist_name_norm"]
    choices = df2["combined_key"].tolist()
    lookup = dict(zip(df2["combined_key"], df2.index))

    def fuzzy_match(row):
        query = row["track_name_norm"] + " " + row["artist_name_norm"]

        match = process.extractOne(
            query,
            choices,
            scorer=fuzz.token_sort_ratio
        )

        if match:
            match_key, score, _ = match
            if score >= 85:
                return lookup[match_key]
        return None

    df1["match_index"] = df1.apply(fuzzy_match, axis=1)
    return df1


# ------------------------------------------------
# BUILD FACT TABLE
# ------------------------------------------------
def build_spotify_modern_fact():
    df1 = pd.read_csv(INTERIM_DATA_DIR / "spotify_music_standardized.csv")
    df2 = pd.read_csv(INTERIM_DATA_DIR / "spotify_tracks_standardized.csv")

    df1 = deduplicate_spotify_music(df1)
    df2 = deduplicate_spotify_tracks(df2)

    df1 = build_fuzzy_match(df1, df2)

    df2 = df2.reset_index()

    merged = df1.merge(
        df2,
        left_on="match_index",
        right_on="index",
        how="left"
    )

    merged["genre_matched"] = merged["match_index"].notna()
    
    if "track_artist_key_x" in merged.columns:
        merged["track_artist_key"] = merged["track_artist_key_x"]

    drop_cols = [c for c in ["track_artist_key_x", "track_artist_key_y", "index"] if c in merged.columns]
    merged = merged.drop(columns=drop_cols)

    merged["genre_bucket"] = merged["genre"].apply(map_spotify_genre_to_bucket)

    out = PROCESSED_DATA_DIR / "spotify_modern_fact.csv"
    merged.to_csv(out, index=False)

    match_rate = merged["genre_matched"].mean()

    quality = pd.DataFrame({
        "metric": [
            "dataset1_rows_after_dedup",
            "dataset2_rows_after_dedup",
            "merged_rows",
            "rows_with_genre_match",
            "genre_match_rate"
        ],
        "value": [
            len(df1),
            len(df2),
            len(merged),
            int(merged["genre_matched"].sum()),
            float(match_rate)
        ]
    })

    quality.to_csv(PROCESSED_DATA_DIR / "spotify_data_quality_summary.csv", index=False)

    print("Columns in spotify_fact:", merged.columns.tolist())
    print(f"✓ Match rate (fuzzy): {match_rate:.2%}")

    return merged


# ------------------------------------------------
# GENRE SUMMARY
# ------------------------------------------------
def build_spotify_genre_summary(spotify_fact: pd.DataFrame):
    df = spotify_fact.copy()

    # ONLY VALID MATCHES
    df = df[df["genre_matched"] == True]

    genre_summary = df.groupby("genre_bucket").agg(
        track_count=("track_artist_key", "count"),
        total_streams=("streams", "sum"),
        avg_popularity=("popularity", "mean")
    ).reset_index()

    total_streams = genre_summary["total_streams"].sum()

    genre_summary["streams_share"] = genre_summary["total_streams"] / total_streams

    genre_summary = genre_summary.sort_values("total_streams", ascending=False)

    genre_summary.to_csv(PROCESSED_DATA_DIR / "spotify_genre_summary.csv", index=False)

    return genre_summary


# ------------------------------------------------
# LOC SUMMARY
# ------------------------------------------------
def build_loc_genre_summary():
    genre_counts = pd.read_csv(RAW_DATA_DIR / "most_frequently_revived_genres.csv")
    revivals = pd.read_csv(RAW_DATA_DIR / "revivals_detected_filtered.csv")

    genre_counts["genre_bucket"] = genre_counts["Genre"].apply(map_loc_genre_to_bucket)
    revivals["genre_bucket"] = revivals["Primary_Genre"].apply(map_loc_genre_to_bucket)

    loc = genre_counts.groupby("genre_bucket").agg(
        historical_genre_revival_count=("count", "sum")
    ).reset_index()

    loc_from_titles = revivals.groupby("genre_bucket").agg(
        revived_title_count=("Title_Normalized", "count"),
        avg_revival_strength=("Revival_Strength", "mean"),
        median_revival_strength=("Revival_Strength", "median"),
        avg_time_span=("Time_Span", "mean"),
        avg_decades_count=("Decades_Count", "mean"),
        max_revival_strength=("Revival_Strength", "max"),
    ).reset_index()

    genre_counts = genre_counts.rename(columns={
        "count": "historical_genre_revival_count",
        "Percentage": "historical_genre_revival_percentage"
    })

    genre_counts_bucketed = genre_counts.groupby("genre_bucket", as_index=False).agg(
        historical_genre_revival_count=("historical_genre_revival_count", "sum"),
        historical_genre_revival_percentage=("historical_genre_revival_percentage", "sum")
    )

    loc = genre_counts_bucketed.merge(loc_from_titles, on="genre_bucket", how="outer")

    loc.to_csv(PROCESSED_DATA_DIR / "loc_genre_summary.csv", index=False)

    return loc


# ------------------------------------------------
# CROSS ERA
# ------------------------------------------------
def build_cross_era_table(spotify_genre, loc_genre):
    cross = spotify_genre.merge(loc_genre, on="genre_bucket", how="outer")

    cross["streams_rank"] = cross["total_streams"].rank(ascending=False)
    cross["historical_rank"] = cross["historical_genre_revival_count"].rank(ascending=False)

    cross["rank_gap"] = cross["streams_rank"] - cross["historical_rank"]

    cross.to_csv(PROCESSED_DATA_DIR / "cross_era_genre_table.csv", index=False)

    return cross


# ------------------------------------------------
# MAIN
# ------------------------------------------------
def main():
    spotify_fact = build_spotify_modern_fact()
    spotify_genre = build_spotify_genre_summary(spotify_fact)
    loc_genre = build_loc_genre_summary()
    build_cross_era_table(spotify_genre, loc_genre)

    print("\n DONE — A+ PIPELINE READY")


if __name__ == "__main__":
    main()