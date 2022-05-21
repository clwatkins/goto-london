# Find and cache StopPoints from TFL.
import hashlib
import json
from typing import Any, Union

from .common import get_config, STOP_POINT_CACHE_NAME, TFL_MODALITIES
from .tfl_api import TflApi


_STOP_POINTS_CACHE_TYPE = dict[
    Union["hash", TFL_MODALITIES] : Union[str, list[dict[str, dict]]]
]
_CONFIG_TYPE = dict[str, Any]


class CacheException(Exception):
    pass


def _get_config_hash(config: _CONFIG_TYPE) -> str:
    return hashlib.md5(str(config).encode("utf-8")).hexdigest()


def _assemble_unique_stops_from_config(
    config: _CONFIG_TYPE,
) -> dict[TFL_MODALITIES, set[str]]:

    bus_destinations: set[str] = set()
    tube_destinations: set[str] = set()

    for _, destination_config in config["destinations"].items():
        for modality, modality_config in destination_config.items():
            if modality == "bus":
                bus_destinations.update(
                    [
                        str(modality_config["origin_stop_id"]),
                        str(modality_config["destination_stop_id"]),
                    ]
                )

            if modality == "tube":
                tube_destinations.update(
                    [
                        modality_config["origin_station"],
                        modality_config["destination_station"],
                    ]
                )

        return {"bus": bus_destinations, "tube": tube_destinations}


def _get_tfl_stop_points(
    unique_stops: dict[TFL_MODALITIES, set[str]]
) -> _STOP_POINTS_CACHE_TYPE:
    api = TflApi()
    tfl_stop_points: _STOP_POINTS_CACHE_TYPE = dict()

    for modality, stops in unique_stops.items():
        tfl_stop_points[modality] = {}

        for stop in stops:
            search_reponse = api.search_stop_points(stop, [modality])
            try:
                best_match = search_reponse["matches"][0]
            except (KeyError, IndexError):
                raise Exception(
                    f"TFL API returned no StopPoint match for stop "
                    f"'{stop}' using modality '{modality}'"
                )

            tfl_stop_points[modality][stop] = best_match

    return tfl_stop_points


def _get_from_cache(config_hash: str) -> _STOP_POINTS_CACHE_TYPE:
    with open(STOP_POINT_CACHE_NAME, "r") as f:
        cache = json.loads(f.read())

    if cache["hash"] == config_hash:
        return cache
    else:
        raise CacheException("Mis-match between cache and current config hash")


def _write_to_cache(tfl_stop_points: _STOP_POINTS_CACHE_TYPE, config_hash: str):
    with open(STOP_POINT_CACHE_NAME, "w") as f:
        f.write(json.dumps({"hash": config_hash} | tfl_stop_points))


def load_or_generate_cache() -> _STOP_POINTS_CACHE_TYPE:
    config: _CONFIG_TYPE = get_config()
    config_hash: str = _get_config_hash(config)

    try:
        tfl_stop_points = _get_from_cache(config_hash)
    except (FileNotFoundError, CacheException):
        tfl_stop_points = None

    if not tfl_stop_points:
        unique_stop_points = _assemble_unique_stops_from_config(config)
        tfl_stop_points = _get_tfl_stop_points(unique_stop_points)
        _write_to_cache(tfl_stop_points, config_hash)

    print(tfl_stop_points)
    return tfl_stop_points


if __name__ == '__main__':
    load_or_generate_cache()
