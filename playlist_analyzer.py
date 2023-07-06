import pygal
from collections import Counter
from datetime import timedelta
from pygal.style import DarkGreenBlueStyle
from pygal.style import Style
from pathlib import Path


chart_js_code = ["file://static/pygal.js"]
_DEBUG_OUTPUT_DIR = Path(Path(__file__).parent, "pygal_tests")


def key_mode_value(k, m):
    return (k * 2) + m


def key_mode_string(k, m, v=None):
    # print(f"k: {k}, m: {m}, v: {v}")
    if v:
        return f"{key_string_map[v // 2]} - {mode_string_map[v % 2]}"
    else:
        return f"{key_string_map[k]} - {mode_string_map[m]}"


def time_formatter(time_ms):
    return str(timedelta(milliseconds=time_ms)).split(".")[0]


def time_signature_formatter(time_sig):
    return f"{int(time_sig)}/4"


def float_to_int_rounder(val):
    return str(round(val))


key_string_map = [
    "C", "C♯, D♭",
    "D", "D♯, E♭",
    "E", "F",
    "F♯, G♭", "G",
    "G♯, A♭", "A",
    "A♯, B♭", "B",
]

mode_string_map = ["minor", "major"]

key_mode_len = len(key_string_map) * len(mode_string_map)

data_keys = [
    "danceability", "energy", "key",
    "loudness", "mode", "speechiness",
    "acousticness", "instrumentalness", "liveness",
    "valence", "tempo", "duration_ms",
    "time_signature",
]

line_plots = [
    "danceability", "energy", "loudness",
    "speechiness", "acousticness", "instrumentalness",
    "liveness", "valence", "tempo", "duration_ms",
    "time_signature"
]

plot_titles = {
    "loudness": "Loudness (in db)",
    "tempo": "BPM (Beats Per Minute)",
    "duration_ms": "Durations",
}

collected_box_plot = [
    "danceability", "energy", "speechiness",
    "acousticness", "instrumentalness", "valence",
    "liveness",
]

box_plots = ["tempo", "duration_ms"]

skip_average = ["key", "time_signature"]

data_descriptions = {
    "danceability": "Danceability describes how suitable a track is for dancing based on a combination of musical elements including tempo, rhythm stability, beat strength, and overall regularity. A value of 0.0 is least danceable and 1.0 is most danceable.",
    "energy": "Energy is a measure from 0.0 to 1.0 and represents a perceptual measure of intensity and activity. Typically, energetic tracks feel fast, loud, and noisy. For example, death metal has high energy, while a Bach prelude scores low on the scale. Perceptual features contributing to this attribute include dynamic range, perceived loudness, timbre, onset rate, and general entropy.",
    "key": "The key the track is in. Integers map to pitches using standard Pitch Class notation. E.g. 0 = C, 1 = C♯/D♭, 2 = D, and so on. If no key was detected, the value is -1.",
    "mode": "Mode indicates the modality (major or minor) of a track, the type of scale from which its melodic content is derived. Major is represented by 1 and minor is 0.",
    "loudness": "The overall loudness of a track in decibels (dB). Loudness values are averaged across the entire track and are useful for comparing relative loudness of tracks. Loudness is the quality of a sound that is the primary psychological correlate of physical strength (amplitude). Values typically range between -60 and 0 db.",
    "speechiness": "Speechiness detects the presence of spoken words in a track. The more exclusively speech-like the recording (e.g. talk show, audio book, poetry), the closer to 1.0 the attribute value. Values above 0.66 describe tracks that are probably made entirely of spoken words. Values between 0.33 and 0.66 describe tracks that may contain both music and speech, either in sections or layered, including such cases as rap music. Values below 0.33 most likely represent music and other non-speech-like tracks.",
    "acousticness": "A confidence measure from 0.0 to 1.0 of whether the track is acoustic. 1.0 represents high confidence the track is acoustic.",
    "instrumentalness": "Predicts whether a track contains no vocals. \"Ooh\" and \"aah\" sounds are treated as instrumental in this context. Rap or spoken word tracks are clearly \"vocal\". The closer the instrumentalness value is to 1.0, the greater likelihood the track contains no vocal content. Values above 0.5 are intended to represent instrumental tracks, but confidence is higher as the value approaches 1.0.",
    "liveness": "Detects the presence of an audience in the recording. Higher liveness values represent an increased probability that the track was performed live. A value above 0.8 provides strong likelihood that the track is live.",
    "valence": "A measure from 0.0 to 1.0 describing the musical positiveness conveyed by a track. Tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence sound more negative (e.g. sad, depressed, angry).",
    "tempo": "The overall estimated tempo of a track in beats per minute (BPM). In musical terminology, tempo is the speed or pace of a given piece and derives directly from the average beat duration.",
    # "duration_ms": "The duration of the track in milliseconds.",
    "duration_ms": "The duration of the track.",
    "time_signature": "An estimated time signature. The time signature (meter) is a notational convention to specify how many beats are in each bar (or measure). The time signature ranges from 3 to 7 indicating time signatures of \"3/4\", to \"7/4\".",
    "key_map": ", ".join(f"{i} = {k}" for i, k in enumerate(key_string_map)),
}


