WIFI CONNECTOR - SOURCE PROJECT
===============================

FILES
-----
main.py             Application entry point.
wifi_tray.py        System tray, Power ON/OFF, background monitoring.
dashboard.py        Modern dashboard with Light/Dark appearance.
profile_manager.py  Saved Wi-Fi profile editor (compatible with existing profiles).
profile_reader.py   Loads saved profiles.
network.py          Windows Wi-Fi and internet connectivity checks.
portal_login.py     Best-effort portal login using a visible Chromium browser.
app_config.py       Shared settings and application data paths.
requirements.txt    Python dependencies.

RUN ON WINDOWS
--------------
1. Install Python 3.10 or newer.
2. Open PowerShell in this folder.
3. Run:
   python -m pip install -r requirements.txt
   python -m playwright install chromium
4. Run:
   python main.py

IMPORTANT BEHAVIOUR
-------------------
- The tray app checks internet connectivity before attempting portal login.
- When internet is already working, it does not open a portal or start login.
- Power OFF stops automatic monitoring and automatic login but leaves the tray app running.
- Existing profile data is kept in %APPDATA%\WiFiConnector\profiles.json.
- Passwords remain in Windows Credential Manager via keyring.
- Existing profile_manager.py data format (id, ssid, auth_type, username, portal_urls,
  legacy portal_url) is retained.

IMPORTANT LIMITATIONS
--------------------
- Windows controls its own captive-portal mini sign-in window. A third-party Python app
  cannot reliably force that exact Microsoft window to appear. Windows may show it
  automatically when its network detection identifies a captive portal.
- The provided login automation uses a visible Chromium window, not the Windows
  captive-portal mini window. College portal HTML differs, so the generic form selectors
  may need adjustment after testing the actual portal. Never share your password.
- This source is a development build, not yet a signed production release.
- Automatic update delivery is not included yet; it requires a release host, signed
  update packages, and a separate updater. Do not deploy unsigned updates to students.
- Windows startup registration and installer packaging are the next project stage.
