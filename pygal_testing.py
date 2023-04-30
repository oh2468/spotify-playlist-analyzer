"""
Trying to decide how to visualize/represent the data.
"""

import pygal
import json
import random
import itertools
from collections import Counter
from datetime import timedelta



with open("spotify_responses/analysis.json", "r", encoding="UTF-8") as file: data = json.load(file)

#danceability = [tr["audio_feature"]["danceability"] for tr in data]

key_string_map = [
    "C", "C♯, D♭",
    "D", "D♯, E♭",
    "E", "F",
    "F♯, G♭", "G",
    "G♯, A♭", "A",
    "A♯, B♭", "B",
]

mode_string_map = ["minor", "major"]

names = []
danceability = []
energy = []
key = []
key_mode = []
loudness = []
mode = []
speechiness = []
acousticness = []
instrumentalness = []
liveness = []
valence = []
tempo = []
duration_ms = []
time_signature = []


for track in data:
    af = track["audio_feature"]
    names.append(track["track"]["name"])
    danceability.append(af["danceability"])
    energy.append(af["energy"])
    key.append(af["key"])
    key_mode.append((af["key"], af["mode"]))
    loudness.append(af["loudness"])
    mode.append(af["mode"])
    speechiness.append(af["speechiness"])
    acousticness.append(af["acousticness"])
    instrumentalness.append(af["instrumentalness"])
    liveness.append(af["liveness"])
    valence.append(af["valence"])
    tempo.append(af["tempo"])
    duration_ms.append(af["duration_ms"])
    time_signature.append(af["time_signature"])


box_plot = pygal.Box()
box_plot.title = "Playlist Song Data Analysis"
box_plot.add("danceability", danceability)
box_plot.add("energy", energy)
box_plot.add("speachiness", speechiness)
box_plot.add("acousticness", acousticness)
box_plot.add("instrumentalness", instrumentalness)
box_plot.add("valence", valence)
box_plot.add("liveness", liveness)


tempo_rounded = [round(t) for t in tempo]
tempo_counted = sorted(Counter(tempo_rounded).items(), key=lambda k: k[0])
# print(tempo_rounded)
# print(tempo_counted)

tempo_plot = pygal.Bar()
tempo_plot.title = "Song BPMs"
tempo_plot.x_labels = [str(t[0]) for t in tempo_counted]
tempo_plot.add("tempo", [t[1] for t in tempo_counted])


duration_plot = pygal.Bar()
duration_plot.show_legend = False
duration_plot.title = "Song durations"
duration_plot.value_formatter = lambda x: str(timedelta(milliseconds=x)).split(".")[0]
#duration_plot.add("duration", [{"value": dur, "label": name} for name, dur in duration_ms])
for name, dur in zip(names, duration_ms):
    duration_plot.add(name, dur)


box_plot_2 = pygal.Box()
box_plot_2.title = "Song Info"
box_plot_2.add("key", key)
box_plot_2.add("time signature", time_signature)

def get_percentage(lst, item):
    count = lst.count(item)
    total = len(lst)
    pc = (count / total) * 100
    return (count, total, f"{pc:.2f}%")

mode_plot = pygal.Bar()
mode_plot.title = "Modality counts"
#mode_plot.value_formatter = lambda x: f"{((x / len(mode)) * 100):.2f}%"
major_perc = get_percentage(mode, 1)
mode_plot.add("major", [{"value": major_perc[0], "label": major_perc[2]}])
minor_perc = get_percentage(mode, 0)
mode_plot.add("minor", [{"value": minor_perc[0], "label": minor_perc[2]}])

mode_pie = pygal.Pie()
mode_pie.title = "Modality Count"
mode_pie.add("major", [{"value": major_perc[0], "label": major_perc[2]}])
mode_pie.add("minor", [{"value": minor_perc[0], "label": minor_perc[2]}])

line_plot = pygal.Line()
line_plot.title = "Song BPMs"
line_plot.show_legend = False
line_plot.add("bpms", [{"value": t, "label": n} for t, n in zip(tempo, names)])

#key_plot = pygal.XY(legend_at_bottom=True)
key_plot = pygal.XY()
key_plot.title = "Key and Modality"
key_plot.value_formatter = lambda y: f"Key - {key_string_map[int(y - 1)]}"
key_plot.x_value_formatter = lambda x: f"#{x}: {names[int(x - 1)]}"
#key_plot.add("keys", key)
for i, key_map in enumerate(key_string_map):
    # "label": f"modality: {mode_string_map[mode[j]]}"
    # "label": f"{names[j]}"
    key_plot.add(key_map, [{"value": ((j + 1), (i + 1)), "label": f"mode: {mode_string_map[mode[j]]} "} for j, k in enumerate(key) if k == i])
key_plot.y_labels = key_string_map
key_plot.x_labels = range(1, len(names) + 1)


loudness_plot = pygal.Line()
loudness_plot.title = "Song Loudness (in db)"
loudness_plot.add("loudness", loudness)

key_plot_2 = pygal.Line()
key_plot_2.title = "Key and Modality 2"
key_plot_2.value_formatter = lambda y: key_string_map[int(y)]
for i, key_map in enumerate(key_string_map):
    key_plot_2.add(key_map, [i if k == i else None for k in key])
key_plot_2.x_labels = range(1, len(names) + 1)

key_plot_3 = pygal.XY(y_labels_major_every=1, show_minor_y_labels=True)
key_plot_3.title = "Key and Modality 3"
for k, key_map in enumerate(key_string_map):
    for m, mod in enumerate(mode_string_map):
        key_plot_3.add(f"{key_map} - {mod}", [(x + 1, (k * 2) + m) for x, km in enumerate(key_mode) if k == km[0] and m == km[1]])
key_plot_3.y_labels = [f"{k} - {m}" for k in key_string_map for m in mode_string_map]


# box_plot.render_to_file("pygal_tests/song_data.svg")
# tempo_plot.render_to_file("pygal_tests/song_bpms.svg")
# duration_plot.render_to_file("pygal_tests/song_durations.svg")
# box_plot_2.render_to_file("pygal_tests/song_info.svg")
# mode_plot.render_to_file("pygal_tests/song_modes.svg")
# mode_pie.render_to_file("pygal_tests/song_modes_pie.svg")
# line_plot.render_to_file("pygal_tests/song_bpms_line.svg")
# key_plot.render_to_file("pygal_tests/song_keys.svg")
# loudness_plot.render_to_file("pygal_tests/song_loudness.svg")
# key_plot_2.render_to_file("pygal_tests/song_keys_2.svg")
key_plot_3.render_to_file("pygal_tests/song_keys_3.svg")

""""""
#box_plot.add("loudness", loudness)
#box_plot.add("time_signature", time_signature)


