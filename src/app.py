from pathlib import Path
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = PROJECT_ROOT / "data" / "processed"
RAW = PROJECT_ROOT / "data" / "raw"

st.set_page_config(
    page_title="Cross-Era Music BI Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Historical Genre Revival and Streaming-Era Dominance")
st.caption("Cross-era Business Intelligence dashboard for comparing LOC revival patterns with Spotify-era streaming metrics.")

@st.cache_data
def load_data():
    spotify_fact = pd.read_csv(PROCESSED / "spotify_modern_fact.csv")
    spotify_genre = pd.read_csv(PROCESSED / "spotify_genre_summary.csv")
    loc_genre = pd.read_csv(PROCESSED / "loc_genre_summary.csv")
    cross = pd.read_csv(PROCESSED / "cross_era_genre_table.csv")
    quality = pd.read_csv(PROCESSED / "spotify_data_quality_summary.csv")
    concentration = pd.read_csv(PROCESSED / "concentration_summary.csv")
    return spotify_fact, spotify_genre, loc_genre, cross, quality, concentration


spotify_fact, spotify_genre, loc_genre, cross, quality, concentration = load_data()


def safe_value(df, metric_name):
    row = df[df["metric"] == metric_name]
    if row.empty:
        return None
    return row["value"].iloc[0]


def fmt_big_number(x):
    if pd.isna(x):
        return "N/A"
    x = float(x)
    if x >= 1e9:
        return f"{x/1e9:.2f}B"
    if x >= 1e6:
        return f"{x/1e6:.2f}M"
    if x >= 1e3:
        return f"{x/1e3:.2f}K"
    return f"{x:.0f}"


def render_bar_chart(df, x_col, y_col, title, top_n=None):
    plot_df = df.copy()
    if top_n is not None:
        plot_df = plot_df.head(top_n)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(plot_df[x_col], plot_df[y_col])
    ax.set_title(title)
    ax.set_xlabel(x_col.replace("_", " ").title())
    ax.set_ylabel(y_col.replace("_", " ").title())
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)


def generate_genre_insight(row):
    genre = row.get("genre_bucket", "Unknown")
    hist_count = row.get("historical_genre_revival_count")
    hist_rank = row.get("historical_revival_rank")
    stream_rank = row.get("streams_rank")
    stream_share = row.get("streams_share")
    avg_pop = row.get("avg_popularity")
    rank_gap = row.get("rank_gap_streams_vs_history")

    parts = [f"**{genre}** shows a distinctive cross-era pattern."]

    if pd.notna(hist_count):
        parts.append(f"It has a historical revival count of **{int(hist_count)}**.")
    if pd.notna(hist_rank):
        parts.append(f"Its historical revival rank is **{int(hist_rank)}**.")
    if pd.notna(stream_rank):
        parts.append(f"Its streaming rank is **{int(stream_rank)}**.")
    if pd.notna(stream_share):
        parts.append(f"It accounts for **{stream_share*100:.2f}%** of matched streaming volume.")
    if pd.notna(avg_pop):
        parts.append(f"Its average Spotify popularity is **{avg_pop:.2f}**.")
    if pd.notna(rank_gap):
        if rank_gap > 0:
            parts.append("This genre performs **worse in streaming than in historical revival**, suggesting archival persistence does not fully convert into platform dominance.")
        elif rank_gap < 0:
            parts.append("This genre performs **better in streaming than in historical revival**, suggesting strong modern platform visibility.")
        else:
            parts.append("Its historical and streaming ranks are closely aligned.")

    return " ".join(parts)

def read_csv_safe(file_path):
    """
    Read CSV file with automatic encoding detection
    """
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            print(f"  ✓ Successfully read with encoding: {encoding}")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"  Error with {encoding}: {e}")
            continue
    
    # If all fail, try with errors='ignore'
    print(f"  ⚠ Using fallback encoding with error handling")
    df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
    return df


page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Genre Explorer", "Cross-Era Comparison", "Title Explorer", "Spotify EDA", "Smart Insights"]
)

