# Server

The FastAPI server reads Spotify playback, renders a 128×64 monochrome frame, and
sends it to the ESP32 at `ws://<server>:8000/ws`. By default it uses lightweight
album artwork rendering. Optional `faces` mode detects a face in the artist's
image, falling back to album artwork when no face is available.

## Start

From this directory:

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Create a `.env` file from the example and add your Spotify application credentials:

```sh
cp .env.example .env
```

Set the Spotify app redirect URI to `http://127.0.0.1:8000/callback`, then open
`http://127.0.0.1:8000/login` to authorize Spotify. The access and refresh tokens are
written to `.env` automatically.

## Debugging

- Open `server/playback_state.jpeg` to inspect the most recently rendered OLED frame.
- Watch the logs for Spotify/API errors and display renders.
