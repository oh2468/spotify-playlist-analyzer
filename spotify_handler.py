import requests
import re
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict


class SpotifyHandler:
    _DEBUG_MODE = True
    _FILE_DIR = Path(__file__).parent
    _OUTPUT_DIR = Path(_FILE_DIR, "spotify_responses")
    _API_KEY_FILE = Path(_FILE_DIR, "api_token.txt")
    _API_TOKEN_FILE = Path(_FILE_DIR, "bearer_token.txt")
    _USER_AGENT = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0"}
    _SPOTIFY_AUTH_URL = "https://accounts.spotify.com/api/token"
    _SEARCH_URL = "https://api.spotify.com/v1/search?q={q}&type={type}&limit={limit}" #LIMIT MAX 50 #MARKET
    _AUDIO_FEATURES_URL = "https://api.spotify.com/v1/audio-features?ids={ids}" # LIMIT MAX 50 #NOMARKET
    _PLAYLIST_URL = "https://api.spotify.com/v1/playlists/{id}" #MARKET
    _TRACKS_URL = "https://api.spotify.com/v1/tracks?ids={ids}" #MARKET
    _ALBUM_SINGLE_URL = "https://api.spotify.com/v1/albums/{id}" #MARKET
    _ALBUM_MULTI_URL = "https://api.spotify.com/v1/albums?ids={ids}" #MARKET
    _ALBUM_TRACKS_URL = "https://api.spotify.com/v1/albums/{id}/tracks?limit=50" #MARKET
    _USER_PLAYLIST_URL = "https://api.spotify.com/v1/users/{user_id}/playlists?limit=50" #NOMARKET
    _ARTIST_URL = "https://api.spotify.com/v1/artists/{id}"
    _ARTIST_CONTENT_URL = "https://api.spotify.com/v1/artists/{id}/albums?include_groups={type}&limit=50" #MARKET
    _ARTIST_APPEARS_ON_URL = "https://api.spotify.com/v1/artists/{id}/albums?include_groups=appears_on&limit=50" #MARKET
    _ARTIST_RELATED = "https://api.spotify.com/v1/artists/{id}/related-artists" #NOMARKET
    _ARTIST_TOP_TRACKS = "https://api.spotify.com/v1/artists/{id}/top-tracks" #MARKET (required?)
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

        creation_time = time.time()
        response = requests.request("POST", self._SPOTIFY_AUTH_URL, data={"grant_type": "client_credentials"}, headers={"Authorization": spotify_api_key})

        if response.status_code != 200:
            raise ValueError(" -- UNABLE TO AUTHORIZE THE SPOTIFY CLIENT! DATA CAN NOT BE GATHERED.... -- ")
        
        auth_data = response.json()
        auth_data["created_at"] = creation_time
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


    @staticmethod
    def valid_spoitify_ids(ids):
        return all(re.match(r"^\w{22}$", id) for id in ids)
    

    def valid_search_type(self, type):
        return type in self._VALID_SEARCH_TYPES

    
    def _loop_requests_with_limit(self, base_url, track_ids, max, market=None):
        result = []
        for i in range(0, len(track_ids), max):
            content = self._get_request_to_json_response(base_url.format(ids=",".join(track_ids[i:i + max])), market)
            result += list(content.values())[0]
        return result


    def _get_audio_features(self, track_map):
        track_ids = list(track_map.keys())

        audio_features = self._loop_requests_with_limit(self._AUDIO_FEATURES_URL, track_ids, self._AUDIO_FEATURE_LIMIT)
        self._write_json_content_to_file(audio_features, "audio_features")
        
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
        joined_track_features = [track_map[af["id"]] | {"audio_feature": af} for af in audio_features if af]

        self._write_json_content_to_file(joined_track_features, "analysis_joined")

        return joined_track_features


    def _validate_response(self, response, tries=0):
        if tries >= 3:
            raise RuntimeError(" -- THERE SEEMS TO BE ISSUES WITH THE SPOTIFY REQUESTS. ABORTING! -- ")
        elif response.status_code == 200:
            #print("valid response")
            return response
        elif response.status_code == 401:
            print(response)
            self._renew_token()
            response.request.headers = self._session.headers
            new_response = self._session.send(response.request)
            return self._validate_response(new_response, tries + 1)
        elif response.status_code == 404:
            print("....ERROR....")
            print(response)
            print(response.json())
            # TODO
            # decide how to handle 404 Not Found - The requested resource could not be found. 
            # This error can be due to a temporary or permanent condition.
            # for now return the response
            #return response
            raise ContentNotFoundError(response.json())
        else:
            # handle unknown error here
            print(response)
            return None


    def _recurse_all_page_items(self, data, market=None):
        print("iterating pages")
        if not data["next"]:
            return data["items"]
        else:
            items = data["items"]
            content = self._get_request_to_json_response(data["next"], market)
            return items + self._recurse_all_page_items(content, market)


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


    def _get_request_to_json_response(self, formatted_url, market=None):
        # BUG
        # TODO
        # Handle the following:
        # raise RemoteDisconnected("Remote end closed connection without"
        # http.client.RemoteDisconnected: Remote end closed connection without response
        #
        # raise RemoteDisconnected("Remote end closed connection without"
        # http.client.RemoteDisconnected: Remote end closed connection without response
        #
        # raise ConnectionError(err, request=request)
        # requests.exceptions.ConnectionError: 
        # ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
        if market:
            add_market = f"&market={market}" if "?" in formatted_url else f"?market={market}"
            formatted_url = f"{formatted_url}{add_market}"
        
        print(formatted_url)
        
        response = self._session.get(formatted_url)
        response = self._validate_response(response)
        return response.json()


    def _input_validator(func):
        def validator(*args, **kwargs):
            for arg in args:
                if not arg:
                    raise ValueError("You cannot enter empty values.")
            return func(*args, **kwargs)
        return validator


    def _spotify_id_format_validator(func):
        def validator(*args, **kwargs):
            argz = args[1]
            argz = argz if isinstance(argz, list) else [argz]
            if not __class__.valid_spoitify_ids(argz):
                raise InvalidIdFormatError
            return func(*args, **kwargs)
        return validator


    @_spotify_id_format_validator
    def get_playlist_analytics(self, playlist_id, *, market=None):
        playlist = self._get_request_to_json_response(self._PLAYLIST_URL.format(id=playlist_id), market)

        self._write_json_content_to_file(playlist, "playlist_base")

        spotify_tracks = self._recurse_all_page_items(playlist["tracks"], market)
        track_map = {track["track"]["id"]: track for track in spotify_tracks if not track["is_local"] and track["track"]}
        af_tracks_joined = self._get_audio_features(track_map)
        track_map |= {track["track"]["uri"]: track for track in spotify_tracks if track["is_local"] and track["track"]}

        return AnalysisResult(playlist["name"], playlist["type"], playlist["tracks"]["total"], track_map, af_tracks_joined)


    @_spotify_id_format_validator
    def get_tracks_analytics(self, track_ids, *, market=None):
        spotify_tracks = self._loop_requests_with_limit(self._TRACKS_URL, track_ids, self._TRACK_ID_LIMIT, market)
        
        self._write_json_content_to_file(spotify_tracks, "tracks")
       
        track_map = {track["id"]: {"track": track} for track in spotify_tracks if track}
        af_tracks_joined = self._get_audio_features(track_map)

        return AnalysisResult("", "track", len(track_ids), track_map, af_tracks_joined)


    @_spotify_id_format_validator
    def get_album_analytics(self, album_ids, *, market=None):
        albums = self._get_request_to_json_response(self._ALBUM_MULTI_URL.format(ids=",".join(album_ids)), market)

        self._write_json_content_to_file(albums, "album_multi_base")

        album_map = {album["id"]: album for album in albums["albums"]}
        all_album_tracks = []
        for album in albums["albums"]:
            all_album_tracks += self._recurse_all_page_items(album["tracks"], market)

        self._write_json_content_to_file(all_album_tracks, "multi_album_test_file")

        all_track_ids = [track["id"] for track in all_album_tracks]
        all_track_analytics = self.get_tracks_analytics(all_track_ids, market=market)

        separated_album_tracks = defaultdict(list)
        for joined_track in all_track_analytics.audio_features:
            album_id = joined_track["track"]["album"]["id"]
            separated_album_tracks[album_id].append(joined_track)
        
        separated_albums = []
        for al_id, al_tracks in separated_album_tracks.items():
            track_map = {}
            features = []
            for track_feat in al_tracks:
                track = track_feat["track"]
                track_map[track["id"]] = track
                features.append(track_feat)
            
            album = album_map[al_id]
            separated_albums.append(AnalysisResult(album["name"], album["type"], album["total_tracks"], track_map, features))

        return separated_albums


    @_spotify_id_format_validator
    def get_artist(self, artist_id):
        artist = self._get_request_to_json_response(self._ARTIST_URL.format(id=artist_id))

        self._write_json_content_to_file(artist, "artist_base")

        return artist


    @_spotify_id_format_validator
    def get_artist_content(self, artist_id, type, *, market=None):
        if type not in self._VALID_ARTIST_CONTENT_TYPES:
            raise ValueError(" --  INVALID ARTIST CONTENT TYPE ENTERED.....  -- ")
        
        artist_type = self._get_request_to_json_response(self._ARTIST_CONTENT_URL.format(id=artist_id, type=type), market)
        artist_content = self._recurse_all_page_items(artist_type, market)

        self._write_json_content_to_file(artist_content, f"artist_{type}")

        return artist_content


    @_spotify_id_format_validator
    def get_artist_top_tracks(self, artist_id, *, market=None):
        if not market:
            market = "SE"
        
        artist_top_tracks = self._get_request_to_json_response(self._ARTIST_TOP_TRACKS.format(id=artist_id), market)
        
        self._write_json_content_to_file(artist_top_tracks, "artist_top_tracks")

        return artist_top_tracks["tracks"]
    

    @_spotify_id_format_validator
    def get_artist_appears_on(self, artist_id, *, market=None):
        artist_appears_on = self._get_request_to_json_response(self._ARTIST_APPEARS_ON_URL.format(id=artist_id), market)

        self._write_json_content_to_file(artist_appears_on, "artist_appears_on")

        return (artist_appears_on["items"], artist_appears_on["total"])


    @_spotify_id_format_validator
    def get_artist_related(self, artist_id):
        related_artists = self._get_request_to_json_response(self._ARTIST_RELATED.format(id=artist_id))

        self._write_json_content_to_file(related_artists, "artist_related")

        return related_artists["artists"]


    @_input_validator
    def get_user_playlists(self, username, *, market=None):
        playlists = self._get_request_to_json_response(self._USER_PLAYLIST_URL.format(user_id=username), market)
        self._write_json_content_to_file(playlists, "user_base")
        return (playlists["items"], playlists["total"])


    @_input_validator
    def get_search(self, type, search, *, market=None):
        if not type in self._VALID_SEARCH_TYPES:
            raise ValueError("Invalid search type.")

        req_url = self._SEARCH_URL.format(q=search, type=type, limit=self._SEARCH_LIMIT)
        results = self._get_request_to_json_response(req_url, market)

        self._write_json_content_to_file(results, f"search_{type}")

        result_key = f"{type}s"
        return (results[result_key]["items"], results[result_key]["total"])


class InvalidIdFormatError(Exception): pass

class ContentNotFoundError(Exception): pass

@dataclass
class AnalysisResult:
    name: str
    type: str
    total: int
    track_map: dict
    audio_features: list
    missing_tracks: list = field(init=False)

    def __post_init__(self):
        if len(self.audio_features) == self.total:
            self.missing_tracks = []
        else:
            missing_track_ids = set(self.track_map.keys()) - {track["track"]["id"] for track in self.audio_features}
            self.missing_tracks = [self.track_map[id] for id in missing_track_ids]

        # self._write_json_content_to_file(self.missing_tracks, "analysis_missing")
        with open("spotify_responses/analysis_missing.json", "w", encoding="UTF-8") as file:
            json.dump(self.missing_tracks, file)

