from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/config.yaml"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as file:
        return yaml.safe_load(file)
