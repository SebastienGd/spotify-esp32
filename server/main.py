import asyncio
from logging import INFO, basicConfig, getLogger

from dotenv import load_dotenv
from fastapi import FastAPI, Query, WebSocket
from fastapi.responses import RedirectResponse

from app.orchestrator import Orchestrator
from app.spotify import Spotify
from app.utils import load_conf, persist_spotify_token

basicConfig(level=INFO)
logger = getLogger(__name__)
load_dotenv()

app = FastAPI()

conf = load_conf()


@app.get("/login")
async def login():
    spotify = Spotify(conf)
    return RedirectResponse(spotify.build_auth_url())


@app.get("/callback")
async def callback(code: str = Query(...)):
    spotify = Spotify(conf)
    token = await spotify.fetch_spotify_token(code)
    persist_spotify_token(token)
    conf.spotify.access_token = token.access_token
    if token.refresh_token:
        conf.spotify.refresh_token = token.refresh_token
    logger.info("Spotify user token acquired")
    return {"status": "ok", "token_type": token.token_type, "expires_in": token.expires_in}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    orchestrator = Orchestrator(conf)

    playback_task = asyncio.create_task(orchestrator.run(websocket))

    try:
        await orchestrator.register_event_listeners(websocket)
    finally:
        playback_task.cancel()
        await asyncio.gather(playback_task, return_exceptions=True)
