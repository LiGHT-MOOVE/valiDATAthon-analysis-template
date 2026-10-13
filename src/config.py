from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def validate_config(config):
    required_keys = {
        "project": ["name"],
        "paths": ["raw_data", "processed_data"],
        "data": ["countries"],
    }

    # Validate required sections and keys.
    for section, keys in required_keys.items():
        if section not in config:
            raise ValueError(f"Missing configuration section: '{section}'")

        for key in keys:
            if key not in config[section]:
                raise ValueError(f"Missing configuration key: '{section}.{key}'")

            value = config[section][key]

            if value is None:
                raise ValueError(
                    f"Configuration value '{section}.{key}' cannot be null"
                )

            if isinstance(value, str) and not value.strip():
                raise ValueError(
                    f"Configuration value '{section}.{key}' cannot be empty"
                )

    # Validate country configurations.
    countries = config["data"]["countries"]

    if not isinstance(countries, list) or not countries:
        raise ValueError(
            "Configuration value 'data.countries' must be a non-empty list"
        )

    country_names = []

    for index, country in enumerate(countries):
        if not isinstance(country, dict):
            raise ValueError(  # noqa: TRY004
                f"Country configuration at index {index} must be a dictionary"
            )

        for key in ["name", "answers", "reviews"]:
            if key not in country:
                raise ValueError(
                    f"Missing configuration key: 'data.countries[{index}].{key}'"
                )

            value = country[key]

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Configuration value "
                    f"'data.countries[{index}].{key}' "
                    f"must be a non-empty string"
                )

        country_name = country["name"].strip().lower()

        if country_name in country_names:
            raise ValueError(f"Duplicate country name: '{country['name']}'")

        country_names.append(country_name)


def load_config(config_path):
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path) as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict) or not config:
        raise ValueError(f"Configuration file is empty or invalid: {config_path}")

    return config


def get_country_config(config, country_name):
    countries = config["data"]["countries"]

    for country in countries:
        if country["name"].lower() == country_name.lower():
            return country

    available_countries = [country["name"] for country in countries]

    raise ValueError(
        f"Country '{country_name}' is not configured. "
        f"Available countries: {', '.join(available_countries)}"
    )
