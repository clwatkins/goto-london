from typing import Any, Optional

import arrow
from dotenv import dotenv_values
import requests as rq

from .common import (
    ENV_FILE_NAME,
    ENV_TFL_APP_ID,
    ENV_TFL_APP_KEY,
    LOGGER,
    TflModalitiesType,
)


class TflApi:
    def __init__(self):
        self.url_base = "https://api.tfl.gov.uk/"
        self.app_id, self.app_key = self._get_api_creds()

    @staticmethod
    def _get_api_creds() -> (str, str):
        env = dotenv_values(ENV_FILE_NAME)
        return env[ENV_TFL_APP_ID], env[ENV_TFL_APP_KEY]

    def _query(
        self, endpoint: str, params: Optional[dict[str, Any]] = None
    ) -> rq.Response:
        response = rq.get(
            self.url_base + endpoint,
            params={"app_id": self.app_id, "app_key": self.app_key} | (params or {}),
        )
        LOGGER.debug("TflApi call @ %s", response.url)
        if not response.ok:
            response.raise_for_status()
        else:
            return response

    def search_stop_points(
        self, name: str, modes: list[TflModalitiesType]
    ) -> dict[str, Any]:
        search_response = self._query(
            "StopPoint/Search",
            params={
                "query": name,
                "modes": ",".join(modes),
            },
        )
        return search_response.json()

    def get_stop_point_detail(self, stop_point_id: str) -> dict[str, Any]:
        search_response = self._query(f"StopPoint/{stop_point_id}")
        return search_response.json()

    def get_direction_between_stop_points(
        self, from_stop_point: str, to_stop_point: str
    ) -> str:
        search_response = self._query(
            f"StopPoint/{from_stop_point}/DirectionTo/{to_stop_point}"
        )
        return search_response.json()

    def get_next_vehicles_for_line_stop_point(
        self, line: str, stop_point_id: str, direction: str = None
    ) -> list[dict[str, Any]]:

        params = {"direction": direction} if direction else None
        search_response = self._query(f"Line/{line}/Arrivals/{stop_point_id}", params)
        return search_response.json()

    def get_vehicle_arrivals(self, vehicle_id: str) -> list[dict[str, Any]]:
        search_response = self._query(f"Vehicle/{vehicle_id}/arrivals")
        return search_response.json()

    @staticmethod
    def filter_stop_points_for_modality_and_line(
        *,
        results: dict[str, Any],
        child_key: str,
        modality_key: str,
        modality: str,
        check_line: bool = False,
        line_key: str = None,
        line: str = None,
    ):
        filtered_results = []

        for child in results[child_key]:
            if modality in child[modality_key]:
                if check_line:
                    for child_line in child[line_key]:
                        if child_line["name"] == line:
                            filtered_results.append(child)
                            break
                else:
                    filtered_results.append(child)

        return filtered_results

    @staticmethod
    def filter_vehicles_beyond_n_minutes_away(
        next_vehicles: list[dict[str, Any]], n_minutes: int
    ) -> list[dict[str, Any]]:
        filtered_results = []
        # Note we use UTC rather than localised time as that's what
        # API returns
        time_in_n_minutes = arrow.utcnow().shift(minutes=n_minutes)

        for next_vehicle in next_vehicles:
            expected_arrival = arrow.get(next_vehicle["expectedArrival"])
            if expected_arrival >= time_in_n_minutes:
                filtered_results.append(next_vehicle)

        return filtered_results

    @staticmethod
    def get_destination_arrival_from_vehicle_arrivals(
        vehicle_arrivals: list[dict[str, Any]],
        stop_point_id: str,
        line: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:

        for vehicle_arrival in vehicle_arrivals:
            # Optionally filter out vehicles not on the target line
            # (relevant for tube trains that can have duplicate ids)
            if line and (vehicle_arrival["lineName"] != line):
                continue

            if vehicle_arrival["naptanId"] == stop_point_id:
                return vehicle_arrival
