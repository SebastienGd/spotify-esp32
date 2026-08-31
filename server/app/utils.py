import os
from pathlib import Path
from typing import cast

from omegaconf import DictConfig, OmegaConf


def persist_spotify_token(token):
    env_path = ".env"
    env_values = {}

    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env_values[key.strip()] = value.strip()

    env_values["SPOTIFY_ACCESS_TOKEN"] = token.access_token
    if token.refresh_token:
        env_values["SPOTIFY_REFRESH_TOKEN"] = token.refresh_token

    with open(env_path, "w") as f:
        for key, value in env_values.items():
            f.write(f"{key}={value}\n")

    os.environ["SPOTIFY_ACCESS_TOKEN"] = token.access_token
    if token.refresh_token:
        os.environ["SPOTIFY_REFRESH_TOKEN"] = token.refresh_token


def load_conf() -> DictConfig:
    config_dir = Path(__file__).parents[1] / "conf"
    configs = [OmegaConf.load(path) for path in sorted(config_dir.glob("*.yml"))]

    return cast(DictConfig, OmegaConf.merge(*configs))
