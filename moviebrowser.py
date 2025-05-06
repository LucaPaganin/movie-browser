# -------------------------------------------------------------
# Istruzioni per l'utente (User Instructions):
# -------------------------------------------------------------
# 1. Install the required libraries:
#    pip install streamlit tmdbsimple
#
# 2. Create a file called `.streamlit/secrets.toml` in your project directory with the following content:
#
#    [tmdb]
#    api_key = "YOUR_TMDB_API_KEY"
#
# 3. Run the app:
#    streamlit run moviebrowser.py
#
# Replace YOUR_TMDB_API_KEY with your actual TMDB API key.

# -------------------------------------------------------------
# Import necessary libraries
import streamlit as st
import tmdbsimple as tmdb
import requests

# Set Streamlit page config
st.set_page_config(page_title="Browser Film TMDB", layout="wide")

# Set TMDB API key from Streamlit secrets
try:
    tmdb.API_KEY = st.secrets["tmdb"]["api_key"]
except Exception:
    st.error("Errore: impossibile trovare la chiave API TMDB. Aggiungi la tua chiave in .streamlit/secrets.toml.")
    st.stop()

# Helper function to get genres in Italian
@st.cache_data(show_spinner=False)
def get_genres():
    try:
        genres = tmdb.Genres()
        response = genres.movie_list(language='it-IT')
        return response['genres']
    except Exception:
        st.error("Errore durante il recupero dei generi.")
        return []

# Helper function to get watch providers for a movie (Italy only)
def get_watch_providers(movie_id):
    try:
        r = tmdb.Movies(movie_id).watch_providers(region="IT", language="it-IT")
        return r.get('results', {}).get('IT', {})
    except Exception:
        return {}

# Helper function to get genre name by id
def genre_names(genre_ids, all_genres):
    id_to_name = {g['id']: g['name'] for g in all_genres}
    return [id_to_name.get(i, str(i)) for i in genre_ids]

# Sidebar: Filters
st.sidebar.header("Filtri")
genres = get_genres()
genre_options = {g['name']: g['id'] for g in genres}
selected_genres = st.sidebar.multiselect("Genere", options=list(genre_options.keys()))

# Release year filter (single year or range)
anno_min, anno_max = 1900, 2025
anno_range = st.sidebar.slider("Anno di uscita", min_value=anno_min, max_value=anno_max, value=(2000, 2025))

# Rating filter
min_rating = st.sidebar.slider("Valutazione minima", min_value=0.0, max_value=10.0, value=0.0, step=0.1)

# Main area: Search bar
st.title("Browser Film TMDB")
search_term = st.text_input("Cerca un film per titolo", placeholder="Inserisci il titolo del film...")

# Button to apply filters (for clarity in Italian)
applica = st.button("Cerca" if search_term else "Applica filtri")

# Function to search movies by title
def search_movies_by_title(title):
    try:
        search = tmdb.Search()
        response = search.movie(query=title, language='it-IT', region='IT')
        return response['results']
    except Exception:
        st.error("Errore durante la ricerca dei film.")
        return []

# Function to discover movies by filters
def discover_movies(selected_genre_ids, year_range, min_vote):
    try:
        discover = tmdb.Discover()
        params = {
            'language': 'it-IT',
            'region': 'IT',
            'sort_by': 'popularity.desc',
            'vote_average.gte': min_vote,
            'primary_release_date.gte': f"{year_range[0]}-01-01",
            'primary_release_date.lte': f"{year_range[1]}-12-31"
        }
        if selected_genre_ids:
            params['with_genres'] = ','.join(str(g) for g in selected_genre_ids)
        response = discover.movie(**params)
        return response['results']
    except Exception:
        st.error("Errore durante il recupero dei film.")
        return []

# Main logic: search takes precedence
def get_movies():
    if search_term:
        return search_movies_by_title(search_term)
    else:
        return discover_movies(
            [genre_options[g] for g in selected_genres],
            anno_range,
            min_rating
        )

# Display results
if applica:
    movies = get_movies()
    st.subheader("Risultati ricerca")
    if not movies:
        st.info("Nessun film trovato.")
    else:
        for movie in movies:
            col1, col2 = st.columns([1, 3])
            with col1:
                if movie.get('poster_path'):
                    st.image(f"https://image.tmdb.org/t/p/w200{movie['poster_path']}", width=120)
                else:
                    st.write(":movie_camera:")
            with col2:
                st.markdown(f"**{movie.get('title', 'Senza titolo')}**")
                st.write(f"Data di uscita: {movie.get('release_date', 'N/A')}")
                st.write(f"Valutazione: {movie.get('vote_average', 'N/A')}")
                st.write(f"Generi: {', '.join(genre_names(movie.get('genre_ids', []), genres))}")
                # Watch providers
                providers = get_watch_providers(movie['id'])
                st.write("**Fornitori di visione:**")
                if not providers:
                    st.write("Nessun fornitore disponibile per l'Italia.")
                else:
                    for key, label in [("flatrate", "Streaming"), ("rent", "Noleggio"), ("buy", "Acquisto")]:
                        if key in providers:
                            st.write(f"_{label}_: " + ", ".join([p['provider_name'] for p in providers[key]]))
else:
    st.info("Imposta i filtri e premi 'Applica filtri' oppure cerca un film per titolo.")
