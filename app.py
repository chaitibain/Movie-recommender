import streamlit as st
import pickle
import requests
import json
import os

# ---------- CONFIG ----------
st.set_page_config(page_title="Netflix Recommender", layout="wide")

# ---------- USER FILE ----------
USER_FILE = "users.json"

# ---------- LOAD USERS ----------
def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

# ---------- AUTH ----------
def signup(username, password):
    users = load_users()
    if username in users:
        return False
    users[username] = password
    save_users(users)
    return True

def login(username, password):
    users = load_users()
    return username in users and users[username] == password

# ---------- SESSION ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------- LOGIN UI ----------
if not st.session_state.logged_in:
    st.title("🔐 Login / Signup")

    option = st.radio("Choose", ["Login", "Signup"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Signup":
        if st.button("Create Account"):
            if signup(username, password):
                st.success("Account created! Please login.")
            else:
                st.error("User already exists")

    if option == "Login":
        if st.button("Login"):
            if login(username, password):
                st.session_state.logged_in = True
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ---------- LOGOUT ----------
if st.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ---------- LOAD DATA ----------
movies = pickle.load(open('movies.pkl','rb'))
similarity = pickle.load(open('similarity.pkl','rb'))

# ---------- API KEY ----------
API_KEY = "4f93bec11651c73b30bae4f07056b747"   # 🔴 put your real key here

# ---------- FETCH DETAILS ----------
def fetch_movie_details(movie_name):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={movie_name}"

    try:
        response = requests.get(url)
        data = response.json()

        if 'results' in data and len(data['results']) > 0:
            result = data['results'][0]

            poster_path = result.get('poster_path')
            rating = result.get('vote_average')
            overview = result.get('overview')
            movie_id = result.get('id')

            poster_url = (
                "https://image.tmdb.org/t/p/w500" + poster_path
                if poster_path else None
            )

            return poster_url, rating, overview, movie_id

    except:
        pass

    return None, None, "No description available", None

# ---------- FETCH TRAILER ----------
def fetch_trailer(movie_id):
    if movie_id is None:
        return None

    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={API_KEY}"

    try:
        data = requests.get(url).json()

        if 'results' in data:
            for video in data['results']:
                if video['type'] == "Trailer":
                    return f"https://www.youtube.com/watch?v={video['key']}"

    except:
        pass

    return None

# ---------- RECOMMEND ----------
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = similarity[index]

    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    names = []
    details = []

    for i in movies_list:
        movie_title = movies.iloc[i[0]].title   # ✅ FIXED
        names.append(movie_title)
        details.append(fetch_movie_details(movie_title))

    return names, details

# ---------- UI ----------
st.markdown("<h1 style='text-align:center;color:#E50914;'>🎬 NETFLIX RECOMMENDER</h1>", unsafe_allow_html=True)

selected_movie = st.selectbox("🔍 Search Movie", movies['title'].values)

if st.button("Recommend"):
    with st.spinner("Fetching recommendations... 🍿"):

        names, details = recommend(selected_movie)
        cols = st.columns(5)

        for i in range(5):
            poster, rating, overview, movie_id = details[i]

            with cols[i]:
                if poster:
                    st.image(poster, use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/500x750?text=No+Image")

                st.markdown(f"**{names[i]}**")

                if rating:
                    st.write(f"⭐ {rating}")

                st.caption(overview[:100] + "...")

                trailer = fetch_trailer(movie_id)
                if trailer:
                    st.markdown(f"[▶ Watch Trailer]({trailer})")
