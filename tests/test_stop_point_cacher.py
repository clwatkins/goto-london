import pytest
import yaml

from goto_london.stop_point_cacher import (
    _build_unique_stop_line_pairs,
    _load_cache,
    _write_cache,
    CacheException,
    config_iterator,
    StopLinePair,
    StopPointsInfo,
    TflModalitiesType,
)


def test_assemble_unique_stops_from_config_succeeds():
    with open("tests/fake_config.yaml", "r") as file:
        test_config = yaml.safe_load(file)

    unique_stops = _build_unique_stop_line_pairs(config_iterator(test_config))
    assert unique_stops["bus"] == {
        StopLinePair(from_stop="73053", to_stop="76007", line="390")
    }
    assert unique_stops["tube"] == {
        StopLinePair(from_stop="Kentish Town", to_stop="Kings Cross", line="Northern")
    }


def test_write_cache_to_disk_succeeds(tmp_path):
    fake_cache: dict[TflModalitiesType, dict[str, StopPointsInfo]] = {
        "bus": {"1 - 2 - inbound": StopPointsInfo("B1", "B2", "1", "inbound")},
        "tube": {
            "KNT - KGX - inbound": StopPointsInfo("T1", "T2", "Northern", "inbound")
        },
    }
    fake_cache_hash = "abc123"

    test_cache_path = tmp_path / "test_stop_points.cache"

    _write_cache(fake_cache, fake_cache_hash, test_cache_path)

    cache = _load_cache(fake_cache_hash, test_cache_path)
    assert cache == fake_cache

    # Check that we won't load an out-of-date cache based on hash
    with pytest.raises(CacheException):
        _load_cache("bad_hash", test_cache_path)

    # And check we raise if file not found
    with pytest.raises(FileNotFoundError):
        _load_cache(fake_cache_hash, tmp_path / "bad_cache_path.cache")
