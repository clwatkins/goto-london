import yaml

from goto_london.common import config_iterator, ModalityOption


def test_config_iterator_succeeds():
    with open("tests/fake_config.yaml", "r") as file:
        test_config = yaml.safe_load(file)

    unpacked_config = list(config_iterator(test_config))
    assert len(unpacked_config) == 3  # 1 destination, 3 modalities

    assert unpacked_config[0] == (
        "kgx",
        "bus",
        ModalityOption(
            "bus",
            "73053",
            "76007",
            "390",
            2,
            5,
        ),
    )

    assert unpacked_config[1] == (
        "kgx",
        "tube",
        ModalityOption(
            "tube",
            "Kentish Town",
            "Kings Cross",
            "Northern",
            10,
            5,
        ),
    )

    assert unpacked_config[2] == (
        "kgx",
        "walk",
        ModalityOption(
            "walk",
            None,
            None,
            None,
            30,
            None,
        ),
    )
