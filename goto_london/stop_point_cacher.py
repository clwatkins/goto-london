# Search and cache StopPoints from TFL based on the stop name.

from collections import defaultdict, namedtuple
from dataclasses import dataclass
import hashlib
import json
import os
from typing import Any, Iterable, Literal, Union

from mashumaro import DataClassDictMixin
import requests as rq

from .common import (
    config_iterator,
    get_config,
    ModalityOption,
    STOP_POINT_CACHE_NAME,
    TflModalitiesType,
)
from .tfl_api import TflApi


# Needs to be hashable for set, so not a dataclass
StopLinePair = namedtuple("StopLinePair", ["from_stop", "to_stop", "line"])


@dataclass
class StopPointsInfo(DataClassDictMixin):
    from_stop_id: str
    to_stop_id: str
    line: str
    direction: str

    def __iter__(self):
        return iter([self.from_stop_id, self.to_stop_id, self.line, self.direction])


_STOP_POINTS_CACHE_TYPE = dict[
    Union[Literal["hash"], TflModalitiesType] : Union[str, dict[str, StopPointsInfo]]
]

_CONFIG_TYPE = dict[str, Any]


class CacheException(Exception):
    pass


class StopPointNotFoundException(Exception):
    def __init__(self, stop_point, modality, line):
        self.message = (
            f"TFL API returned no StopPoint match for stop "
            f"'{stop_point}' using modality '{modality}' and line '{line}'"
        )

    def __str__(self):
        return self.message


class StopPointsDirectionNotFoundException(Exception):
    def __init__(self, from_point, to_point, from_stop_point, to_stop_point):
        self.message = (
            f"TFL API didn't find the direction between StopPoints from "
            f"'{from_point}' and '{to_point}'. Are you sure they're on the same line? "
            f"Searched {from_stop_point}/{to_stop_point} specifically."
        )

    def __str__(self):
        return self.message


def _get_config_hash(config: _CONFIG_TYPE) -> str:
    return hashlib.md5(str(config).encode("utf-8")).hexdigest()


def _build_unique_stop_line_pairs(
    config_iterator: Iterable[tuple[str, TflModalitiesType, ModalityOption]]
) -> dict[TflModalitiesType, set[StopLinePair]]:
    """Assemble set of unique destination pairs from config."""

    unique_destinations = defaultdict(set)

    for _, modality, modality_option in config_iterator:
        unique_destinations[modality].update(
            [
                StopLinePair(
                    modality_option.from_stop,
                    modality_option.to_stop,
                    modality_option.line,
                )
            ]
        )

    return unique_destinations


def _get_stop_point_id(
    *,
    search_term: str,
    get_detail: bool,
    modality: TflModalitiesType,
    stop_line_pair: StopLinePair,
    api: TflApi,
) -> str:
    if get_detail:
        search_response = api.get_stop_point_detail(search_term)
        child_key = "children"
        check_line = True
    else:
        search_response = api.search_stop_points(search_term, [modality])
        child_key = "matches"
        check_line = True

        # If we're finding only the hub-level tube station then it won't include line info
        if modality == "tube":
            check_line = False

    try:
        filtered_responses = api.filter_stop_points_for_modality_and_line(
            results=search_response,
            child_key=child_key,
            modality_key="modes",
            check_line=check_line,
            line_key="lines",
            line=stop_line_pair.line,
            modality=modality,
        )
        stop_point_id = filtered_responses[0]["id"]
    except (KeyError, IndexError):
        raise StopPointNotFoundException(search_term, modality, stop_line_pair.line)

    return stop_point_id