if page == "Overview":
    st.header("Overview")

    total_tracks = len(spotify_fact)
    match_rate = safe_value(quality, "genre_match_rate")
    genre_count = cross["genre_bucket"].nunique()
    stream_entropy = safe_value(concentration, "spotify_stream_entropy")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Modern Tracks", f"{total_tracks:,}")
    c2.metric("Genre Match Rate", f"{match_rate*100:.2f}%" if match_rate is not None else "N/A")
    c3.metric("Cross-Era Genres", f"{genre_count}")
    c4.metric("Stream Entropy", f"{stream_entropy:.4f}" if stream_entropy is not None else "N/A")

    st.subheader("Top Genres by Total Streams")
    render_bar_chart(
        spotify_genre.sort_values("total_streams", ascending=False),
        "genre_bucket",
        "total_streams",
        "Top Genres by Total Streams",
        top_n=10
    )

    st.subheader("Top Historical Genres by Revival Count")
    if "historical_genre_revival_count" in loc_genre.columns:
        render_bar_chart(
            loc_genre.sort_values("historical_genre_revival_count", ascending=False),
            "genre_bucket",
            "historical_genre_revival_count",
            "Top Historical Genres by Revival Count",
            top_n=10
        )

    with st.expander("Data Quality Summary"):
        st.dataframe(quality, use_container_width=True)

    with st.expander("Concentration Summary"):
        st.dataframe(concentration, use_container_width=True)

elif page == "Genre Explorer":
    st.header("Genre Explorer")

    genres = sorted([g for g in cross["genre_bucket"].dropna().unique()])
    selected_genre = st.selectbox("Select Genre", genres)

    row = cross[cross["genre_bucket"] == selected_genre]
    if not row.empty:
        row = row.iloc[0]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Historical Revival Count", f"{int(row['historical_genre_revival_count'])}" if pd.notna(row.get("historical_genre_revival_count")) else "N/A")
        c2.metric("Total Streams", fmt_big_number(row.get("total_streams")))
        c3.metric("Stream Share", f"{row['streams_share']*100:.2f}%" if pd.notna(row.get("streams_share")) else "N/A")
        c4.metric("Avg Popularity", f"{row['avg_popularity']:.2f}" if pd.notna(row.get("avg_popularity")) else "N/A")

        st.subheader("Cross-Era Metrics")
        st.dataframe(pd.DataFrame(row).reset_index(), use_container_width=True)

        tracks = spotify_fact[spotify_fact["genre_bucket"] == selected_genre].copy()
        if not tracks.empty:
            st.subheader("Top Tracks in Selected Genre")
            cols_to_show = [
                "track_name", "artist(s)_name", "album",
                "streams", "popularity", "released_year"
            ]
            cols_to_show = [c for c in cols_to_show if c in tracks.columns]
            tracks = tracks.sort_values("streams", ascending=False)
            st.dataframe(tracks[cols_to_show].head(20), use_container_width=True)

elif page == "Cross-Era Comparison":
    st.header("Cross-Era Comparison")

    sort_col = st.selectbox(
        "Sort by",
        [
            "historical_genre_revival_count",
            "total_streams",
            "streams_share",
            "historical_revival_rank",
            "streams_rank",
            "rank_gap_streams_vs_history"
        ]
    )

    ascending = st.checkbox("Ascending sort", value=False)

    display_cols = [
        "genre_bucket",
        "historical_genre_revival_count",
        "avg_revival_strength",
        "total_streams",
        "streams_share",
        "historical_revival_rank",
        "streams_rank",
        "rank_gap_streams_vs_history"
    ]
    display_cols = [c for c in display_cols if c in cross.columns]

    st.dataframe(
        cross.sort_values(sort_col, ascending=ascending)[display_cols],
        use_container_width=True
    )

    valid = cross.dropna(subset=["historical_genre_revival_count", "streams_share"]).copy()
    if not valid.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(valid["historical_genre_revival_count"], valid["streams_share"])
        ax.set_title("Historical Revival Count vs Streaming Share")
        ax.set_xlabel("Historical Revival Count")
        ax.set_ylabel("Streaming Share")
        plt.tight_layout()
        st.pyplot(fig)

