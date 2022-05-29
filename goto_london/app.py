from flask import Flask, render_template

from .common import config_iterator, get_config, get_local_timestamp
from .destination_ranker import rank_options_for_destination, RankedDestinationOptions


app = Flask(__name__)

_TFL_OPTION_TEMPLATE_STR = (
    "The {modality} || Arriving @ {to_station} by {arrival_time} (in {arrival_mins} mins) "
    "// (walk to stop {time_from_mins}m) --> (wait for vehicle {vehicle} @ {from_station} for {wait_departure_mins}m) "
    "--> (arrive @ {to_station} after {travel_time_mins}m) --> (walk to destination {time_to_mins}m)"
)
_WALKING_OPTION_TEMPLATE_STR = (
    "WALKING || Arriving by {arrival_time} (in {arrival_mins} mins) "
    "--> (walk {arrival_mins}m)"
)


def _string_for_option(option: RankedDestinationOptions) -> str:
    if option.modality == "walk":
        return _WALKING_OPTION_TEMPLATE_STR.format(
            modality=option.modality.upper(),
            arrival_time=option.details.arrival_time.format("HH:mm"),
            arrival_mins=int(
                (option.details.arrival_time - get_local_timestamp()).seconds / 60
            ),
        )
    else:
        return _TFL_OPTION_TEMPLATE_STR.format(
            modality=option.modality.upper(),
            vehicle=option.details.vehicle_id,
            from_station=option.details.modality_option.from_stop,
            to_station=option.details.modality_option.to_stop,
            time_from_mins=option.details.modality_option.time_from,
            time_to_mins=option.details.modality_option.time_to,
            wait_departure_mins=int(
                (
                    option.details.departure_time
                    - (
                        get_local_timestamp().shift(
                            minutes=option.details.modality_option.time_from
                        )
                    )
                ).seconds
                / 60
            ),
            travel_time_mins=int(
                (option.details.arrival_time - option.details.departure_time).seconds
                / 60
            ),
            arrival_time=option.final_arrival_time.format("HH:mm"),
            arrival_mins=int(
                (option.final_arrival_time - get_local_timestamp()).seconds / 60
            ),
        )


@app.route("/goto/<destination>")
def get_destination_options(destination: str):

    ranked_options = rank_options_for_destination(target_destination=destination)
    best_option = _string_for_option(ranked_options[0])
    other_options = [
        _string_for_option(ranked_option) for ranked_option in ranked_options[1:]
    ]

    return render_template(
        "transit_options.html", best_option=best_option, other_options=other_options
    )


@app.route("/goto")
def get_all_destinations():
    destinations = set()
    for destination, modality, modality_options in config_iterator(get_config()):
        destinations.update([destination])

    return "Destinations: " + ", ".join(destinations)


def main():
    app.run(debug=True)
