"""Wi-Fi, internet, and captive-portal detection."""

import subprocess
import urllib.request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse

NCSI_URL = "http://www.msftconnecttest.com/connecttest.txt"
NCSI_EXPECTED = "Microsoft Connect Test"

# These plain-HTTP connectivity checks are commonly redirected by captive
# portals. The redirect destination can reveal the portal's current URL.
PORTAL_PROBES = (
    "http://www.msftconnecttest.com/redirect",
    "http://connectivitycheck.gstatic.com/generate_204",
)


def get_wifi_status():
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
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
        headers={"User-Agent": "WiFiConnector/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            final_url = response.geturl().lower()
            body = response.read(256).decode("utf-8", errors="ignore").strip()
            return final_url.startswith(NCSI_URL) and body == NCSI_EXPECTED
    except (URLError, HTTPError, TimeoutError, OSError):
        return False


def discover_captive_portal_url(timeout=5):
    """Return a portal URL exposed by a captive-portal HTTP redirect.

    A portal may not expose a redirect to every probe. None means that
    automatic discovery did not find one; saved profile URLs can then be used
    as a fallback.
    """
    for probe_url in PORTAL_PROBES:
        try:
            request = urllib.request.Request(
                probe_url,
                headers={"User-Agent": "Mozilla/5.0 WiFiConnector/1.0"},
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                final_url = response.geturl()
                original = urlparse(probe_url)
                final = urlparse(final_url)

                if (
                    final.scheme in ("http", "https")
                    and final.netloc
                    and final.hostname != original.hostname
                ):
                    return final_url
        except (URLError, HTTPError, TimeoutError, OSError, ValueError):
            continue

    return None
