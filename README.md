# Using spotipy to interact with my Spotify library

---
### Prerequisites

In order to interact with the spotipy (python wrapper for the spotify API) it's necessary to follow the Spotify API [authorization guide](https://developer.spotify.com/documentation/general/guides/authorization-guide). \
Once you have a `spotify client id`, `spotify client secret` and a `redirect uri` store them into `app_credentials.py`

---
### Functionality

Currently `py_my_spotify.py` connects to the spotify API and extracts:
1. all the user's liked songs
2. all the [audio features](https://developer.spotify.com/documentation/web-api/reference/#category-tracks) of the user's liked songs
3. genres associated to the artis who plays each song

---
### Future implementations
1. Clustering of all liked songs into playlists based on tracks' audio features + artist genres


