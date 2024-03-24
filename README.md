# Album Ranker
A web app that ranks albums containing songs you've liked on Spotify by the number of liked songs.

## Installation
1. Create a Python virtual environment
2. Activate the environment and install the requirements: `pip install -r requirements.txt`

## Configuration
1. Log on to the [Spotify app developer dashboard](https://developer.spotify.com/dashboard).
2. Create an app using the "Create app" button.
3. Click the "Settings" button. Click the "View client secret" button.
4. Copy `.env.example` to a new file named `.env` (this will be hidden to everyone but you).
5. Replace `YourIDHere`, `YourSecretHere`, and `YourURIHere` with the client ID and secret on the page, and a redirect URI, respectively. Uncomment `PROXY` to enable reverse proxies.

## Turning the server on and off
Type `waitress-serve --host 127.0.0.1 ranker:app` to start the server on your machine. Press `Ctrl+C` to shut off the server.
