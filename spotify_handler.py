from os import environ
import requests
import re
import json
import time
from pathlib import Path


class SpotifyHandler:
    _DEBUG_MODE = True
    _FILE_DIR = Path(__file__).parent
    _OUTPUT_DIR = Path(_FILE_DIR, "spotify_responses")
    _API_KEY_FILE = Path(_FILE_DIR, "api_token.txt")
    _API_TOKEN_FILE = Path(_FILE_DIR, "bearer_token.txt")
    _USER_AGENT = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0"}
    _SPOTIFY_AUTH_URL = "https://accounts.spotify.com/api/token"
    _SEARCH_URL = "https://api.spotify.com/v1/search" #LIMIT MAX 50 #MARKET
    _AUDIO_FEATURES_URL = "https://api.spotify.com/v1/audio-features?ids={ids}" # LIMIT MAX 50 #NOMARKET
    _PLAYLIST_URL = "https://api.spotify.com/v1/playlists/{id}" #MARKET
    _TRACKS_URL = "https://api.spotify.com/v1/tracks?ids={ids}" #MARKET
    _ALBUM_SINGLE_URL = "https://api.spotify.com/v1/albums/{id}" #MARKET
    _ALBUM_MULTI_URL = "https://api.spotify.com/v1/albums?ids={ids}" #MARKET
    _ALBUM_TRACKS_URL = "https://api.spotify.com/v1/albums/{id}/tracks?limit=50" #MARKET
    _USER_PLAYLIST_URL = "https://api.spotify.com/v1/users/{user_id}/playlists?limit=50" #NOMARKET
    _ARTIST_CONTENT_URL = "https://api.spotify.com/v1/artists/{id}/albums?include_groups={type}&limit=50" #MARKET
    _ARTIST_APPEARS_ON_URL = "https://api.spotify.com/v1/artists/{id}/albums?include_groups=appears_on" #MARKET
    _ARTIST_RELATED = "https://api.spotify.com/v1/artists/{id}/related-artists" #NOMARKET
    _ARTIST_TOP_TRACKS = "https://api.spotify.com/v1/artists/{id}/top-tracks?market={market}" #MARKET (required?)
    _SPOTIFY_MARKETS_URL = "https://api.spotify.com/v1/markets"
    _AUDIO_FEATURE_LIMIT = 50
    _TRACK_ID_LIMIT = 50
    _SEARCH_LIMIT = 50
    _VALID_SEARCH_TYPES = ["playlist", "artist", "album"]
    _VALID_ARTIST_CONTENT_TYPES = ["album", "single", "compilation", "appears_on"]


    def __init__(self):
        self._session = requests.Session()
        self._bearer = ""
        self._markets = []
        self._renew_token()
        self._init_session()


    @property
    def markets(self):
        return self._markets


    def _valid_token(self):
        print("validating token")
        try:
            with open(self._API_TOKEN_FILE, "r", encoding="UTF-8") as file:
                auth_data = json.load(file)
                if time.time() < auth_data["invalid_after"]:
                    self._bearer = auth_data["access_token"]
                    return True
                else:
                    return False
        except Exception as ex:
            return False


    def _renew_token(self):
        if self._valid_token(): return

        print("renewing token")
        try:
            with open(self._API_KEY_FILE, "r", encoding="UTF-8") as file:
                spotify_api_key = file.read()
        except FileNotFoundError as ex:
            print(" -- THE API KEY FILE DOESN'T EXISTS!!! ADD THE API KEY TO IT BEFORE TRYIG AGAIN -- ")
            raise ex

        response = requests.request("POST", self._SPOTIFY_AUTH_URL, data={"grant_type": "client_credentials"}, headers={"Authorization": spotify_api_key})

        if response.status_code != 200:
            raise ValueError(" -- UNABLE TO AUTHORIZE THE SPOTIFY CLIENT! DATA CAN NOT BE GATHERED.... -- ")
        
        auth_data = response.json()
        auth_data["created_at"] = time.time()
        auth_data["invalid_after"] = auth_data["created_at"] + auth_data["expires_in"]

        self._bearer = auth_data["access_token"]
        self._init_session()

        with open(self._API_TOKEN_FILE, "w", encoding="UTF-8") as file:
            json.dump(auth_data, file)
        
        print("token renewed")


    def _init_session(self):
        header = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._bearer}",
        }
        self._session.headers.update(header)
        self._markets = self._session.get(self._SPOTIFY_MARKETS_URL).json()["markets"]


    def valid_spotify_urls(self, type, urls):
        #valid = all(re.match(r"https://open.spotify.com/(playlist|track|album|artist)/\w{22}$", url) for url in urls)
        pattern = r"https://open.spotify.com/{type}/\w{{22}}$".format(type=type)
        valid = all(re.match(pattern, url) for url in urls)
        return [url.split("/")[-1] for url in urls] if valid else None


    def valid_spoitify_ids(self, ids):
        return all(re.match(r"^\w{22}$", id) for id in ids)
    

    def valid_search_type(self, type):
        return type in self._VALID_SEARCH_TYPES

    
    def _valid_spotify_ids(self, ids):
        if not all(re.match(r"^\w{22}$", id) is not None for id in ids):
            raise ValueError("Invalid spotify id(s) entered")

    
    def _loop_requests_with_limit(self, base_url, track_ids, max):
        result = []
        for i in range(0, len(track_ids), max):
            response = self._session.get(base_url.format(ids=",".join(track_ids[i:i + max])))
            response = self._validate_response(response)
            result += list(response.json().values())[0]
        return result


    def _get_audio_features(self, track_ids):
        audio_features = self._loop_requests_with_limit(self._AUDIO_FEATURES_URL, track_ids, self._AUDIO_FEATURE_LIMIT)
        self._write_json_content_to_file(audio_features, "audio_features")
        # with open("spotify_responses/audio_features.json", "w", encoding="UTF-8") as file:
        #     json.dump(audio_features, file)
        
        return audio_features


    def _analyze_tracks(self, tracks):
        pass


    def _validate_response(self, response, tries=0):
        if tries >= 3:
            raise RuntimeError(" -- THERE SEEMS TO BE ISSUES WITH THE SPOTIFY REQUESTS. ABORTING! -- ")
        elif response.status_code == 200:
            print("valid response")
            return response
        elif response.status_code == 401:
            print(response)
            self._renew_token()
            new_response = self._session.send(response.request)
            return self._validate_response(new_response, tries + 1)
        elif response.status_code == 404:
            pass
        else:
            # handle unknown error here
            print(response)
            return None


    def _recurse_all_page_items(self, data):
        print("iterating pages")
        if not data["next"]:
            return data["items"]
        else:
            items = data["items"]
            response = self._session.get(data["next"])
            response = self._validate_response(response)
            return items + self._recurse_all_page_items(response.json())


    def _write_json_content_to_file(self, content, filename):
        if not self._DEBUG_MODE: return False

        if not self._OUTPUT_DIR.exists():
            self._OUTPUT_DIR.mkdir()
        
        if not self._OUTPUT_DIR.is_dir():
            print("The output location name is already taken by another file....")
            print(f"The needed name of the directory is: {self._OUTPUT_DIR.stem}")
            return False
        
        with open(self._OUTPUT_DIR.joinpath(f"{filename}.json"), "w", encoding="UTF-8") as file:
            json.dump(content, file)

        return True


    def get_playlist_analytics(self, playlist_id):
        self._valid_spotify_ids([playlist_id])
        response = self._session.get(self._PLAYLIST_URL.format(id=playlist_id))
        response = self._validate_response(response)
        playlist = response.json()

        #with open("spotify_responses/what.json", "w", encoding="UTF-8") as file: json.dump(playlist, file)
        self._write_json_content_to_file(playlist, "playlist_base")

        spotify_tracks = self._recurse_all_page_items(playlist["tracks"])
        tracks_dict = {track["track"]["id"]: track for track in spotify_tracks}
        tracks_audio_features = self._get_audio_features(list(tracks_dict.keys()))
        
        # with open("spotify_responses/audio_features.json", "w", encoding="UTF-8") as file:
        #     json.dump(tracks_audio_features, file)

        track_features_joined = [tracks_dict[af["id"]] | {"audio_feature": af} for af in tracks_audio_features]

        #with open("spotify_responses/analysis.json", "w", encoding="UTF-8") as file: json.dump(track_features_joined, file)
        self._write_json_content_to_file(track_features_joined, "analysis")

        return (playlist["name"], track_features_joined, playlist["type"])


    def get_tracks_analytics(self, track_ids):
        self._valid_spotify_ids(track_ids)
        spotify_tracks = self._loop_requests_with_limit(self._TRACKS_URL, track_ids, self._TRACK_ID_LIMIT)
        
        #with open("spotify_responses/tracks.json", "w", encoding="UTF-8") as file: json.dump(spotify_tracks, file)
        self._write_json_content_to_file(spotify_tracks, "tracks")

        tracks_dict = {track["id"]: {"track": track} for track in spotify_tracks}
        tracks_audio_features = self._get_audio_features(list(tracks_dict.keys()))
        
        #with open("spotify_responses/track_features.json", "w", encoding="UTF-8") as file: json.dump(tracks_audio_features, file)
        self._write_json_content_to_file(tracks_audio_features, "track_features")

        # BUG
        # some track ids return null, i.e. the list comp fails on af["id"] when af is None
        # the issue seems to be on spotify's end when a song seems to have multiple ids
        # and the analysis is done on the original id and not on an id from another compilation/playlist
        # trying to figure out if the original id/analysis can somehow be found
        # some track ids, e.g. 1nDYJBvNOt5afmquv7y7Ii, audio features return the following:
        # {
        #   "error": {
        #     "status": 404,
        #     "message": "analysis not found"
        #   }
        # }
        # a decision needs to be made on how to handle those situations
        # looks to be this closed issue: https://github.com/spotify/web-api/issues/1570
        track_features_joined = [tracks_dict[af["id"]] | {"audio_feature": af} for af in tracks_audio_features]

        #with open("spotify_responses/analysis.json", "w", encoding="UTF-8") as file: json.dump(track_features_joined, file)
        self._write_json_content_to_file(track_features_joined, "analysis")

        return track_features_joined


    def get_album_analytics(self, album_id):
        response = self._session.get(self._ALBUM_SINGLE_URL.format(id=album_id))
        response = self._validate_response(response)
        album = response.json()

        # with open("spotify_responses/album_single.json", "w", encoding="UTF-8") as file:
        #     json.dump(album, file)
        self._write_json_content_to_file(album, "album_single")

        response = self._session.get(self._ALBUM_TRACKS_URL.format(id=album_id))
        response = self._validate_response(response)
        album_tracks = self._recurse_all_page_items(response.json())

        # with open("spotify_responses/album_tracks.json", "w", encoding="UTF-8") as file:
        #     json.dump(album_tracks, file)
        self._write_json_content_to_file(album_tracks, "album_tracks")

        track_ids = [track["id"] for track in album_tracks]
        return (album["name"], self.get_tracks_analytics(track_ids), album["type"])


    def get_artist_content(self, artist_id, type):
        if type not in self._VALID_ARTIST_CONTENT_TYPES:
            raise ValueError(" --  INVALID ARTIST CONTENT TYPE ENTERED.....  -- ")
        
        response = self._session.get(self._ARTIST_CONTENT_URL.format(id=artist_id, type=type))
        response = self._validate_response(response)
        artist_start = response.json()
        artist_all = self._recurse_all_page_items(artist_start)

        #with open("spotify_responses/artist.json", "w", encoding="UTF-8") as file: json.dump(artist_all, file)
        self._write_json_content_to_file(artist_all, "artist")

        return artist_all


    def get_artist_top_tracks(self, artist_id, market="SE"):
        response = self._session.get(self._ARTIST_TOP_TRACKS.format(id=artist_id, market=market))
        response = self._validate_response(response)
        artist_top_tracks = response.json()
        
        #with open("spotify_responses/artist_top_tracks.json", "w", encoding="UTF-8") as file: json.dump(artist_top_tracks, file)
        self._write_json_content_to_file(artist_top_tracks, "artist_top_tracks")

        return artist_top_tracks["tracks"]
    

    def get_artist_appears_on(self, artist_id):
        response = self._session.get(self._ARTIST_APPEARS_ON_URL.format(id=artist_id))
        response = self._validate_response(response)
        artist_appears_on = response.json()

        #with open("spotify_responses/appears_on.json", "w", encoding="UTF-8") as file: json.dump(artist_appears_on, file)
        self._write_json_content_to_file(artist_appears_on, "appears_on")

        return (artist_appears_on["items"], artist_appears_on["total"])


    def get_user_playlists(self, username):
        if not username:
            raise ValueError("You must enter a username! It cannot be empty...")

        self._renew_token()
        response = self._session.get(self._USER_PLAYLIST_URL.format(user_id=username))
        print(response.status_code)

        content = response.json()
        #with open("spotify_responses/user.json", "w", encoding="UTF-8") as file: json.dump(content, file)
        self._write_json_content_to_file(content, "user")

        if response.status_code == 200:
            playlists = response.json()
            return (playlists["items"], playlists["total"])
        elif response.status_code == 404:
            return None
        else:
            raise RuntimeError(f"Unexpected behaviour, error getting user content..., search: {username}")



    def get_search(self, type, search):
        response = self._session.get(
            self._SEARCH_URL,
            params={"q": search, "type": type, "limit": self._SEARCH_LIMIT}
        )

        response = self._validate_response(response)
        results = response.json()

        # with open("spotify_responses/search.json", "w", encoding="UTF-8") as file:
        #     json.dump(results, file)
        self._write_json_content_to_file(results, "search")

        result_key = f"{type}s"
        return (results[result_key]["items"], results[result_key]["total"])






"""
"""

        # audio_features = []
        # max = self._AUDIO_FEATURE_LIMIT
        # for i in range(0, len(track_ids), max):
        #     response = self._session.get(self._AUDIO_FEATURES_URL.format(ids=",".join(track_ids[i:i + max])))
        #     response = self._validate_response(response)
        #     audio_features += response.json()["audio_features"]


        
        # first_playlist = playlists["playlists"]["items"][0]
        # tracks_url = first_playlist["tracks"]["href"]

        # response = self._session.get(tracks_url)
        # response = self._validate_response(response)

        # tracks = response.json()

        # with open("spotify_responses/playlist.json", "w", encoding="UTF-8") as file:
        #     json.dump(tracks, file)
        

        # track_ids = [track["track"]["id"] for track in tracks["items"]]

        # audio_features = self._get_audio_features(track_ids)

        #return (playlists["playlists"]["items"], playlists["playlists"]["total"])

