from flask import Flask, render_template, request, redirect, url_for, abort, flash, session
from spotify_handler import SpotifyHandler, ContentNotFoundError, InvalidIdFormatError
from datetime import timedelta
import country_codes


app = Flask(__name__)
app.secret_key = "RANDOMSECRETKEY1"
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 # max file size = 2MB
sp_handler = SpotifyHandler()
#sp_handler = None


@app.template_filter("format_time")
def format_time(t):
    return str(timedelta(milliseconds=t)).split(".")[0]


@app.template_filter("format_artists")
def format_artists(artists):
    return ", ".join(artist["name"] for artist in artists)


def _do_analysis(tracks, name, type):
    # do picture analyzis
    return render_template("analysis.html", data={"tracks": tracks, "name": name, "type": type})


def _analyze_playlist(playlist_id):
    print(playlist_id)
    try:
        playlist_name, playlist_tracks, type = sp_handler.get_playlist_analytics(playlist_id)
    except ValueError as err:
        abort(404)
    return _do_analysis(playlist_tracks, playlist_name, type)


def _analyze_tracks(track_urls):
    if not (track_ids := sp_handler.valid_spotify_urls("track", track_urls)):
        return _return_flash_error(["Invalid spotify track url(s) entered in the text."])
    
    audio_features = sp_handler.get_tracks_analytics(track_ids)
    return _do_analysis(audio_features, "< individual track urls >", "track")


def _return_flash_error(error_msgs):
    for msg in error_msgs:
        flash(msg)
    return redirect(url_for("index"))


def _get_market_from_cookie():
    return request.cookies.get("market", None)


def _error_handler(func):
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InvalidIdFormatError as err:
            pass
        except ContentNotFoundError as err:
            pass
    return handler


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/search")
def search():
    try:
        search_type, search_query = list(request.args.items())[0]
    except IndexError:
        return _return_flash_error(["You seem to be searching incorrectly."])

    try:
        top_results, total = sp_handler.get_search(search_type, search_query)
    except ValueError as err:
        return _return_flash_error([str(err)])

    data = {"results": top_results, "search_query": search_query, "total": total, "search_type": search_type}
    return render_template("search.html", data=data)


@app.post("/playlist_url")
def analyze_url():
    url = request.form.get("playlist_url", "").strip()
    type = request.form.get("type", "")

    if not (content_id := sp_handler.valid_spotify_urls(type, [url])):
        return _return_flash_error([f"Invalid spotify {type} url format entered."])

    if type == "album":
        return redirect(url_for("album_analysis", album_id=content_id[0]))
    
    return redirect(url_for("playlist_analysis", playlist_id=content_id[0]))
    

@app.post("/playlist_file")
def analyze_file():
    playlist_file = request.files["tracks_file"]
    file_content = playlist_file.read()

    if not file_content:
        return _return_flash_error(["The uploaded file is empty."])
    
    playlist_tracks = [line.strip() for line in file_content.decode().splitlines()]
    return _analyze_tracks(playlist_tracks)


@app.post("/playlist_text")
def analyze_text():
    track_urls = [track.strip() for track in request.form.get("tracks_text", "").splitlines()]
    
    if not track_urls:
        return _return_flash_error(["No spotify track url(s) entered in the text field."])
    
    return _analyze_tracks(track_urls)


@app.get("/playlist/<playlist_id>")
def playlist_analysis(playlist_id):
    return _analyze_playlist(playlist_id)


@app.get("/album/<album_id>")
def album_analysis(album_id):
    if not sp_handler.valid_spoitify_ids([album_id]):
        return _return_flash_error(["The entered album ID format is INVALID... Try again with a correct one!"])
    
    album_name, track_data, type = sp_handler.get_album_analytics(album_id)
    return _do_analysis(track_data, album_name, type)


@app.get("/artist/<artist_id>")
def artist_lookup(artist_id):
    if not sp_handler.valid_spoitify_ids([artist_id]):
        return _return_flash_error(["The entered artist ID format is INVALID..."])
        
    data = {}
    data["top_tracks"] = sp_handler.get_artist_top_tracks(artist_id)
    data["albums"] = sp_handler.get_artist_content(artist_id, "album")
    data["singles"] = sp_handler.get_artist_content(artist_id, "single")
    data["compilations"] = sp_handler.get_artist_content(artist_id, "compilation")
    appears_on, appears_total = sp_handler.get_artist_appears_on(artist_id)
    data["appears_on"] = appears_on
    data["appears_on_total"] = appears_total
    data["related_artists"] = sp_handler.get_artist_related(artist_id)
    return render_template("artist.html", data=data)


@app.get("/track/<track_id>")
def single_track_analysis(track_id):
    audio_features = sp_handler.get_tracks_analytics([track_id])
    return _do_analysis(audio_features, "< single track >", "track")


@app.get("/user/<username>")
def user_playlists(username):
    data = {"username": username, "user_found": False}
    try:
        playlists = sp_handler.get_user_playlists(username)
        data["user_found"] = True
        data["playlists"] = playlists[0]
        data["total"] = playlists[1]
    except ValueError as err:
        # empty username 
        pass
    
    return render_template("user.html", data=data)


@app.get("/markets")
def get_markets():
    spotify_markets = sp_handler.markets
    mapped_markets = [{"code": code, "name": country_codes.code_to_name.get(code, code)} for code in spotify_markets]
    return mapped_markets



@app.errorhandler(404)
def error_404(error):
    return render_template("error.html"), 404


@app.errorhandler(405)
def error_405(error):
    return render_template("error.html"), 405



if __name__ == "__main__":
    #app.run(debug=True)
    app.run()
