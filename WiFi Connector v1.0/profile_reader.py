"""Read saved Wi-Fi profiles."""

import json

from app_config import PROFILE_FILE


def load_profiles():
    try:
        data = json.loads(
            PROFILE_FILE.read_text(encoding="utf-8")
        )

        return data if isinstance(data, list) else []

    except FileNotFoundError:
        return []

    except (OSError, json.JSONDecodeError) as error:
        print("Could not read Wi-Fi profiles:", error)
        return []