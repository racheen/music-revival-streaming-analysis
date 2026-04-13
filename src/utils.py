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

    text = text.lower().strip()

    # ------------------------------------------------
    # Remove ALL parentheses content (very important)
    # ------------------------------------------------
    text = re.sub(r"\(.*?\)", "", text)

    # ------------------------------------------------
    # Remove "feat", "ft", "featuring"
    # ------------------------------------------------
    text = re.sub(r"\b(feat|ft|featuring)\b.*", "", text)

    # ------------------------------------------------
    # Remove version / suffix info after "-"
    # ------------------------------------------------
    text = re.sub(
        r"\s*-\s*(remaster(ed)?|live|acoustic|remix|edit|version|single|deluxe|mono|stereo).*",
        "",
        text
    )

    # ------------------------------------------------
    # Remove common keywords
    # ------------------------------------------------
    text = re.sub(r"\bexplicit\b", "", text)
    text = re.sub(r"\bversion\b", "", text)

    # ------------------------------------------------
    # Remove punctuation
    # ------------------------------------------------
    text = re.sub(r"[^\w\s]", " ", text)

    # ------------------------------------------------
    # Normalize spaces
    # ------------------------------------------------
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

def extract_main_artist(artist):
    if not isinstance(artist, str):
        return ""
    return artist.split(",")[0].strip()

def _clean_genre_text(genre: str) -> str:
    if not isinstance(genre, str):
        return ""
    g = genre.lower().strip()
    g = g.replace("&", " and ")
    g = re.sub(r"[.]", "", g)
    g = re.sub(r"\s+", " ", g).strip()
    return g
def map_spotify_genre_to_bucket(genre: str) -> str:
    """
    Robust Spotify genre mapper using the actual uploaded Spotify genre list.
    IMPORTANT:
    - Missing/blank genres return 'Unmatched/Unknown'
    - Real mapped genres return shared BI buckets
    """

    g = _clean_genre_text(genre)

    if not g:
        return "Unmatched/Unknown"

    # ------------------------------------------------
    # Soundtrack / Stage / Screen
    # ------------------------------------------------
    if any(k in g for k in [
        "anime", "disney", "movie", "movies", "film", "soundtrack",
        "score", "broadway", "show tunes", "show-tunes"
    ]):
        return "Soundtrack/Stage/Screen"

    # ------------------------------------------------
    # Holiday / Children / Novelty / Comedy
    # ------------------------------------------------
    if any(k in g for k in [
        "children", "kids", "holidays", "holiday", "christmas",
        "comedy", "happy"
    ]):
        return "Holiday/Children/Novelty"

    # ------------------------------------------------
    # Gospel / Christian
    # ------------------------------------------------
    if any(k in g for k in [
        "gospel", "christian", "worship", "ccm"
    ]):
        return "Gospel/Christian"

    # ------------------------------------------------
    # Hip-Hop / Rap
    # ------------------------------------------------
    if any(k in g for k in [
        "hip-hop", "hip hop", "rap", "trap", "drill"
    ]):
        return "Hip-Hop/Rap"

    # ------------------------------------------------
    # R&B / Soul / Funk / Afrobeat
    # ------------------------------------------------
    if any(k in g for k in [
        "r-n-b", "rnb", "soul", "funk", "groove", "neo-soul",
        "motown", "afrobeat"
    ]):
        return "R&B/Soul/Funk"

    # ------------------------------------------------
    # Blues
    # ------------------------------------------------
    if "blues" in g:
        return "Blues"

    # ------------------------------------------------
    # Jazz
    # ------------------------------------------------
    if any(k in g for k in [
        "jazz", "bossanova", "bossa nova", "bebop", "bop", "swing"
    ]):
        return "Jazz"

    # ------------------------------------------------
    # Country / Folk / Acoustic / Bluegrass
    # ------------------------------------------------
    if any(k in g for k in [
        "country", "bluegrass", "honky-tonk"
    ]):
        return "Country"

    if any(k in g for k in [
        "folk", "acoustic", "guitar"
    ]):
        return "Folk/Bluegrass"

    # ------------------------------------------------
    # Rock / Metal / Punk / Alternative
    # ------------------------------------------------
    if any(k in g for k in [
        "rock", "alt-rock", "alternative", "hard-rock", "hardcore",
        "punk", "grunge", "emo", "garage", "goth",
        "metal", "heavy-metal", "black-metal", "death-metal",
        "grindcore"
    ]):
        return "Rock"

    # ------------------------------------------------
    # Popular / Pop
    # ------------------------------------------------
    if any(k in g for k in [
        "pop", "cantopop", "mandopop", "k-pop", "j-pop",
        "power-pop", "indie-pop", "british", "french", "german"
    ]):
        return "Popular/Pop"

    # ------------------------------------------------
    # Classical / Orchestral
    # ------------------------------------------------
    if any(k in g for k in [
        "classical", "opera", "piano", "orchestral", "chamber"
    ]):
        return "Classical/Opera/Orchestral"

    # ------------------------------------------------
    # Electronic / Dance
    # ------------------------------------------------
    if any(k in g for k in [
        "electronic", "electro", "electronica", "edm", "dance",
        "club", "chill", "ambient", "house", "deep-house",
        "chicago-house", "detroit-techno", "techno", "breakbeat",
        "drum-and-bass", "dnb", "dubstep", "hardstyle"
    ]):
        return "Electronic/Dance"

    # ------------------------------------------------
    # Reggae / Caribbean
    # ------------------------------------------------
    if any(k in g for k in [
        "reggae", "dub", "dancehall", "ska"
    ]):
        return "Reggae"

    # ------------------------------------------------
    # Latin / Regional
    # ------------------------------------------------
    if any(k in g for k in [
        "brazil", "forro", "latin", "latino", "reggaeton",
        "salsa", "bachata", "cumbia", "tejano", "mariachi",
        "vallenato", "pagode", "mpb"
    ]):
        return "Latin/Regional"

    return "Other"

