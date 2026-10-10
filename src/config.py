from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/config.yaml"


def validate_config(config):
    required_keys = {
        "project": ["name"],
        "paths": ["raw_data", "processed_data"],
        "data": ["answers", "reviews", "country"],
    }

    for section, keys in required_keys.items():
        if section not in config:
            raise ValueError(f"Missing configuration section: '{section}'")

        for key in keys:
            if key not in config[section]:
                raise ValueError(f"Missing configuration key: '{section}.{key}'")
            if config[section][key] is None:
                raise ValueError(
                    f"Configuration value '{section}.{key}' cannot be null"
                )
            if isinstance(config[section][key], str):  # noqa: SIM102
                if not config[section][key].strip():
                    raise ValueError(
                        f"Configuration value '{section}.{key}' cannot be empty"
                    )


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    with open(CONFIG_PATH, encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict) or not config:
        raise ValueError(f"Configuration file is empty or invalid: {CONFIG_PATH}")

    return config