def get_data_charts(data, debug_mode=False):
    if not data:
        return {}

    debug_charts = {}

    seperated_data = {key: {"data": [], "total": 0} for key in data_keys}
    total_songs = len(data)
    name_strings = ["_DATA_AVERAGE_"]
    names = []
    key_mode = []
    data_charts = {key: [] for key in data_keys}
    data_charts["collected"] = []

    for i, track in enumerate(data, 1):
        af = track["audio_feature"]
        names.append(track["track"]["name"])
        name_strings.append(f"#{i}: {names[-1]}")
        key_mode.append((af["key"], af["mode"]))

        for key, value in seperated_data.items():
            analysis_value = af[key]
            value["data"].append(analysis_value if key != "tempo" else round(analysis_value))
            value["total"] += value["data"][-1]


    for key, value in seperated_data.items():
        if key not in skip_average:
            value["data"].insert(0, value["total"] / total_songs)


    # line_plot_style = Style(colors=["#007700"])
    # line_plot_style = Style(colors=["#ffa500"])
    line_plot_style = Style(colors=["#000000"])
    for key in line_plots:
        line_plot = pygal.Line(show_legend=False, dots_size=5, style=line_plot_style, js=chart_js_code)
        line_plot.title = f"Song {plot_titles.get(key, key.capitalize())}"

        line_plot.add(key, seperated_data[key]["data"])
        line_plot.x_labels = name_strings

        if 0 <= seperated_data[key]["data"][0] <= 1:
            line_plot.range = (0, 1)

        if key == "duration_ms":
            line_plot.value_formatter = time_formatter
            line_plot.title += f" (total: {time_formatter(seperated_data[key]['total'])})"

        if key == "time_signature":
            line_plot.max_scale = 5
            line_plot.range = (3, 7)
            line_plot.x_labels = line_plot.x_labels[1:]
            line_plot.value_formatter = time_signature_formatter

        if key == "loudness":
            line_plot.range = (-60, 0)

        debug_charts[f"line_plot_{key}"] = line_plot
        data_charts[key].append(line_plot.render_data_uri())


    box_plot = pygal.Box(
        title="Collected Song Data Analysis",
        box_mode="tukey",
        legend_at_bottom=True,
        range=(0, 1),
        js=chart_js_code
    )
    for box in collected_box_plot:
        box_plot.add(box, seperated_data[box]["data"])

    debug_charts["box_plot_collected"] = box_plot
    data_charts["collected"].append(box_plot.render_data_uri())


    xy_plot = pygal.XY(title="Key and Modality", dots_size=5, js=chart_js_code, range=(1, key_mode_len + 1))
    xy_plot.value_formatter = lambda y: ""
    xy_plot.x_value_formatter = lambda x: name_strings[int(x)]
    for k, key_map in enumerate(key_string_map):
        for m, mode_map in enumerate(mode_string_map):
            xy_plot.add(key_mode_string(k, m), [(x + 1, 1 + key_mode_value(k, m)) for x, y in enumerate(key_mode) if y[0] == k and y[1] == m])
    xy_plot.y_labels = key_string_map
    xy_plot.x_labels = range(1, total_songs + 1)

    debug_charts["xy_plot_key_mode"] = xy_plot
    data_charts["key"].append(xy_plot.render_data_uri())


    pie_count = Counter(key_mode)
    pie_plot = pygal.Pie(title="Key and Modality", js=chart_js_code)
    for i, key in enumerate(key_string_map):
        pie_plot.add(key, [
            {"value": pie_count.get((i, 0)), "label": mode_string_map[0] },
            {"value": pie_count.get((i, 1)), "label": mode_string_map[1] }
            ]
        )
    pie_plot.value_formatter = lambda x: f"{x}/{total_songs} = {round(100 * (x / total_songs), 2)}%"

    debug_charts["pie_plot_key_mode"] = pie_plot
    data_charts["key"].append(pie_plot.render_data_uri())

    for key in box_plots:
        box_plot = pygal.Box(
            title=plot_titles.get(key, key.capitalize()),
            box_mode="tukey",
            show_legend=False,
            js=chart_js_code
        )
        box_plot.add("", seperated_data[key]["data"])

        if key == "duration_ms":
            box_plot.value_formatter = time_formatter
        
        if key == "tempo":
            box_plot.value_formatter = float_to_int_rounder

        debug_charts[f"box_plot_{key}"] = box_plot
        data_charts[key].append(box_plot.render_data_uri())

    if debug_mode:
        try:
            for name, plot in debug_charts.items():
                plot.render_to_file(f"{_DEBUG_OUTPUT_DIR}/{name}.svg")
        except Exception as ex:
            print(f"Failed writing the data to the file location: {_DEBUG_OUTPUT_DIR}")


    return data_charts
