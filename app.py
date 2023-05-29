from flask import Flask, render_template, request, redirect, url_for, abort, flash, session
from spotify_handler import SpotifyHandler, ContentNotFoundError, InvalidIdFormatError
from datetime import timedelta
from functools import wraps
import playlist_analyzer
import country_codes
import json


app = Flask(__name__)
app.secret_key = "RANDOMSECRETKEY1"
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 # max file size = 2MB
sp_handler = None
sp_handler = SpotifyHandler()


@app.template_filter("format_time")
def format_time(t):
    # return str(timedelta(milliseconds=t)).split(".")[0]
    return playlist_analyzer.time_formatter(t)


@app.template_filter("format_artists")
def format_artists(artists):
    return ", ".join(artist["name"] for artist in artists)


def _do_analysis(tracks, name, type):
    charts = playlist_analyzer.test_chart_making(tracks)
    return render_template("analysis.html", data={"tracks": tracks, "charts": charts, "name": name, "type": type})


def _analyze_tracks(track_urls, track_display_title="< individual track urls >"):
    if not (track_ids := sp_handler.valid_spotify_urls("track", track_urls)):
        return _return_flash_error(["Invalid spotify track url(s) entered in the text."])
    
    audio_features = sp_handler.get_tracks_analytics(track_ids, market=_get_market_from_cookie())
    return _do_analysis(audio_features, track_display_title, "track")


def _return_flash_error(error_msgs):
    for msg in error_msgs:
        flash(msg)
    return redirect(url_for("index"))


def _get_market_from_cookie():
    user_market = request.cookies.get("market", None)
    return user_market if user_market in country_codes.code_to_name else None


def _error_handler(func):
    @wraps(func)
    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InvalidIdFormatError as err:
            print(err)
            return _return_flash_error(["Invalid format of the entered spotify ID."])
        except ContentNotFoundError as err:
            msg = str(err)
            try:
                msg = err.args[0]["error"]["message"]
            except (IndexError, KeyError) as err:
                # the exception failed to include the message, should not happen
                pass
            return _return_flash_error([msg])
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
        top_results, total = sp_handler.get_search(search_type, search_query, market=_get_market_from_cookie())
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
    filename = playlist_file.filename
    file_content = playlist_file.read()

    if not file_content:
        return _return_flash_error(["The uploaded file is empty."])
    
    playlist_tracks = [line.strip() for line in file_content.decode().splitlines()]
    return _analyze_tracks(playlist_tracks, filename)


@app.post("/playlist_text")
def analyze_text():
    track_urls = [track.strip() for track in request.form.get("tracks_text", "").splitlines()]
    
    if not track_urls:
        return _return_flash_error(["No spotify track url(s) entered in the text field."])
    
    return _analyze_tracks(track_urls)


@app.get("/playlist/<playlist_id>")
@_error_handler
def playlist_analysis(playlist_id):
    playlist_name, playlist_tracks, type = sp_handler.get_playlist_analytics(playlist_id, market=_get_market_from_cookie())
    return _do_analysis(playlist_tracks, playlist_name, type)
    

@app.get("/album/<album_id>")
@_error_handler
def album_analysis(album_id):
    album_name, track_data, type = sp_handler.get_album_analytics(album_id, market=_get_market_from_cookie())
    return _do_analysis(track_data, album_name, type)


@app.get("/artist/<artist_id>")
@_error_handler
def artist_lookup(artist_id):
    market = _get_market_from_cookie()
    data = {}
    data["top_tracks"] = sp_handler.get_artist_top_tracks(artist_id, market=market)
    data["albums"] = sp_handler.get_artist_content(artist_id, "album", market=market)
    data["singles"] = sp_handler.get_artist_content(artist_id, "single", market=market)
    data["compilations"] = sp_handler.get_artist_content(artist_id, "compilation", market=market)
    appears_on, appears_total = sp_handler.get_artist_appears_on(artist_id, market=market)
    data["appears_on"] = appears_on
    data["appears_on_total"] = appears_total
    data["related_artists"] = sp_handler.get_artist_related(artist_id)
    return render_template("artist.html", data=data)


@app.get("/track/<track_id>")
@_error_handler
def single_track_analysis(track_id):
    audio_features = sp_handler.get_tracks_analytics([track_id], market=_get_market_from_cookie())
    return _do_analysis(audio_features, "< single track >", "track")


@app.get("/user/<username>")
def user_playlists(username):
    data = {"username": username, "user_found": False}
    try:
        playlists = sp_handler.get_user_playlists(username, market=_get_market_from_cookie())
        data["user_found"] = True
        data["playlists"] = playlists[0]
        data["total"] = playlists[1]
    except ValueError as err:
        # empty username 
        return _return_flash_error([str(err)])
    except ContentNotFoundError as err:
        # no user found with the entered name
        print(err)
        pass
    
    return render_template("user.html", data=data), 404


@app.get("/markets")
def get_markets():
    if sp_handler is None: return ""
    spotify_markets = sp_handler.markets
    mapped_markets = [{"code": code, "name": country_codes.code_to_name.get(code, code)} for code in spotify_markets]
    return mapped_markets


@app.get("/test")
def testing_charts():
    with open("spotify_responses/analysis.json", "r", encoding="UTF-8") as file:
            data = json.load(file)
    charts = playlist_analyzer.test_chart_making(data)
    return render_template("analysis.html", data={"tracks": data, "charts": charts, "name": "TESTING CHARTS", "type": "WHAT TYPE"})


@app.errorhandler(404)
def error_404(error):
    return render_template("error.html"), 404


@app.errorhandler(405)
def error_405(error):
    return render_template("error.html"), 405



if __name__ == "__main__":
    #app.run(debug=True)
    app.run()
