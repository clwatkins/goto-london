# Calculate best routes using live TFL arrivals info.
from dataclasses import dataclass
from typing import Optional

import arrow

from .common import (
    config_iterator,
    get_config,
    get_local_timestamp,
    LOGGER,
    ModalityOption,
    AllModalitiesType,
)
from .stop_point_cacher import get_from_cache, load_or_generate_cache
from .tfl_api import TflApi


@dataclass
class CalculatedDestinationModalityOption:
    """Live vehicle-specific timings for a given ModalityOption."""

    destination: str
    modality_option: ModalityOption
    vehicle_id: Optional[str]
    departure_time: arrow.Arrow
    arrival_time: arrow.Arrow


@dataclass
class RankedDestinationOptions:
    """Overall ranked option based on vehicle timings and modality bonus."""

    destination: str
    modality: AllModalitiesType
    final_arrival_time: arrow.Arrow
    applied_bonus: int
    rank: int
    id: int
    details: CalculatedDestinationModalityOption


STOP_POINTS_CACHE = load_or_generate_cache()
CONFIG = get_config()


def _get_modality_timings_for_destination(
    target_destination: str,
) -> list[CalculatedDestinationModalityOption]:
    """Generate CalculatedDestinationModalityOptions for each destination modality in config."""
    api = TflApi()
    calculated_options: list[CalculatedDestinationModalityOption] = []

    for destination, modality, modality_option in config_iterator(CONFIG):
        # Skip non-target destination configs
        if destination != target_destination:
            continue

        # Cover non-TFL data calculated case
        if modality == "walk":
            # Assume we just leave now for any walking case
            now = get_local_timestamp()
            calculated_options.append(
                CalculatedDestinationModalityOption(
                    destination=destination,
                    modality_option=modality_option,
                    vehicle_id=None,
                    departure_time=now,
                    arrival_time=now.shift(minutes=modality_option.time_from),
                )
            )
            break

        # Look up the specific StopPoint IDs for the given ModalityOption
        # (needed for the TFL API)
        from_stop_point, to_stop_point, line, direction = get_from_cache(
            modality_option,
            cache=STOP_POINTS_CACHE,
        )
        next_vehicles = api.get_next_vehicles_for_line_stop_point(
            line=line, stop_point_id=from_stop_point, direction=direction
        )

        LOGGER.info("Found %d next vehicles", len(next_vehicles))

        next_vehicles = api.filter_vehicles_beyond_n_minutes_away(
            next_vehicles, modality_option.time_from
        )

        LOGGER.info(
            "Filtered that down to %d vehicles enough in future", len(next_vehicles)
        )

        for next_vehicle in next_vehicles:
            # Check that the vehicles departing our origin StopPoint will travel to our
            # destination (needed where a certain line might branch on the way)
            next_vehicle_arrivals = api.get_vehicle_arrivals(next_vehicle["vehicleId"])

            vehicle_destination_arrival = (
                api.get_destination_arrival_from_vehicle_arrivals(
                    next_vehicle_arrivals, stop_point_id=to_stop_point, line=line
                )
            )

            if not vehicle_destination_arrival:
                continue

            # As soon as we find a vehicle that we know will travel to destination
            # then we go with that option, as the vehicles are returned in order of arrival
            # time (and we've already filtered out those arriving too soon to get to the stop)
            calculated_options.append(
                CalculatedDestinationModalityOption(
                    destination=destination,
                    modality_option=modality_option,
                    vehicle_id=next_vehicle["vehicleId"],
                    # expectedArrival = when the next vehicle will arrive at origin stop
                    departure_time=get_local_timestamp(next_vehicle["expectedArrival"]),
                    arrival_time=get_local_timestamp(
                        # expectedArrival = when the vehicle will arrive at its destination stop
                        vehicle_destination_arrival["expectedArrival"]
                    ),
                )
            )
            break

    return calculated_options


def rank_options_for_destination(
    target_destination: str,
) -> list[RankedDestinationOptions]:
    """Generate ranked travel options for a target destination."""
    ranked_destination_options: dict[int, RankedDestinationOptions] = {}

    modality_timings = _get_modality_timings_for_destination(target_destination)
    adjusted_arrival_times: list[tuple[int, arrow.Arrow]] = []

    for m, modality_timing in enumerate(modality_timings):
        modality = modality_timing.modality_option.modality
        # Config describes time bonus in positive terms for so reverse the time shift
        bonus_minutes = -1 * CONFIG[f"{modality}_time_bonus"]

        # Add the final walking time from transit arrival to destination
        final_arrival_time = modality_timing.arrival_time.shift(
            minutes=modality_timing.modality_option.time_to or 0
        )

        ranked_destination_options[m] = RankedDestinationOptions(
            destination=target_destination,
            final_arrival_time=final_arrival_time,
            modality=modality,
            applied_bonus=bonus_minutes,
            # Placeholder rank to be over-writen once all options generated
            rank=-1,
            id=m,
            details=modality_timing,
        )

        adjusted_arrival_times.append(
            # Penalise/benefit mode based on config-level bonus minutes.
            # This list is just to facilitate final ranking of our options
            (m, final_arrival_time.shift(minutes=bonus_minutes))
        )

    # Sort list based on which option will get user there first,
    # taking into account all travel time + the modality bonus/penalty
    adjusted_arrival_times.sort(key=lambda item: item[1])

    # Update our RankedDestinationOptions based on this sorted list
    for rank, id_and_time in enumerate(adjusted_arrival_times):
        ranked_destination_options[id_and_time[0]].rank = rank

    ranked_destination_options_list = list(ranked_destination_options.values())
    # Ensure that the final results will arrive in rank-sorted order
    ranked_destination_options_list.sort(key=lambda option: option.rank)

    return ranked_destination_options_list


def main():
    destinations = set()
    for destination, modality, modality_options in config_iterator(CONFIG):
        destinations.update([destination])

    for destination in destinations:
        options = rank_options_for_destination(destination)
        print(options)
