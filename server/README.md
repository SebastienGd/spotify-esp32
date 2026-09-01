# Server

The FastAPI server reads Spotify playback, finds a face in the current artist's image when possible, renders a 128×64 monochrome frame, and sends it to the ESP32 at `ws://<server>:8000/ws`. If no artist face is found, it uses the track's album artwork instead.

## Start

From this directory:

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Create a `.env` file with Spotify application credentials:

```dotenv
SPOTIFY_CLIENT_ID=...
SPOTIFY_API_KEY=...
```

Open `http://127.0.0.1:8000/login` to authorize Spotify. The access and refresh tokens are then written to `.env` automatically.

## Debugging

- Open `server/playback_state.jpeg` to inspect the most recently rendered OLED frame.
- Watch the Uvicorn logs for Spotify/API errors and display renders.
- The ESP32 must use your computer's LAN IP in its WebSocket URL; `localhost` refers to the ESP32 itself.
