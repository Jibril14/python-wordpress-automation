# bot/config.py
import json
from pathlib import Path


def load_config(config_path: str) -> dict:
    """
    Load bot configuration from JSON file.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    required_keys = [
        "openai_api_key",
        "wordpress_url",
        "wordpress_username",
        "wordpress_app_password"
    ]

    for key in required_keys:
        if key not in config or not config[key]:
            raise ValueError(f"Missing required config key: {key}")

    return config
