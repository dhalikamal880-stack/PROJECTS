"""Wi-Fi and internet connectivity detection."""

import subprocess
import urllib.request

from urllib.error import URLError, HTTPError


NCSI_URL = "http://www.msftconnecttest.com/connecttest.txt"
NCSI_EXPECTED = "Microsoft Connect Test"


def get_wifi_status():
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=8,
            creationflags=getattr(
                subprocess,
                "CREATE_NO_WINDOW",
                0,
            ),
        )

        state = None
        ssid = None

        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()

            if line.lower().startswith("state") and ":" in line:
                state = line.split(":", 1)[1].strip().lower()

            elif (
                line.lower().startswith("ssid")
                and not line.lower().startswith("bssid")
                and ":" in line
            ):
                ssid = line.split(":", 1)[1].strip()

        if state == "connected" and ssid:
            return True, ssid

        if state is not None:
            return False, None

        return None, None

    except (OSError, subprocess.SubprocessError) as error:
        print("Wi-Fi detection failed:", error)
        return None, None


def has_internet(timeout=5):
    request = urllib.request.Request(
        NCSI_URL,
        headers={
            "User-Agent": "WiFiConnector/1.0"
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:

            final_url = response.geturl().lower()

            body = response.read(256).decode(
                "utf-8",
                errors="ignore",
            ).strip()

            return (
                final_url.startswith(NCSI_URL)
                and body == NCSI_EXPECTED
            )

    except (
        URLError,
        HTTPError,
        TimeoutError,
        OSError,
    ):
        return False