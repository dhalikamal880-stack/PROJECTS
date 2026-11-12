
"""System tray controller and background Wi-Fi monitor."""

import subprocess
import sys
import threading
import webbrowser
import winreg
from pathlib import Path

import pystray
from PIL import Image, ImageDraw
from plyer import notification

from app_config import (
    load_settings,
    save_settings,
    CHECK_INTERVAL_SECONDS,
)

from profile_reader import load_profiles
from network import get_wifi_status, has_internet
from portal_login import automatic_portal_login, get_portal_urls


APP_DIR = Path(__file__).resolve().parent


class WiFiTrayApp:

    def __init__(self):
        self.settings = load_settings()
        self.enabled = bool(
            self.settings.get("enabled", True)
        )

        self.icon = None
        self.stop_event = threading.Event()
        self.last_network = None

        self.login_running = False
        self.login_lock = threading.Lock()

        self.login_attempted_for = set()

    @staticmethod
    def icon_image(color):
        image = Image.new(
            "RGBA",
            (64, 64),
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(image)

        draw.ellipse(
            (7, 7, 57, 57),
            fill=color,
        )

        draw.arc(
            (18, 17, 46, 43),
            200,
            340,
            fill="white",
            width=4,
        )

        draw.ellipse(
            (29, 37, 35, 43),
            fill="white",
        )

        return image

    @staticmethod
    def notify(title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="WiFi Connector",
                timeout=5,
            )

        except Exception as error:
            print("Notification error:", error)

    def refresh_icon(self, color=None):
        if self.icon:
            if color is None:
                color = (
                    (34, 170, 95)
                    if self.enabled
                    else (130, 130, 140)
                )

            self.icon.icon = self.icon_image(color)
            self.icon.update_menu()

    def matching_profile(self, ssid):
        for profile in load_profiles():
            if (
                profile.get("ssid", "").casefold()
                == ssid.casefold()
            ):
                return profile

        return None

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)

        self.settings["enabled"] = self.enabled
        save_settings(self.settings)

        if not self.enabled:
            self.notify(
                "WiFi Connector",
                "Automatic Wi-Fi monitoring is OFF.",
            )

            self.refresh_icon((130, 130, 140))

        else:
            self.notify(
                "WiFi Connector",
                "Automatic Wi-Fi monitoring is ON.",
            )

            self.last_network = None
            self.refresh_icon((34, 170, 95))

    def toggle_enabled(self, _icon=None, _item=None):
        self.set_enabled(not self.enabled)

    def menu_power_label(self, _item=None):
        return "Turn OFF" if self.enabled else "Turn ON"

    def menu_status(self, _item=None):
        connected, ssid = get_wifi_status()

        if connected:
            return f"Wi-Fi: {ssid}"

        if connected is False:
            return "Wi-Fi: Disconnected"

        return "Wi-Fi: Status unavailable"

    def open_profiles(self):
        try:
            if getattr(sys, "frozen", False):
                command = [sys.executable, "--settings"]
            else:
                command = [
                    sys.executable,
                    str(APP_DIR / "main.py"),
                    "--settings",
                ]

            subprocess.Popen(command, cwd=str(APP_DIR))

        except Exception as error:
            self.notify(
                "WiFi Connector",
                f"Could not open profile settings: {error}",
            )

    def open_portal(self, _icon=None, _item=None):
        connected, ssid = get_wifi_status()

        if not connected:
            self.notify(
                "WiFi Connector",
                "Connect to Wi-Fi first.",
            )
            return

        profile = self.matching_profile(ssid)

        if (
            not profile
            or profile.get("auth_type") != "Captive Portal"
        ):
            self.notify(
                "WiFi Connector",
                "No captive-portal profile exists for this network.",
            )
            return

        if has_internet():
            self.notify(
                "WiFi Connector",
                "Internet is already working. No portal was opened.",
            )
            return

        urls = get_portal_urls(profile)

        if urls:
            webbrowser.open(urls[0])

    def retry_login(self, _icon=None, _item=None):
        connected, ssid = get_wifi_status()

        if not connected:
            self.notify(
                "WiFi Connector",
                "Connect to Wi-Fi before retrying login.",
            )
            return

        if has_internet():
            self.notify(
                "WiFi Connector",
                "Internet is already working. No login is needed.",
            )
            return

        profile = self.matching_profile(ssid)

        if (
            not profile
            or profile.get("auth_type") != "Captive Portal"
        ):
            self.notify(
                "WiFi Connector",
                "No captive-portal profile exists for this network.",
            )
            return

        self.login_attempted_for.discard(ssid)
        self.start_login(profile, ssid)

    def start_login(self, profile, ssid):
        with self.login_lock:
            if self.login_running:
                return

            self.login_running = True

        def worker():
            try:
                if has_internet():
                    return

                self.notify(
                    "WiFi Connector",
                    f"Login may be required for {ssid}. Opening the portal workflow.",
                )

                success = automatic_portal_login(profile)

                if success:
                    self.notify(
                        "WiFi Connector",
                        f"Internet access confirmed for {ssid}.",
                    )

                else:
                    self.notify(
                        "WiFi Connector",
                        "Login was not confirmed. Finish in the portal window or use Retry Login.",
                    )

            except Exception as error:
                self.notify(
                    "WiFi Connector",
                    f"Automatic login error: {error}",
                )

            finally:
                with self.login_lock:
                    self.login_running = False

        threading.Thread(
            target=worker,
            daemon=True,
        ).start()

    def monitor(self):
        while not self.stop_event.is_set():

            if self.enabled:
                connected, ssid = get_wifi_status()

                if connected and ssid:

                    if ssid != self.last_network:
                        self.last_network = ssid

                        self.notify(
                            "WiFi Connector",
                            f"Connected to {ssid}.",
                        )

                        self.login_attempted_for.discard(ssid)

                    profile = self.matching_profile(ssid)

                    if (
                        profile
                        and profile.get("auth_type") == "Captive Portal"
                    ):

                        # Never launch the portal if internet works.
                        internet_available = has_internet()

                        if (
                            not internet_available
                            and ssid not in self.login_attempted_for
                        ):
                            self.login_attempted_for.add(ssid)

                            self.start_login(
                                profile,
                                ssid,
                            )

                        self.refresh_icon(
                            (34, 170, 95)
                            if internet_available
                            else (230, 165, 45)
                        )

                    else:
                        self.refresh_icon((50, 130, 220))

                elif connected is False:

                    if self.last_network is not None:
                        self.notify(
                            "WiFi Connector",
                            "Wi-Fi disconnected.",
                        )

                    self.last_network = None
                    self.refresh_icon((130, 130, 140))

            self.stop_event.wait(
                CHECK_INTERVAL_SECONDS
            )

    def exit_app(self, _icon=None, _item=None):
        self.stop_event.set()

        if self.icon:
            self.icon.stop()

    def configure_windows_startup(self):
        """Register the app to start for the current Windows user."""

        try:
            if getattr(sys, "frozen", False):
                command = f'"{sys.executable}"'

            else:
                command = (
                    f'"{sys.executable}" '
                    f'"{Path(__file__).with_name("main.py")}"'
                )

            key_path = (
                r"Software\Microsoft\Windows\CurrentVersion\Run"
            )

            with winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
            ) as key:

                if self.settings.get("start_with_windows", True):

                    winreg.SetValueEx(
                        key,
                        "WiFiConnector",
                        0,
                        winreg.REG_SZ,
                        command,
                    )

                else:
                    try:
                        winreg.DeleteValue(
                            key,
                            "WiFiConnector",
                        )

                    except FileNotFoundError:
                        pass

        except OSError as error:
            print(
                "Could not configure Windows startup:",
                error,
            )

    def run(self):
        self.configure_windows_startup()

        menu = pystray.Menu(
            pystray.MenuItem(
                self.menu_status,
                None,
                enabled=False,
            ),

            pystray.Menu.SEPARATOR,

            pystray.MenuItem(
                self.menu_power_label,
                self.toggle_enabled,
            ),

            pystray.MenuItem(
                "Wi-Fi Profiles / Settings",
                lambda _icon, _item: self.open_profiles(),
                default=True,
            ),

            pystray.MenuItem(
                "Open Captive Portal",
                self.open_portal,
            ),

            pystray.MenuItem(
                "Retry Login",
                self.retry_login,
            ),

            pystray.Menu.SEPARATOR,

            pystray.MenuItem(
                "Exit",
                self.exit_app,
            ),
        )

        self.icon = pystray.Icon(
            "WiFiConnector",
            self.icon_image((34, 170, 95)),
            "WiFi Connector",
            menu,
        )

        threading.Thread(
            target=self.monitor,
            daemon=True,
        ).start()

        self.icon.run()


def run_app():
    WiFiTrayApp().run()


if __name__ == "__main__":
    run_app()