elif page == "Title Explorer":
    st.header("Title Explorer")

    query = st.text_input("Search by Title")
    genre_filter = st.selectbox("Filter by Genre Bucket", ["All"] + sorted(spotify_fact["genre_bucket"].dropna().unique().tolist()))

    filtered = spotify_fact.copy()
    if genre_filter != "All":
        filtered = filtered[filtered["genre_bucket"] == genre_filter]

    if query:
        filtered = filtered[filtered["track_name"].astype(str).str.contains(query, case=False, na=False)]

    st.write(f"Results: {len(filtered)}")

    cols_to_show = [
        "track_name",
        "artist(s)_name",
        "genre_bucket",
        "genre",
        "album",
        "streams",
        "popularity",
        "released_year"
    ]
    cols_to_show = [c for c in cols_to_show if c in filtered.columns]

    st.dataframe(
        filtered.sort_values("streams", ascending=False)[cols_to_show].head(50),
        use_container_width=True
    )

elif page == "Smart Insights":
    st.header("Smart Insights")

    genres = sorted([g for g in cross["genre_bucket"].dropna().unique()])
    selected_genre = st.selectbox("Select Genre", genres, key="smart_genre")

    row = cross[cross["genre_bucket"] == selected_genre]
    if not row.empty:
        row = row.iloc[0]
        st.markdown(generate_genre_insight(row))
        with st.expander("Supporting Metrics"):
            st.dataframe(pd.DataFrame(row).reset_index(), use_container_width=True)

elif page == "Spotify EDA":

    st.title("Spotify Dataset – Exploratory Data Analysis")

    st.markdown("This section explores the raw Spotify datasets before integration.")
    st.info("This EDA supports data quality assessment and explains preprocessing decisions.")
    
    # =========================
    # LOAD DATA
    # =========================
    df1 = read_csv_safe(f"{RAW}/spotify-music/Popular_Spotify_Songs.csv")
    df2 = read_csv_safe(f"{RAW}/spotify-dataset/spotify_tracks.csv")

    # =========================
    # MISSING VALUES
    # =========================
    st.subheader("Missing Values")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Dataset 1**")
        st.dataframe(df1.isnull().sum())

    with col2:
        st.markdown("**Dataset 2**")
        st.dataframe(df2.isnull().sum())

    # =========================
    # STREAM DISTRIBUTION
    # =========================
    st.subheader("Stream Distribution")

    fig, ax = plt.subplots()
    ax.hist(df1["streams"], bins=50)
    ax.set_title("Distribution of Streams")
    ax.set_xlabel("Streams")
    ax.set_ylabel("Frequency")
    st.pyplot(fig)

    st.markdown(
        "Streams are highly right-skewed, indicating concentration of attention among a small number of tracks."
    )

    # =========================
    # POPULARITY
    # =========================
    st.subheader("Popularity Distribution")

    fig, ax = plt.subplots()
    ax.hist(df2["popularity"], bins=30)
    ax.set_title("Popularity Distribution")
    st.pyplot(fig)

    # =========================
    # AUDIO FEATURES
    # =========================
    st.subheader("Audio Features")

    features = [
        "danceability_%",
        "energy_%",
        "valence_%"
    ]

    for feature in features:
        fig, ax = plt.subplots()
        ax.hist(df1[feature], bins=30)
        ax.set_title(f"{feature} Distribution")
        st.pyplot(fig)

    # =========================
    # TRACK DURATION
    # =========================
    st.subheader("Track Duration")

    fig, ax = plt.subplots()
    ax.hist(df2["duration_ms"] / 60000, bins=30)
    ax.set_title("Track Duration (minutes)")
    st.pyplot(fig)

    # =========================
    # GENRE DISTRIBUTION
    # =========================
    st.subheader("Spotify Genre Distribution")

    genre_counts = df2["genre"].value_counts().head(20)

    fig, ax = plt.subplots()
    genre_counts.plot(kind="bar", ax=ax)
    ax.set_title("Top 20 Spotify Genres")
    st.pyplot(fig)

    st.markdown(
        "Spotify genres are highly fragmented into microgenres, motivating the need for genre bucket mapping."
    )