def map_loc_genre_to_bucket(genre: str) -> str:
    """
    Robust mapping of LOC historical genres into broad shared buckets.
    Designed to align LOC archival labels with Spotify-led buckets.
    """

    g = _clean_genre_text(genre)

    if not g:
        return "Other"

    # ------------------------------------------------
    # Gospel / Christian / Sacred / Choral
    # ------------------------------------------------
    if any(k in g for k in [
        "gospel", "christian", "hymn", "hymns", "carol", "carols",
        "sacred", "spirituals", "psalms", "anthem", "anthems",
        "church music", "synagogue music", "communion service music",
        "offertories", "passion music", "magnificat", "vespers",
        "te deum", "salve regina", "sacred musical", "sacred musicals",
        "sacred vocal", "choruses sacred", "choruses, sacred",
        "masses", "mass ", "motets", "motet", "oratorio", "oratorios",
        "cantatas sacred", "cantatas, sacred", "solo cantatas sacred",
        "evangelistic sermons", "country gospel"
    ]):
        return "Gospel/Christian"

    # ------------------------------------------------
    # Hip-Hop / Rap
    # ------------------------------------------------
    if any(k in g for k in [
        "rap", "hip-hop", "hip hop", "hiphop", "christian rap", "gangsta rap"
    ]):
        return "Hip-Hop/Rap"

    # ------------------------------------------------
    # R&B / Soul / Funk
    # ------------------------------------------------
    if any(k in g for k in [
        "rhythm and blues", "rhythm & blues", "r and b", "rnb",
        "soul music", "soul", "funk", "doo-wop", "boogie woogie", "swamp pop"
    ]):
        return "R&B/Soul/Funk"

    # ------------------------------------------------
    # Blues
    # ------------------------------------------------
    if any(k in g for k in [
        "blues", "blues-rock"
    ]):
        return "Blues"

    # ------------------------------------------------
    # Jazz
    # ------------------------------------------------
    if any(k in g for k in [
        "jazz", "big band", "swing", "bebop", "bop", "cool jazz",
        "trad jazz", "dixieland", "latin jazz", "jazz-rock",
        "jazz vocals", "jazz ensemble", "ragtime", "piano music (jazz)",
        "guitar music (jazz)", "organ music (jazz)", "saxophone music (jazz)",
        "trumpet music (jazz)", "clarinet music (jazz)", "vibraphone music (jazz)"
    ]):
        return "Jazz"

    # ------------------------------------------------
    # Rock / Metal / Punk / Alternative
    # ------------------------------------------------
    if any(k in g for k in [
        "rock music", "rock and roll", "alternative rock", "folk-rock",
        "country rock", "christian rock", "rockabilly", "punk rock", "punk",
        "grunge", "emo", "new wave", "gothic rock", "psychedelic rock",
        "garage rock", "glam rock", "progressive rock", "hard rock",
        "heavy metal", "death metal", "black metal", "alternative metal",
        "progressive metal", "sludge metal", "thrash metal", "metal",
        "industrial music"
    ]):
        return "Rock"

    # ------------------------------------------------
    # Popular / Pop
    # ------------------------------------------------
    if any(k in g for k in [
        "popular music", "popular instrumental", "pop music",
        "latin pop", "synthpop", "easy listening", "muÃÅsica popular",
        "popular music.", "songs", "humorous songs", "love songs",
        "national songs", "patriotic music", "karaoke"
    ]) or g == "music" or g == "music." or g == "songs.":
        return "Popular/Pop"

    # ------------------------------------------------
    # Country / Americana / Roots
    # ------------------------------------------------
    if any(k in g for k in [
        "country music", "bluegrass", "honky-tonk", "old-time music",
        "western swing", "americana", "alternative country", "fiddle tunes",
        "square dance music", "jug band music"
    ]):
        return "Country"

    # ------------------------------------------------
    # Folk / Traditional
    # ------------------------------------------------
    if any(k in g for k in [
        "folk music", "folk songs", "traditional music", "ballads",
        "sea songs", "powwow songs", "folk dance music", "celtic music",
        "celtic harp", "native american flute music", "world beat", "world music"
    ]):
        return "Folk/Bluegrass"

    # ------------------------------------------------
    # Classical / Opera / Orchestral / Art music
    # ------------------------------------------------
    if any(k in g for k in [
        "opera", "operas", "orchestral music", "orchestra", "symphon",
        "requiem", "piano music", "organ music", "chamber music",
        "string quartet", "string quartets", "string orchestra",
        "sonata", "sonatas", "concerto", "concertos", "cantata", "cantatas",
        "suite", "suites", "overture", "overtures", "ballet", "ballets",
        "madrigal", "madrigals", "chorale", "chorale preludes",
        "concerti grossi", "canons", "fugues", "passacaglias", "toccatas",
        "rhapsodies", "romances", "polonaises", "mazurkas", "waltzes",
        "quartets", "quintets", "trios", "sextets", "septets", "octets", "nonets",
        "wind quintets", "wind sextets", "woodwind", "brass quintets",
        "brass quartets", "brass ensembles", "violin music", "cello music",
        "flute music", "harpsichord music", "lute music", "harp music",
        "oboe music", "clarinet music", "bassoon music", "viola music",
        "trumpet music", "trombone music", "band music", "instrumental ensemble",
        "instrumental music", "vocal music", "art songs", "gregorian chants",
        "liturgical dramas", "music appreciation", "choruses", "choruses secular"
    ]):
        return "Classical/Opera/Orchestral"

    # ------------------------------------------------
    # Electronic / Dance
    # ------------------------------------------------
    if any(k in g for k in [
        "electronic music", "electronic dance music", "electronica",
        "techno", "house", "dance music", "dance orchestra", "disco",
        "trance", "ambient", "new age", "computer music", "synthesizer music",
        "electronic organ", "dubstep", "jungle", "lounge music",
        "remixes", "music for relaxation", "music for meditation",
        "relaxation", "electronic and percussion", "electronic and violin",
        "electronic and cello", "piano and electronic", "flute and electronic"
    ]):
        return "Electronic/Dance"

    # ------------------------------------------------
    # Reggae / Caribbean
    # ------------------------------------------------
    if any(k in g for k in [
        "reggae", "dub", "dancehall", "ska", "soca"
    ]):
        return "Reggae"

    # ------------------------------------------------
    # Latin / Regional
    # ------------------------------------------------
    if any(k in g for k in [
        "salsa", "conjunto", "cumbia", "mariachi", "vallenato",
        "tejano", "bachata", "tangos", "tango", "mambos", "mambo",
        "banda", "rumbas", "rumba", "boleros", "bolero", "fados", "fado",
        "villancicos", "zarzuelas", "zarzuela", "flamenco", "bossa nova",
        "sambas", "samba", "merengues", "merengue", "corridos", "calypso",
        "cajun", "zydeco", "latin jazz", "latin pop", "reggaeton",
        "musica popular", "muÃÅsica popular"
    ]):
        return "Latin/Regional"

    # ------------------------------------------------
    # Soundtrack / Stage / Screen / Broadcast
    # ------------------------------------------------
    if any(k in g for k in [
        "motion picture music", "film music", "film soundtracks",
        "television music", "radio music", "radio programs musical",
        "radio operas", "radio plays", "musicals", "musicals.",
        "music theater", "stage music", "incidental music", "dramatic music",
        "production music", "animated film music", "burlesque", "revues",
        "masques with music", "monologues with music"
    ]):
        return "Soundtrack/Stage/Screen"

    # ------------------------------------------------
    # Holiday / Children / Novelty / Comedy
    # ------------------------------------------------
    if any(k in g for k in [
        "christmas music", "christmas", "easter music", "holiday",
        "children", "children's songs", "childrens songs", "songs for children",
        "nursery rhymes", "lullabies", "children's stories", "humorous music",
        "humorous recitations", "comedy", "stand-up comedy", "comedy sketches",
        "novelty", "singing games", "dance for children"
    ]):
        return "Holiday/Children/Novelty"

    # ------------------------------------------------
    # Explicit non-genre / topic / people labels
    # ------------------------------------------------
    if any(k in g for k in [
        "world war", "september 11", "indians of north america", "jews",
        "mexican americans", "african americans", "police", "presidents",
        "women", "men", "murder", "interviews", "stories", "poetry",
        "fiction", "literature", "history", "religion", "christian life",
        "spiritual life", "nature", "animals", "families", "marriage",
        "lawyers", "doctors", "journalists", "private investigators",
        "fictitious character", "terrorism", "war", "holocaust",
        "actors", "authors", "architects", "baseball players", "politicians"
    ]):
        return "Other"

    return "Other"