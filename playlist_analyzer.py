import pygal
import json
from collections import Counter
from datetime import timedelta
from pygal.style import DarkGreenBlueStyle
from pygal.style import Style


# with open("spotify_responses/analysis.json", "r", encoding="UTF-8") as file: data = json.load(file)

chart_js_code = ["file://static/pygal.js"]

def key_mode_value(k, m):
    return (k * 2) + m


def key_mode_string(k, m, v=None):
    # print(f"k: {k}, m: {m}, v: {v}")
    if v:
        # v = int(v)
        return f"{key_string_map[v // 2]} - {mode_string_map[v % 2]}"
    else:
        return f"{key_string_map[k]} - {mode_string_map[m]}"


def time_formatter(time_ms):
    return str(timedelta(milliseconds=time_ms)).split(".")[0]


def time_signature_formatter(time_sig):
    # return f"{int(time_sig) + 3}/4"
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

def get_data_charts(data):
    print(f"LENGTH OF DATA: {len(data)}")
    if not data:
        return {}

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
            value["data"].append(analysis_value)
            value["total"] += analysis_value


    for key, value in seperated_data.items():
        if key not in skip_average:
            value["data"].insert(0, value["total"] / total_songs)


    # line_plot_style = Style(colors=["#007700"])
    # line_plot_style = Style(colors=["#ffa500"])
    line_plot_style = Style(colors=["#000000"])
    for key in line_plots:
        line_plot = pygal.Line(show_legend=False, dots_size=5, style=line_plot_style, js=chart_js_code)
        # line_plot = pygal.Line(show_legend=False, dots_size=5, style={"colors": ["#007700"]})
        line_plot.title = f"Song {plot_titles.get(key, key.capitalize())}"
        # print(seperated_data[key]["total"])
        line_plot.add(key, seperated_data[key]["data"])
        line_plot.x_labels = name_strings

        if 0 <= seperated_data[key]["data"][0] <= 1:
            line_plot.range = (0, 1)

        if key == "duration_ms":
            line_plot.value_formatter = time_formatter
            line_plot.title += f" (total: {time_formatter(seperated_data[key]['total'])})"

        if key == "time_signature":
            line_plot.max_scale = 5
            # line_plot.range = (1, 5)
            line_plot.range = (3, 7)
            line_plot.x_labels = line_plot.x_labels[1:]
            line_plot.value_formatter = time_signature_formatter

        if key == "loudness":
            line_plot.range = (-60, 0)

        if key == "tempo":
            line_plot.value_formatter = float_to_int_rounder

        #line_plot.render_to_file(f"pygal_tests/tests_2/line_plot_{key}.svg")
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

    #box_plot.render_to_file("pygal_tests/tests_2/box_plot_collected.svg")
    data_charts["collected"].append(box_plot.render_data_uri())


    xy_plot = pygal.XY(title="Key and Modality", dots_size=5, js=chart_js_code, range=(1, key_mode_len + 1))
    xy_plot.value_formatter = lambda y: ""
    xy_plot.x_value_formatter = lambda x: name_strings[int(x)]
    for k, key_map in enumerate(key_string_map):
        for m, mode_map in enumerate(mode_string_map):
            xy_plot.add(key_mode_string(k, m), [(x + 1, 1 + key_mode_value(k, m)) for x, y in enumerate(key_mode) if y[0] == k and y[1] == m])
    xy_plot.y_labels = key_string_map
    xy_plot.x_labels = range(1, total_songs + 1)

    # xy_plot.render_to_file("pygal_tests/tests_2/xy_plot_key_mode.svg")
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

    # pie_plot.render_to_file("pygal_tests/tests_2/pie_plot_key_mode.svg")
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

        # box_plot.render_to_file("pygal_tests/tests_2/box_plot_tempo.svg")
        data_charts[key].append(box_plot.render_data_uri())

    return data_charts
