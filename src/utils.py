import re
import pandas as pd


def read_csv_safe(file_path: str, **kwargs) -> pd.DataFrame:
    encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252", "utf-16"]
    last_error = None

    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, **kwargs)
            print(f"✓ Read {file_path} with encoding={encoding}")
            return df
        except Exception as e:
            last_error = e

    raise ValueError(f"Could not read {file_path}. Last error: {last_error}")


def normalize_text(text):
    if not isinstance(text, str):
        return ""

    text = text.lower()

    patterns_to_remove = [
        r"\s*\(feat\.?\s+.*?\)",
        r"\s*\(ft\.?\s+.*?\)",
        r"\s*feat\.?\s+.*?(?=\s|$)",
        r"\s*ft\.?\s+.*?(?=\s|$)",
        r"\s*\(remastered.*?\)",
        r"\s*\(live.*?\)",
        r"\s*\(acoustic.*?\)",
        r"\s*\(remix.*?\)",
        r"\s*\(single.*?\)",
        r"\s*-\s*single\s*$",
        r"\s*-\s*remastered\s*$",
        r"\s*-\s*live\s*$",
        r"\s*-\s*acoustic\s*$",
        r"\s*-\s*remix\s*$",
        r"\bexplicit ver\b",
        r"\bexplicit version\b",
        r"\bver\b",
    ]

    for pattern in patterns_to_remove:
        text = re.sub(pattern, "", text)

    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def clean_artist_field(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.strip()
    separators = [",", "&", ";", " feat", " ft", " x ", " / "]
    lower = text.lower()

    positions = []
    for sep in separators:
        idx = lower.find(sep)
        if idx != -1:
            positions.append(idx)

    if positions:
        text = text[:min(positions)]

    return text.strip()


def _clean_genre_text(genre: str) -> str:
    if not isinstance(genre, str):
        return ""
    g = genre.lower().strip()
    g = g.replace("&", " and ")
    g = re.sub(r"[.]", "", g)
    g = re.sub(r"\s+", " ", g).strip()
    return g


def map_loc_genre_to_bucket(genre: str) -> str:
    """
    Map LOC revival genres into broad, analysis-friendly buckets.
    """
    g = _clean_genre_text(genre)

    if not g:
        return "Other"

    # Popular / Pop
    if (
        "popular music" in g
        or "pop music" in g
        or "power pop" in g
        or "indie pop" in g
        or g == "songs"
        or "popular instrumental music" in g
    ):
        return "Popular/Pop"

    # Rock / Metal / Alternative
    if (
        "rock music" in g
        or "rock and roll" in g
        or "alternative rock" in g
        or "folk-rock" in g
        or "punk" in g
        or "grunge" in g
        or "heavy metal" in g
        or "metal" in g
        or "emo" in g
        or "hard rock" in g
    ):
        return "Rock"

    # Jazz
    if "jazz" in g or "big band" in g or "bebop" in g or "swing" in g:
        return "Jazz"

    # Country / Bluegrass / Honky-tonk
    if "country music" in g or "bluegrass" in g or "honky-tonk" in g:
        return "Country"

    # Gospel / Christian
    if (
        "gospel" in g
        or "christian" in g
        or "hymn" in g
        or "worship" in g
        or "sacred music" in g
        or "spirituals" in g
        or "carols" in g
    ):
        return "Gospel/Christian"

    # Blues
    if "blues" in g:
        return "Blues"

    # Hip-Hop / Rap
    if "rap" in g or "hip-hop" in g or "hip hop" in g:
        return "Hip-Hop/Rap"

    # R&B / Soul / Funk
    if (
        "rhythm and blues" in g
        or "soul music" in g
        or "funk" in g
        or "r and b" in g
        or "rnb" in g
    ):
        return "R&B/Soul/Funk"

    # Folk
    if "folk music" in g or "folk songs" in g:
        return "Folk/Bluegrass"

    # Classical / Opera / Orchestral / Piano / Organ / Instrumental art music
    if (
        "opera" in g
        or "operas" in g
        or "classical" in g
        or "orchestral music" in g
        or "symphon" in g
        or "requiem" in g
        or "piano music" in g
        or "organ music" in g
        or "chamber music" in g
        or "violin music" in g
        or "sonatas" in g
        or "concertos" in g
        or "cantatas" in g
        or "motets" in g
        or "choruses" in g
        or "masses" in g
    ):
        return "Classical/Opera/Orchestral"

    # Electronic / Dance / Disco / New Age
    if (
        "electronic" in g
        or "dance music" in g
        or "dance orchestra" in g
        or "electronic dance music" in g
        or "disco" in g
        or "house" in g
        or "techno" in g
        or "new age" in g
        or "ambient" in g
    ):
        return "Electronic/Dance"

    # Reggae
    if "reggae" in g or "dub" in g or "dancehall" in g or "reggaeton" in g:
        return "Reggae"

    # Soundtrack / musical / film / stage
    if (
        "motion picture music" in g
        or "film music" in g
        or "musicals" in g
        or "show tunes" in g
        or "stage music" in g
        or "television music" in g
    ):
        return "Soundtrack/Stage/Screen"

    # Holiday / children / novelty
    if (
        "christmas music" in g
        or "children" in g
        or "children's songs" in g
        or "holiday" in g
        or "novelty" in g
    ):
        return "Holiday/Children/Novelty"

    return "Other"


def map_spotify_genre_to_bucket(genre: str) -> str:
    """
    Map Spotify microgenres into the same broad bucket system.
    """
    g = _clean_genre_text(genre)

    if not g:
        return "Other"

    # Popular / Pop
    if g in {"pop", "indie-pop", "power-pop", "pop-film", "k-pop", "j-pop", "cantopop", "mandopop"}:
        return "Popular/Pop"

    # Rock
    if g in {
        "rock", "alt-rock", "alternative", "hard-rock", "punk-rock", "punk",
        "psych-rock", "grunge", "emo", "j-rock", "metal", "heavy-metal",
        "black-metal", "death-metal", "metalcore", "metal-misc", "hardcore",
        "grindcore", "industrial", "goth"
    }:
        return "Rock"

    # Jazz
    if g in {"jazz", "bossanova"}:
        return "Jazz"

    # Country
    if g in {"country", "bluegrass", "honky-tonk"}:
        return "Country"

    # Gospel / Christian
    if g in {"gospel"}:
        return "Gospel/Christian"

    # Blues
    if g in {"blues"}:
        return "Blues"

    # Hip-Hop / Rap
    if g in {"hip-hop"}:
        return "Hip-Hop/Rap"

    # R&B / Soul / Funk
    if g in {"r-n-b", "funk", "groove"}:
        return "R&B/Soul/Funk"

    # Folk
    if g in {"folk", "acoustic"}:
        return "Folk/Bluegrass"

    # Classical
    if g in {"classical", "opera", "piano"}:
        return "Classical/Opera/Orchestral"

    # Electronic / Dance
    if g in {
        "electronic", "edm", "dance", "disco", "house", "deep-house",
        "progressive-house", "chicago-house", "detroit-techno", "minimal-techno",
        "techno", "club", "dubstep", "post-dubstep", "drum-and-bass",
        "breakbeat", "electro", "idm", "ambient", "chill", "new-age",
        "party", "j-dance", "dancehall"
    }:
        return "Electronic/Dance"

    # Reggae
    if g in {"reggae", "dub", "reggaeton"}:
        return "Reggae"

    # Soundtrack / screen / stage
    if g in {"movies", "disney", "anime", "show-tunes" if False else ""}:
        return "Soundtrack/Stage/Screen"

    # Holiday / children / novelty
    if g in {"children", "kids", "holidays", "comedy", "happy"}:
        return "Holiday/Children/Novelty"

    # Latin as its own fallback family; if you prefer, move to Other
    if g in {"latin", "latino", "brazil", "mpb", "pagode", "forro"}:
        return "Other"

    return "Other"