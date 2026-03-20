# Cross-Era Music Analytics

### Historical Genre Revival vs Streaming-Era Dominance

## Project Overview

This project investigates the relationship between **historical music
genre revival** and **modern streaming-era dominance** using a Business
Intelligence framework.

Building on prior analysis of **553,852 Library of Congress (LOC)
bibliographic records**, this project integrates historical revival
metrics with contemporary Spotify datasets to examine:

-   Do historically persistent genres dominate modern streaming
    platforms?
-   Is streaming distribution concentrated or diverse?
-   How do archival preservation patterns compare to platform-driven
    visibility?

The project combines **data engineering, statistical analysis, and
interactive BI visualization** into a reproducible pipeline and
dashboard.

------------------------------------------------------------------------

## Objectives

-   Integrate multi-source datasets (LOC + Spotify)
-   Standardize and map genre classifications across eras
-   Compare historical revival metrics with streaming performance
-   Measure genre concentration using entropy
-   Deliver an interactive BI dashboard for exploration

------------------------------------------------------------------------

## Data Sources

### Historical (LOC)

-   553,852 bibliographic records (1000--2016)
-   Derived metrics:
    -   Genre Revival Strength
    -   Revival Frequency
    -   Longevity Indicators

### Spotify (Kaggle)

-   Track-level dataset:
    -   Streams, release data, audio features
-   Metadata dataset:
    -   Genre, album, popularity

------------------------------------------------------------------------

## Project Structure

    music-revival-streaming-analysis/
    │
    ├── data/
    │   ├── raw/                
    │   ├── interim/            
    │   └── processed/          
    │
    ├── notebooks/              
    ├── src/
    │   ├── utils.py
    │   ├── standardize_spotify.py
    │   ├── build_analysis_tables.py
    |   ├── data_extract.py
    │   └── app.py              
    │
    ├── requirements.txt
    └── README.md

------------------------------------------------------------------------

## Data Pipeline

1.  Standardize Spotify datasets\
2.  Merge datasets into a unified fact table\
3.  Map genres into unified buckets\
4.  Generate analysis tables\
5.  Build cross-era comparison metrics

------------------------------------------------------------------------

## How to Run

### Install dependencies

    pip install -r requirements.txt

### Run data pipeline

    python src/standardize_spotify.py
    python src/build_analysis_tables.py

### Launch dashboard

    streamlit run src/app.py

------------------------------------------------------------------------

## Key Outputs

-   spotify_modern_fact.csv\
-   spotify_genre_summary.csv\
-   loc_genre_summary.csv\
-   cross_era_genre_table.csv\
-   concentration_summary.csv

------------------------------------------------------------------------

## Dashboard Features

-   Overview metrics\
-   Genre explorer\
-   Cross-era comparison\
-   Title search\
-   Smart insight summaries


## Live Demo

**[View Live Dashboard](https://racheen-music-revival-streaming-analysis-srcapp-foh9jo.streamlit.app/)**
