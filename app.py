from flask import Flask, render_template, request, redirect, url_for, abort, flash, session
from spotify_handler import SpotifyHandler, ContentNotFoundError, InvalidIdFormatError
from functools import wraps
from jinja2.exceptions import TemplateNotFound
import playlist_analyzer
import country_codes
import pickle


DEBUG_MODE = True

app = Flask(__name__)
app.secret_key = "RANDOMSECRETKEY1"
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 # max file size = 2MB
sp_handler = None
sp_handler = SpotifyHandler(DEBUG_MODE)


@app.template_filter("format_time")
def format_time(t):
    return playlist_analyzer.time_formatter(t)


@app.template_filter("format_artists")
def format_artists(artists):
    return ", ".join(artist["name"] for artist in artists)


@app.context_processor
def inject_base_data():
    if sp_handler is None: return {}

    spotify_markets = sp_handler.markets
    mapped_markets = [{"code": code, "name": country_codes.code_to_name.get(code, code)} for code in spotify_markets]

    limits = {
        "playlist": sp_handler.MAX_MULTI_PLAYLIST,
        "album": sp_handler.MAX_MULTI_ALBUM,
        "track": sp_handler.MAX_MULTI_TRACK,
    }

    base = {"markets": mapped_markets, "limits": limits}
    return {"base": base}


def _do_analysis(analysis_data):
    _dump_data_for_testing(analysis_data)
    all_data = []
    for analysis in analysis_data:
        data = {}
        data["tracks"] = analysis.audio_features
        data["name"] = analysis.name
        data["type"] = analysis.type
        data["total"] = analysis.total
        data["missing"] = analysis.missing_tracks
        data["descriptions"] = playlist_analyzer.data_descriptions
        data["charts"] = playlist_analyzer.get_data_charts(data["tracks"], DEBUG_MODE)
        all_data.append(data)
    return render_template("analysis.html", all_data=all_data)


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
            except (IndexError, KeyError, TypeError) as err:
                # the exception failed to include the message, should not happen
                # now happens when multi albums throws error for all invalid ids
                pass
            return _return_flash_error([msg])
        except ValueError as err:
            return _return_flash_error([str(err)])
    return handler


@_error_handler
def _analyze_tracks(track_urls, track_display_title="< individual track urls >"):
    if not (track_ids := sp_handler.valid_spotify_urls("track", track_urls)):
        return _return_flash_error(["Invalid spotify track url(s) entered in the text."])
    
    analysis_data = sp_handler.get_tracks_analytics(track_ids, market=_get_market_from_cookie())
    analysis_data.name = track_display_title
    return _do_analysis([analysis_data])


def _return_flash_error(error_msgs):
    for msg in error_msgs:
        flash(msg)
    return redirect(url_for("index"))


def _get_market_from_cookie():
    user_market = request.cookies.get("market", None)
    return user_market if user_market in country_codes.code_to_name else None


def _dump_data_for_testing(data):
    if DEBUG_MODE:
        with open("spotify_responses/pickled_data", "wb") as file:
            pickle.dump(data, file)


def _get_data_for_testing():
    with open("spotify_responses/pickled_data", "rb") as file:
        return pickle.load(file)


def _clean_spotify_urls(content):
    return [url.strip().split("?")[0] for url in content.splitlines() if url]


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
        top_results, total, next = sp_handler.get_search(search_type, search_query, market=_get_market_from_cookie())
    except ValueError as err:
        return _return_flash_error([str(err)])
    except ContentNotFoundError as err:
        return _return_flash_error(["There seems to be issues with spotify searching at the moment!", "Try again in a while and hopefully spotify is working correctly again."])

    data = {"results": top_results, "search_query": search_query, "total": total, "search_type": search_type, "next": next}
    return render_template("search.html", data=data)


