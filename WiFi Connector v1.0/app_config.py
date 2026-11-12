"""Shared application paths and settings."""

import json
from pathlib import Path

APP_NAME = "WiFiConnector"

APP_DIR = Path.home() / "AppData" / "Roaming" / APP_NAME

PROFILE_FILE = APP_DIR / "profiles.json"
SETTINGS_FILE = APP_DIR / "settings.json"

SERVICE_NAME = APP_NAME

DEFAULT_PORTAL_URL = "http://192.168.80.1"

MAX_PROFILES = 5
CHECK_INTERVAL_SECONDS = 15

APP_DIR.mkdir(parents=True, exist_ok=True)


def load_settings():
    defaults = {
        "enabled": True,
        "theme": "system",
        "start_with_windows": True,
    }

    try:
        data = json.loads(
            SETTINGS_FILE.read_text(encoding="utf-8")
        )

        if isinstance(data, dict):
            defaults.update(data)

    except (OSError, json.JSONDecodeError):
        pass

    return defaults


def save_settings(settings):
    temporary = SETTINGS_FILE.with_suffix(".tmp")

    temporary.write_text(
        json.dumps(settings, indent=2),
        encoding="utf-8",
    )

    temporary.replace(SETTINGS_FILE)