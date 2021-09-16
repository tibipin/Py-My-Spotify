import pandas
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ast import literal_eval
from datetime import date
from app_credentials import client_id, client_secret, my_spotify_username, redirect_uri

hard_limit = 50


def login_to_spotify_api(app_client_id, app_client_secret, spotify_username: str, redirect_uri):
    """
    Login to spotify API
    :param app_client_id: spotify API app client id
    :param app_client_secret: spotify API app client secret
    :param spotify_username: spotify user name
    :return: spotify API connection
    """
    scopes = ['user-library-read', 'user-library-modify', 'playlist-modify-private', 'playlist-read-private']

    login_details = SpotifyOAuth(client_id=app_client_id,
                                 client_secret=app_client_secret,
                                 username=spotify_username, scope=' '.join(scopes),
                                 redirect_uri=redirect_uri)

    magic_token = login_details.get_access_token()['access_token']

    s = spotipy.Spotify(auth=magic_token, auth_manager=login_details)
    return s


# ===> Step 1: Instantiate a connection to Spotify API

conn = login_to_spotify_api(app_client_id=client_id, app_client_secret=client_secret,
                            spotify_username=my_spotify_username, redirect_uri=redirect_uri)


def extract_my_liked_songs(api_connection, limit: int):
    """
    ===============================
    Extract data from the API:
    --------------------------
    1. Date added to liked songs
    2. Track IDs
    3. Track Names
    4. Artists names
    5. Artists IDs
    6. Artists genres
    ===============================
    :param limit: integer, limit of songs to be accessed as allowed by the api, normally 50
    :param api_connection: the api connection resulted from the login_to_spotify_api function
    :return: pandas dataframe with all saved tracks
    """

    total_number_of_saved_tracks = api_connection.current_user_saved_tracks()['total']
    api_extraction_steps = total_number_of_saved_tracks // limit + 1
    time_added_in_liked_songs = []
    track_ids_master = []
    track_names_master = []
    artists_master = []
    artist_ids_master = []
    artist_genres_master = []

    for i in range(api_extraction_steps):
        if i == 0:
            offset_val = 0
        else:
            offset_val = i * hard_limit
        for j in api_connection.current_user_saved_tracks(limit=hard_limit, offset=offset_val)['items']:
            added_time = j['added_at']
            time_added_in_liked_songs.append(added_time)

            track_id = j['track']['id']
            track_ids_master.append(track_id)

            track_name = j['track']['name']
            track_names_master.append(track_name)

            artists = [x['name'] for x in j['track']['artists']]
            artists_master.append(artists)

            artist_ids = [x['id'] for x in j['track']['artists']]
            artist_ids_master.append(artist_ids)

            artist_genres = [api_connection.artist(x)['genres'] for x in artist_ids]
            artist_genres_master.append(artist_genres)

    liked_songs_df = pandas.DataFrame({'time_added': time_added_in_liked_songs,
                                       'track_id': track_ids_master,
                                       'track_name': track_names_master,
                                       'artists': artists_master,
                                       'artists_ids': artist_ids_master,
                                       'artists_genres': artist_genres_master})

    def get_all_genres(list_of_lists):
        """
        Helper function to merge all genres
        from a list of lists
        to a single list

         [[],[],...]

        :param list_of_lists: [[1,2],[3,4],...]
        :return: [1,2,3,4...]
        """
        genres = []
        list_of_lists = literal_eval(str(list_of_lists))
        for element in list_of_lists:
            for sub_element in element:
                genres.append(sub_element)
        return genres

    liked_songs_df['artists_genres'] = liked_songs_df['artists_genres'].apply(lambda x: get_all_genres(x))

    return liked_songs_df


# ===> Step 2: Extract a list of My Liked Songs

my_liked_songs_df = extract_my_liked_songs(api_connection=conn, limit=hard_limit)


def extract_audio_features(df: pandas.DataFrame, api_connection, limit: int):
    master_audio_feats = pandas.DataFrame()
    total_number_of_track_ids = len(df.track_id.values.tolist())
    api_extraction_steps = total_number_of_track_ids // limit + 1
    for i in range(api_extraction_steps):
        if i == 0:
            track_ids = my_liked_songs_df.iloc[i:50]['track_id'].values.tolist()
        else:
            track_ids = my_liked_songs_df.iloc[i * 50:(i + 1) * 50]['track_id'].values.tolist()
        audio_feats = pandas.DataFrame(api_connection.audio_features(track_ids))
        master_audio_feats = master_audio_feats.append(audio_feats)
    final_df = df.merge(master_audio_feats, left_on='track_id', right_on='id')
    return final_df


# ===> Step 3: Extract the audio features for all my liked songs

my_liked_songs_df = extract_audio_features(my_liked_songs_df, api_connection=conn, limit=hard_limit)

# ===> Export liked songs + audio features to pickle for later use

my_liked_songs_df.to_pickle(f'liked_songs_{date.today().strftime("%Y-%m-%d")}.pkl')


# ===> Step 4: Extract genres

def extract_genre_overview(df: pandas.DataFrame):
    """

    :param df: DataFrame which needs to contain the columns ['track_id', 'artists_genres']
    :return: tuple(
    """
    genre_mapping = df['artists_genres'].str.join(',').str.get_dummies(',')
    df = df[['track_id', 'track_name', 'artists']]
    track_genre_relationship = df.merge(genre_mapping, left_index=True, right_index=True)
    pivotted_genre_mapping = {}
    for i in genre_mapping.to_dict('list'):
        pivotted_genre_mapping.update({i: sum(pivotted_genre_mapping[i])})
    pivotted_genre_mapping = pandas.DataFrame.from_dict(pivotted_genre_mapping, orient='index')
    pivotted_genre_mapping = pivotted_genre_mapping.sort_values(by=0, ascending=False)
    return pivotted_genre_mapping, df


pivotted_genre_mapping = extract_genre_overview(my_liked_songs_df)[0]