@app.post("/playlist-urls")
def analyze_urls():
    urls = _clean_spotify_urls(request.form.get("spotify-urls", ""))
    print(urls)

    try:
        url_type = urls[0].split("/")[3]
    except:
        url_type = None # failed to extract url type
    
    print(url_type)

    if url_type == "track":
        return _analyze_tracks(urls)

    spotify_ids = sp_handler.valid_spotify_urls(url_type, urls)

    if not spotify_ids or not url_type:
        return _return_flash_error(["Invalid spotify url format entered", "Make sure to only enter a single type or content link"])

    return redirect(f"/{url_type}/{','.join(spotify_ids)}")


@app.post("/playlist-file")
def analyze_file():
    playlist_file = request.files["tracks_file"]
    filename = playlist_file.filename
    file_content = playlist_file.read()

    if not file_content:
        return _return_flash_error(["The uploaded file is empty."])
    
    playlist_tracks = _clean_spotify_urls(file_content.decode())
    return _analyze_tracks(playlist_tracks, filename)


@app.get("/playlist/<playlist_ids>")
@_error_handler
def playlist_analysis(playlist_ids):
    analysis_data = sp_handler.get_playlist_analytics(playlist_ids.split(","), market=_get_market_from_cookie())
    return _do_analysis(analysis_data)
    

@app.get("/album/<album_ids>")
@_error_handler
def album_analysis(album_ids):
    analysis_data = sp_handler.get_album_analytics(album_ids.split(","), market=_get_market_from_cookie())
    return _do_analysis(analysis_data)


@app.get("/artist/<artist_id>")
@_error_handler
def artist_lookup(artist_id):
    market = _get_market_from_cookie()
    data = {}
    data["artist"] = sp_handler.get_artist(artist_id)
    data["top_tracks"] = sp_handler.get_artist_top_tracks(artist_id, market=market)
    data["albums"] = sp_handler.get_artist_content(artist_id, "album", market=market)
    data["singles"] = sp_handler.get_artist_content(artist_id, "single", market=market)
    data["compilations"] = sp_handler.get_artist_content(artist_id, "compilation", market=market)
    appears_on, appears_total, next_page = sp_handler.get_artist_appears_on(artist_id, market=market)
    data["appears_on"] = appears_on
    data["appears_on_total"] = appears_total
    data["related_artists"] = sp_handler.get_artist_related(artist_id)
    data["next"] = next_page
    return render_template("artist.html", data=data)


@app.get("/track/<track_id>")
@_error_handler
def single_track_analysis(track_id):
    analysis_data = sp_handler.get_tracks_analytics([track_id], market=_get_market_from_cookie())
    analysis_data.name = "< single track >"
    return _do_analysis([analysis_data])


@app.get("/user/<username>")
def user_playlists(username):
    data = {"username": username, "user_found": False}
    return_code = 200
    try:
        playlists, total, next_page = sp_handler.get_user_playlists(username, market=_get_market_from_cookie())
        data["user_found"] = True
        data["playlists"] = playlists
        data["total"] = total
        data["next"] = next_page
    except ValueError as err:
        # empty username 
        return _return_flash_error([str(err)])
    except ContentNotFoundError as err:
        # no user found with the entered name
        print(err)
        return_code = 404
    
    return render_template("user.html", data=data), return_code


@app.get("/load-more")
def load_next_page():
    page_url = request.args.get("next-page", None)
    page_type = request.args.get("next-type", None)
    
    try:
        next_items, next_page = sp_handler.get_next_page(page_url, market=_get_market_from_cookie())
        return {"items": render_template(f"data_tables/{page_type}.html", results=next_items), "next": next_page}
    except ContentNotFoundError as err:
        error = err.args[0]["error"]
        return error["message"], error["status"]
    except TemplateNotFound as ex:
        # happens if the page_type does not map to a proper resource
        return "", 404


if DEBUG_MODE:
    @app.get("/test")
    def testing_charts():
        test_data = _get_data_for_testing()
        return _do_analysis(test_data)


@app.errorhandler(404)
def error_404(error):
    return render_template("error.html"), 404


@app.errorhandler(405)
def error_405(error):
    return render_template("error.html"), 405



if __name__ == "__main__":
    app.run(debug=DEBUG_MODE)
