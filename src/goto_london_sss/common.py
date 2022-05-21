from typing import Literal

import yaml

ENV_FILE_NAME = ".env"
CONFIG_FILE_NAME = "config.yaml"

ENV_TFL_APP_ID = "TFL_API_APP_ID"
ENV_TFL_APP_KEY = "TFL_API_APP_KEY"

STOP_POINT_CACHE_NAME = "tfl_stop_points.cache"
TFL_MODALITIES = Literal["bus", "tube"]


def get_config():
    with open(CONFIG_FILE_NAME, "r") as file:
        config = yaml.safe_load(file)

    if not config:
        raise FileNotFoundError(f"Didn't find config file under name {CONFIG_FILE_NAME}")
    return config
