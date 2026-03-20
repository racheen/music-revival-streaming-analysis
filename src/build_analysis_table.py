from pathlib import Path
import numpy as np
import pandas as pd

from utils import map_loc_genre_to_bucket, map_spotify_genre_to_bucket


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INTERIM_DATA_DIR = PROJECT_ROOT / "data" / "interim"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


def deduplicate_spotify_music(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep the highest-streams record per normalized track+artist.
    """
    df = df.copy()
    df["streams"] = pd.to_numeric(df["streams"], errors="coerce")
    df = df.sort_values(["streams"], ascending=False)
    return df.drop_duplicates(subset=["track_artist_key"])


def deduplicate_spotify_tracks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep the highest-popularity record per normalized track+artist.
    """
    df = df.copy()
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce")
    df = df.sort_values(["popularity"], ascending=False)
    return df.drop_duplicates(subset=["track_artist_key"])


def build_spotify_modern_fact():
    df1 = pd.read_csv(INTERIM_DATA_DIR / "spotify_music_standardized.csv")
    df2 = pd.read_csv(INTERIM_DATA_DIR / "spotify_tracks_standardized.csv")

    df1 = deduplicate_spotify_music(df1)
    df2 = deduplicate_spotify_tracks(df2)

    keep_cols_df2 = [
        "track_artist_key",
        "id",
        "name",
        "genre",
        "artists",
        "album",
        "popularity",
        "duration_ms",
        "explicit",
    ]
    df2_small = df2[keep_cols_df2].copy()

    merged = df1.merge(df2_small, on="track_artist_key", how="left", indicator=True)

    merged["genre_matched"] = merged["_merge"].eq("both")
    merged.drop(columns=["_merge"], inplace=True)

    merged["genre_bucket"] = merged["genre"].apply(map_spotify_genre_to_bucket)

    out = PROCESSED_DATA_DIR / "spotify_modern_fact.csv"
    merged.to_csv(out, index=False)

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
            float(merged["genre_matched"].mean())
        ]
    })
    quality.to_csv(PROCESSED_DATA_DIR / "spotify_data_quality_summary.csv", index=False)

    print(f"✓ Saved spotify_modern_fact.csv ({len(merged)} rows)")
    print(f"✓ Genre match rate: {merged['genre_matched'].mean():.2%}")

    return merged


def build_spotify_genre_summary(spotify_fact: pd.DataFrame):
    df = spotify_fact.copy()

    numeric_cols = [
        "streams", "popularity", "danceability_%", "valence_%", "energy_%",
        "acousticness_%", "instrumentalness_%", "liveness_%", "speechiness_%",
        "bpm", "duration_ms"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    genre_summary = df.groupby("genre_bucket", dropna=False).agg(
        track_count=("track_artist_key", "count"),
        matched_track_count=("genre_matched", "sum"),
        total_streams=("streams", "sum"),
        avg_streams=("streams", "mean"),
        median_streams=("streams", "median"),
        avg_popularity=("popularity", "mean"),
        median_popularity=("popularity", "median"),
        avg_bpm=("bpm", "mean"),
        avg_danceability=("danceability_%", "mean"),
        avg_valence=("valence_%", "mean"),
        avg_energy=("energy_%", "mean"),
        avg_acousticness=("acousticness_%", "mean"),
        avg_instrumentalness=("instrumentalness_%", "mean"),
        avg_liveness=("liveness_%", "mean"),
        avg_speechiness=("speechiness_%", "mean"),
    ).reset_index()

    total_tracks = genre_summary["track_count"].sum()
    total_streams = genre_summary["total_streams"].sum()

    genre_summary["track_share"] = genre_summary["track_count"] / total_tracks
    genre_summary["streams_share"] = genre_summary["total_streams"] / total_streams

    genre_summary = genre_summary.sort_values("total_streams", ascending=False)

    genre_summary.to_csv(PROCESSED_DATA_DIR / "spotify_genre_summary.csv", index=False)
    print("✓ Saved spotify_genre_summary.csv")

    return genre_summary


def build_loc_genre_summary():
    """
    Build LOC genre summary using your uploaded genre revival file.
    """
    genre_counts = pd.read_csv(RAW_DATA_DIR / "most_frequently_revived_genres.csv")
    revivals = pd.read_csv(RAW_DATA_DIR / "revivals_detected_filtered.csv")
    
    genre_counts["genre_bucket"] = genre_counts["Genre"].apply(map_loc_genre_to_bucket)
    revivals["genre_bucket"] = revivals["Primary_Genre"].apply(map_loc_genre_to_bucket)
    # aggregate title-level revival metrics by primary genre

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

    loc_genre = genre_counts_bucketed.merge(loc_from_titles, on="genre_bucket", how="outer")

    loc_genre.to_csv(PROCESSED_DATA_DIR / "loc_genre_summary.csv", index=False)
    print("✓ Saved loc_genre_summary.csv")

    return loc_genre


def build_cross_era_table(spotify_genre: pd.DataFrame, loc_genre: pd.DataFrame):
    cross = spotify_genre.merge(loc_genre, on="genre_bucket", how="outer")

    cross["streams_rank"] = cross["total_streams"].rank(ascending=False, method="dense")
    cross["historical_revival_rank"] = cross["historical_genre_revival_count"].rank(ascending=False, method="dense")
    cross["avg_revival_strength_rank"] = cross["avg_revival_strength"].rank(ascending=False, method="dense")

    cross["rank_gap_streams_vs_history"] = cross["streams_rank"] - cross["historical_revival_rank"]

    cross.to_csv(PROCESSED_DATA_DIR / "cross_era_genre_table.csv", index=False)
    print("✓ Saved cross_era_genre_table.csv")

    # concentration summary
    valid_track_share = cross["track_share"].dropna()
    valid_stream_share = cross["streams_share"].dropna()

    def shannon_entropy(series):
        s = series[series > 0]
        return float(-(s * np.log2(s)).sum())

    concentration = pd.DataFrame({
        "metric": [
            "spotify_track_entropy",
            "spotify_stream_entropy",
            "genre_count_in_cross_table"
        ],
        "value": [
            shannon_entropy(valid_track_share),
            shannon_entropy(valid_stream_share),
            int(cross["genre_bucket"].nunique())
        ]
    })
    concentration.to_csv(PROCESSED_DATA_DIR / "concentration_summary.csv", index=False)
    print("✓ Saved concentration_summary.csv")

    return cross


def main():
    spotify_fact = build_spotify_modern_fact()
    spotify_genre = build_spotify_genre_summary(spotify_fact)
    loc_genre = build_loc_genre_summary()
    build_cross_era_table(spotify_genre, loc_genre)

    print("\n✓ Analysis tables built successfully.")
    print(f"Processed outputs saved in: {PROCESSED_DATA_DIR}")


if __name__ == "__main__":
    main()