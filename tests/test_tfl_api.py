from goto_london.tfl_api import TflApi


def test_filter_results_for_line_and_modality_modality_and_line_succeeds():
    _result_1 = {
        "modes": ["bus", "tube"],
        "lines": [{"name": "Line 1"}, {"name": "Line 2"}],
    }
    _result_2 = {
        "modes": ["train"],
        "lines": [{"name": "Train A"}, {"name": "Train B"}],
    }
    fake_results = {"results": [_result_1, _result_2]}
    filtered_fake_results = TflApi().filter_stop_points_for_modality_and_line(
        results=fake_results,
        child_key="results",
        modality_key="modes",
        line_key="lines",
        line="Line 1",
        modality="tube",
    )
    assert filtered_fake_results == [_result_1]


def test_filter_results_for_line_and_modality_just_modality_succeeds():
    _result_1 = {
        "modes": ["bus", "tube"],
        "lines": [{"name": "Line 1"}, {"name": "Line 2"}],
    }
    _result_2 = {
        "modes": ["train"],
        "lines": [{"name": "Train A"}, {"name": "Train B"}],
    }
    fake_results = {"results": [_result_1, _result_2]}
    filtered_fake_results = TflApi().filter_stop_points_for_modality_and_line(
        results=fake_results,
        child_key="results",
        modality_key="modes",
        check_line=False,
        modality="train",
    )
    assert filtered_fake_results == [_result_2]


class TestFilterVehicleArrivals:
    vehicle_1 = {
        "lineName": "mainLine",
        "naptanId": "A1",
        "vehicleId": 1,
        "expectedArrival": "2020-01-01 12:00:00Z",
    }
    vehicle_2 = {
        "lineName": "anotherLine",
        "naptanId": "A1",
        "vehicleId": 2,
        "expectedArrival": "2020-01-01 12:15:00Z",
    }
    vehicle_3 = {
        "lineName": "anotherLine",
        "naptanId": "B1",
        "vehicleId": 3,
        "expectedArrival": "2020-01-01 12:30:00Z",
    }
    vehicle_4 = {
        "lineName": "mainLine",
        "naptanId": "B1",
        "vehicleId": 4,
        "expectedArrival": "2020-01-01 13:00:00Z",
    }
    vehicle_arrivals = [
        vehicle_1,
        vehicle_2,
        vehicle_3,
        vehicle_4,
    ]

    def test_succeeds_for_stop_and_line(self):
        filtered_arrival = TflApi().get_destination_arrival_from_vehicle_arrivals(
            self.vehicle_arrivals, stop_point_id="B1", line="mainLine"
        )
        assert filtered_arrival == self.vehicle_4

    def test_succeeds_for_stop_only(self):
        filtered_arrival = TflApi().get_destination_arrival_from_vehicle_arrivals(
            self.vehicle_arrivals, stop_point_id="B1"
        )
        assert filtered_arrival == self.vehicle_3
