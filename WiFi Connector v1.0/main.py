
"""WiFi Connector entry point."""

import sys


def main():
    if "--settings" in sys.argv:
        from profile_manager import main as open_settings
        open_settings()
    else:
        from wifi_tray import run_app
        run_app()


if __name__ == "__main__":
    main()
