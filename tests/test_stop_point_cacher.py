import yaml

from src.goto_london_sss.stop_point_cacher import _assemble_unique_stops_from_config

with open("tests/fake_config.yaml", "r") as file:
    TEST_CONFIG = yaml.safe_load(file)


def test_assemble_unique_stops_from_config_succeeds():
    unique_stops = _assemble_unique_stops_from_config(TEST_CONFIG)
    assert unique_stops['bus'] == {'73053', '76007'}
    assert unique_stops['tube'] == {'Kentish Town', 'Kings Cross'}
