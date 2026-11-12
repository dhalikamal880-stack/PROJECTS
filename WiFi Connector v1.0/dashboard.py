"""Modern compact dashboard with light/dark theme selection."""
import tkinter as tk
from tkinter import ttk
from app_config import load_settings, save_settings
from network import get_wifi_status, has_internet


class Dashboard:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.settings = load_settings()
        self.root.title("WiFi Connector")
        self.root.geometry("760x520")
        self.root.minsize(680, 470)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)
        self.apply_theme()
        self.build()
        self.refresh()

    def apply_theme(self):
        self.dark = self.settings.get("theme", "system") == "dark"
        self.bg = "#151923" if self.dark else "#F3F6FB"
        self.panel = "#222A38" if self.dark else "#FFFFFF"
        self.fg = "#F4F7FC" if self.dark else "#172033"
        self.muted = "#AAB5C5" if self.dark else "#64748B"
        self.accent = "#4F8CFF"
        self.root.configure(bg=self.bg)

    def build(self):
        self.root.configure(bg=self.bg)
        header = tk.Frame(self.root, bg=self.bg)
        header.pack(fill="x", padx=28, pady=(22, 12))
        tk.Label(header, text="WiFi Connector", bg=self.bg, fg=self.fg,
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        self.power_var = tk.BooleanVar(value=self.controller.enabled)
        self.power_button = tk.Button(header, text="", command=self.toggle_power,
            font=("Segoe UI", 11, "bold"), relief="flat", padx=18, pady=9,
            cursor="hand2")
        self.power_button.pack(side="right")

        self.status_card = tk.Frame(self.root, bg=self.panel, padx=22, pady=20)
        self.status_card.pack(fill="x", padx=28, pady=10)
        tk.Label(self.status_card, text="NETWORK STATUS", bg=self.panel, fg=self.muted,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.wifi_label = tk.Label(self.status_card, text="Checking Wi-Fi…", bg=self.panel,
                                   fg=self.fg, font=("Segoe UI", 18, "bold"))
        self.wifi_label.pack(anchor="w", pady=(8, 3))
        self.internet_label = tk.Label(self.status_card, text="Internet: checking…", bg=self.panel,
                                       fg=self.muted, font=("Segoe UI", 11))
        self.internet_label.pack(anchor="w")

        grid = tk.Frame(self.root, bg=self.bg)
        grid.pack(fill="both", expand=True, padx=28, pady=12)
        self.make_tile(grid, "Wi-Fi Profiles", "Manage saved networks and portal URLs", self.open_profiles, 0, 0)
        self.make_tile(grid, "Retry Login", "Try the saved portal credentials", self.controller.retry_login, 0, 1)
        self.make_tile(grid, "Appearance", "Switch between light and dark mode", self.toggle_theme, 1, 0)
        self.make_tile(grid, "Open Portal", "Open the saved portal manually", self.controller.open_portal, 1, 1)
        footer = tk.Frame(self.root, bg=self.bg)
        footer.pack(fill="x", padx=28, pady=(0, 18))
        tk.Label(footer, text="Runs quietly in the Windows system tray", bg=self.bg,
                 fg=self.muted, font=("Segoe UI", 9)).pack(side="left")
        tk.Button(footer, text="Exit application", command=self.controller.exit_app,
                  relief="flat", bg=self.bg, fg=self.muted, cursor="hand2").pack(side="right")
        self.update_power_button()

    def make_tile(self, parent, title, description, command, row, column):
        tile = tk.Frame(parent, bg=self.panel, padx=18, pady=16, cursor="hand2")
        tile.grid(row=row, column=column, sticky="nsew", padx=7, pady=7)
        tk.Label(tile, text=title, bg=self.panel, fg=self.fg,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(tile, text=description, bg=self.panel, fg=self.muted,
                 font=("Segoe UI", 9), wraplength=250, justify="left").pack(anchor="w", pady=(6, 0))
        tile.bind("<Button-1>", lambda _e: command())
        for child in tile.winfo_children():
            child.bind("<Button-1>", lambda _e: command())
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

    def update_power_button(self):
        if self.controller.enabled:
            self.power_button.configure(text="●  POWER ON", bg="#DDF7E8", fg="#137A43", activebackground="#C7F0D8")
        else:
            self.power_button.configure(text="○  POWER OFF", bg="#FCE4E4", fg="#A52A2A", activebackground="#F8D0D0")

    def toggle_power(self):
        self.controller.set_enabled(not self.controller.enabled)
        self.update_power_button()

    def toggle_theme(self):
        self.settings["theme"] = "light" if self.settings.get("theme") == "dark" else "dark"
        save_settings(self.settings)
        self.root.destroy()
        self.controller.open_dashboard()

    def open_profiles(self):
        self.controller.open_profiles()

    def refresh(self):
        connected, ssid = get_wifi_status()
        if connected:
            self.wifi_label.configure(text=ssid)
            self.internet_label.configure(text="Internet: Connected" if has_internet() else "Internet: Sign-in may be required")
        elif connected is False:
            self.wifi_label.configure(text="Wi-Fi disconnected")
            self.internet_label.configure(text="Internet: unavailable")
        else:
            self.wifi_label.configure(text="Unable to detect Wi-Fi")
            self.internet_label.configure(text="Internet: unknown")
        self.root.after(10000, self.refresh)

    def hide(self):
        self.root.withdraw()
