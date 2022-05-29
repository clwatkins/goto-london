"""Common settings and utility functions."""
from dataclasses import dataclass
import logging
import sys
from typing import Any, Iterator, Literal, Optional, Union

import arrow
from dotenv import dotenv_values
import yaml

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
LOGGER = logging

CONFIG_FILE_NAME = "config.yaml"
ENV_FILE_NAME = ".env"
STOP_POINT_CACHE_NAME = "tfl_stop_points.cache"

ENV_TFL_APP_ID = "TFL_API_APP_ID"
ENV_TFL_APP_KEY = "TFL_API_APP_KEY"
ENV_TIMEZONE = "TIMEZONE"
ENV = dotenv_values(ENV_FILE_NAME)

TflModalitiesType = Literal["bus", "tube"]
NonTflModalitiesType = Literal["walk"]
AllModalitiesType = Union[TflModalitiesType, NonTflModalitiesType]


@dataclass
class ModalityOption:
    """Describes a particular destination-modality option from config."""

    modality: AllModalitiesType
    from_stop: Optional[str]
    to_stop: Optional[str]
    line: Optional[str]
    time_from: int
    time_to: Optional[int]


def get_config() -> dict[str, Any]:
    """Load YAML config from file."""
    with open(CONFIG_FILE_NAME, "r") as file:
        config = yaml.safe_load(file)

    if not config:
        raise FileNotFoundError(
            f"Didn't find config file under name {CONFIG_FILE_NAME}"
        )
    return config


def config_iterator(
    config: dict[str, Any]
) -> Iterator[tuple[str, AllModalitiesType, ModalityOption]]:
    """Iterate over destination-modality pairs (returning ModalityOptions)."""
    for destination, destination_config in config["destinations"].items():
        for modality, modality_config in destination_config.items():
            if modality == "bus":
                modality_option = ModalityOption(
                    modality,
                    str(modality_config["origin_stop_id"]),
                    str(modality_config["destination_stop_id"]),
                    str(modality_config["number"]),
                    int(modality_config["origin_walking_time"]),
                    int(modality_config["destination_walking_time"]),
                )

            elif modality == "tube":
                modality_option = ModalityOption(
                    modality,
                    modality_config["origin_station"],
                    modality_config["destination_station"],
                    modality_config["line"],
                    int(modality_config["origin_walking_time"]),
                    int(modality_config["destination_walking_time"]),
                )

            else:
                # Walking time option has just one populated field
                modality_option = ModalityOption(
                    modality, None, None, None, modality_config["total_time"], None
                )

            yield destination, modality, modality_option


def get_local_timestamp(timestamp: Optional[str] = None) -> arrow.Arrow:
    """Localise a target timestamp, or the current time."""
    target_tz = ENV[ENV_TIMEZONE]

    if timestamp:
        base_ts = arrow.get(timestamp)
    else:
        base_ts = arrow.utcnow()

    return base_ts.to(target_tz)
