# Spotify Playlist Analyzer

## Description

A website that can be used to analyze the public content on Spotify. Users can either manually enter or upload a file with Spotify urls which are then analyzed. The analysis consists of graphs/charts and a table with the song data that is available from the Spotify API found at: https://developer.spotify.com/documentation/web-api/reference/get-several-audio-features. It is possible to analyze more than one playlist or album at a time for easier comparisons, e.g. if you want to compare multiple albums from an artists catalog. Which can be done when searching for an artist and the artist page shows the various content like albums, singles or compilations.

Users also have the ability to search for playlists, albums, artists and tracks or try to access the public playlists of a specific Spotify user. It is however not possible to search for users since that is not available with the API. But if you know of a public playlist they have, you can search for that and then take the ```User ID``` of that playlist (available in the playlist search result table) and that way access all the other public playlists of that user with that specific ID.

Keep in mind that the data is only as reliable as its source, in this case Spotify.

## Getting Started

1. Create a Spotify account and register it at: https://developer.spotify.com/
2. Follow their instuctions to get an access token at: https://developer.spotify.com/documentation/web-api
3. Download Python and this repo and install all the dependencies
    1. Download and install Python from: https://www.python.org/
    2. Open a terminal and use pip to install the dependencies e.g. ```pip install flask```
4. Add you token to the file: ```api_token.txt``` like following: ```Basic <token_code_here>```
5. Open a terminal in the directory where the ```app.py``` file is located
6. Run the website by typing ```python app.py``` in the termianl window
7. Visit the website by typing ```localhost:5000``` in your browsers address/url bar
8. Press ```CTRL+C``` in the terminal window to stop the server running the website
9. Optional: Change some variables in the ```app.py``` file, like ```app.secret_key``` to a string of your choice. Or switch to ```DEBUG_MODE = False``` if the server is too verbose or you don't want the file writes to happen.


### Dependencies

* Python (developed with v. 3.10.5)
* Flask (developed with v. 2.2.3)
* Requests (developed with v. 2.28.2)
* Pygal (Developed with v. 3.0.0)

* Your own Spotify API key
