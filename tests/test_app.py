import arrow

from goto_london.app import _string_for_option
from goto_london.destination_ranker import (
    CalculatedDestinationModalityOption,
    ModalityOption,
    RankedDestinationOptions,
)


def test_string_for_option_walking(mocker):
    now = arrow.Arrow(year=2022, month=1, day=1, hour=12, minute=00)
    mocker.patch("goto_london.app.get_local_timestamp", return_value=now)

    walking_time_mins = 25

    walking_option = RankedDestinationOptions(
        destination="somewhere",
        final_arrival_time=now.shift(minutes=walking_time_mins),
        modality="walk",
        applied_bonus=0,
        rank=0,
        id=0,
        details=CalculatedDestinationModalityOption(
            destination="somewhere",
            vehicle_id=None,
            departure_time=now,
            arrival_time=now.shift(minutes=walking_time_mins),
            modality_option=ModalityOption(
                modality="walk",
                from_stop=None,
                to_stop=None,
                line=None,
                time_from=walking_time_mins,
                time_to=None,
            ),
        ),
    )

    assert (
        _string_for_option(walking_option)
        == "WALKING || Arriving by 12:25 (in 25 mins) --> (walk 25m)"
    )


def test_string_for_option_tube_bus(mocker):
    now = arrow.Arrow(year=2022, month=1, day=1, hour=12, minute=00)
    mocker.patch("goto_london.app.get_local_timestamp", return_value=now)

    bus_leaves_at = now.shift(minutes=10)
    bus_travel_time_mins = 10
    time_to_departing_stop_mins = 5
    time_from_arriving_stop_mins = 10

    bus_option = RankedDestinationOptions(
        destination="somewhere",
        final_arrival_time=bus_leaves_at.shift(
            minutes=bus_travel_time_mins + time_from_arriving_stop_mins
        ),
        modality="bus",
        applied_bonus=0,
        rank=0,
        id=0,
        details=CalculatedDestinationModalityOption(
            destination="somewhere",
            vehicle_id="A1",
            departure_time=bus_leaves_at,
            arrival_time=bus_leaves_at.shift(minutes=bus_travel_time_mins),
            modality_option=ModalityOption(
                modality="walk",
                from_stop="Departing Stop",
                to_stop="Destination Stop",
                line="1",
                time_from=time_to_departing_stop_mins,
                time_to=time_from_arriving_stop_mins,
            ),
        ),
    )

    assert (
        _string_for_option(bus_option)
        == "The BUS || Arriving @ Destination Stop by 12:30 (in 30 mins) "
        "// (walk to stop 5m) --> (wait for vehicle A1 @ Departing Stop for 5m)"
        " --> (arrive @ Destination Stop after 10m) --> (walk to destination 10m)"
    )
