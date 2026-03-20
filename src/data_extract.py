import kagglehub
import os
import shutil

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

top_spotify_songs_path = kagglehub.dataset_download("arnavvvvv/spotify-music")
spotify_dataset_path = kagglehub.dataset_download("ambaliyagati/spotify-dataset-for-playing-around-with-sql")

def copy_dataset(source_path, destination_name):
    """Copy downloaded dataset to data/raw directory"""
    dest_path = os.path.join(RAW_DATA_DIR, destination_name)
    if os.path.exists(dest_path):
        shutil.rmtree(dest_path)
    shutil.copytree(source_path, dest_path)
    print(f"Dataset copied to: {dest_path}")
    return dest_path

top_spotify_songs = copy_dataset(top_spotify_songs_path, "spotify-music")
spotify_dataset = copy_dataset(spotify_dataset_path, "spotify-dataset")

print("Path to dataset files:")
print(f"  - Top Spotify Songs: {top_spotify_songs}")
print(f"  - Spotify Dataset: {spotify_dataset}")