def _get_tfl_stop_points(
    unique_stops: dict[TflModalitiesType, set[StopLinePair]]
) -> dict[TflModalitiesType, dict[str, StopPointsInfo]]:
    api = TflApi()
    tfl_stop_points: _STOP_POINTS_CACHE_TYPE = dict()

    for modality, stop_line_pairs in unique_stops.items():
        # Don't collect TFL data for walking option
        if modality == "walk":
            continue

        tfl_stop_points[modality] = {}

        for stop_line_pair in stop_line_pairs:
            stop_point_ids: list[str, str] = []
            # Ordered from_dest, to_dest
            for stop in (stop_line_pair.from_stop, stop_line_pair.to_stop):
                stop_point_id = _get_stop_point_id(
                    search_term=stop,
                    get_detail=False,
                    modality=modality,
                    stop_line_pair=stop_line_pair,
                    api=api,
                )

                # If the modality is 'bus' then we can be confident that we have the right ID.
                # That's because the stop IDs are direction-specific
                if modality == "bus":
                    stop_point_ids.append(stop_point_id)
                # Otherwise (for tube) we need to get one more level of detail
                # to confirm the modality-specific id
                else:
                    stop_point_id = _get_stop_point_id(
                        search_term=stop_point_id,
                        get_detail=True,
                        modality=modality,
                        stop_line_pair=stop_line_pair,
                        api=api,
                    )
                    stop_point_ids.append(stop_point_id)

            # Get the canonical direction of travel between the stop points
            try:
                direction = api.get_direction_between_stop_points(*stop_point_ids)
            except rq.exceptions.HTTPError:
                raise StopPointsDirectionNotFoundException(
                    stop_line_pair.from_stop, stop_line_pair.to_stop, *stop_point_ids
                )

            tfl_stop_points[modality][
                f"{stop_line_pair.from_stop} - {stop_line_pair.to_stop} - {stop_line_pair.line}"
            ] = StopPointsInfo(
                stop_point_ids[0], stop_point_ids[1], stop_line_pair.line, direction
            )

    return tfl_stop_points


def _load_cache(
    config_hash: str, cache_path: os.PathLike = STOP_POINT_CACHE_NAME
) -> _STOP_POINTS_CACHE_TYPE:
    with open(cache_path, "r") as f:
        raw_cache = json.loads(f.read())

    cache = {}
    if raw_cache["hash"] == config_hash:
        for cache_key in raw_cache:
            if cache_key == "hash":
                continue

            # Re-load serialised items into StopPointsInfo objects
            cache[cache_key] = {
                k: StopPointsInfo.from_dict(v) for k, v in raw_cache[cache_key].items()
            }

        return cache
    else:
        raise CacheException("Mis-match between cache and current config hash")


def _write_cache(
    tfl_stop_points: dict[TflModalitiesType, dict[str, StopPointsInfo]],
    config_hash: str,
    cache_path: os.PathLike = STOP_POINT_CACHE_NAME,
):
    prepped_cache = {}
    for cache_key in tfl_stop_points:
        prepped_cache[cache_key] = {
            k: v.to_dict() for k, v in tfl_stop_points[cache_key].items()
        }

    with open(cache_path, "w") as f:
        f.write(json.dumps({"hash": config_hash} | prepped_cache))


def load_or_generate_cache() -> _STOP_POINTS_CACHE_TYPE:
    """Loads a StopPoint cache from memory or generates a new one.

    We:
        - Generate a hash of the config to track versioning
        - Attempt to load an existing cache from memory, failing
        if the cache isn't found or is out of date (based its hash)
        - Return the saved cache, or generate a new one by:
            - Building a set of all unique stops listed in the config
            - Polling the TFL API for the naptanIds of the StopPoints
            - returned by our search
            - Building unique route combinations to cache, containing:
                origin_naptan_id, destination_naptan_id, line, direction
    """
    config: _CONFIG_TYPE = get_config()
    config_hash: str = _get_config_hash(config)

    try:
        tfl_stop_points = _load_cache(config_hash)
    except (FileNotFoundError, CacheException):
        tfl_stop_points = None

    if not tfl_stop_points:
        unique_stop_points = _build_unique_stop_line_pairs(config_iterator(config))
        tfl_stop_points = _get_tfl_stop_points(unique_stop_points)
        _write_cache(tfl_stop_points, config_hash)

    return tfl_stop_points


def get_from_cache(
    modality_option: ModalityOption, cache: _STOP_POINTS_CACHE_TYPE
) -> StopPointsInfo:
    return cache[modality_option.modality][
        f"{modality_option.from_stop} - {modality_option.to_stop} - {modality_option.line}"
    ]


def main():
    print(load_or_generate_cache())
