"""Compact Wi-Fi profile editor for WiFi Connector."""

import json
import uuid
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import urlparse

import keyring

from app_config import (
    APP_DIR,
    PROFILE_FILE,
    SERVICE_NAME,
    MAX_PROFILES,
    DEFAULT_PORTAL_URL,
    load_settings,
    save_settings,
)


class WiFiProfileManager:

    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.dark = self.settings.get("theme", "light") == "dark"
        self.selected_id = None
        self.portal_url_entries = []
        self.profiles = self.load_profiles()

        APP_DIR.mkdir(parents=True, exist_ok=True)

        self.root.title("WiFi Connector - Wi-Fi Profiles")
        self.root.geometry("720x590")
        self.root.minsize(660, 540)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

        self.configure_style()
        self.build_interface()
        self.refresh_list()
        self.update_auth_fields()
        self.update_theme_button()

    def colors(self):
        if self.dark:
            return {
                "bg": "#171B24",
                "panel": "#222936",
                "field": "#171D28",
                "fg": "#F1F5F9",
                "muted": "#A4AFBF",
                "accent": "#6C9EFF",
                "border": "#354052",
                "select": "#30466A",
                "danger": "#E58B8B",
            }

        return {
            "bg": "#F3F5F8",
            "panel": "#FFFFFF",
            "field": "#F8FAFC",
            "fg": "#182230",
            "muted": "#64748B",
            "accent": "#2867D9",
            "border": "#DCE2EA",
            "select": "#DCE9FF",
            "danger": "#B93838",
        }

    def configure_style(self):
        c = self.colors()

        self.root.configure(bg=c["bg"])

        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure(
            "TFrame",
            background=c["bg"],
        )

        style.configure(
            "Card.TFrame",
            background=c["panel"],
        )

        style.configure(
            "TLabel",
            background=c["bg"],
            foreground=c["fg"],
            font=("Segoe UI", 9),
        )

        style.configure(
            "Muted.TLabel",
            background=c["bg"],
            foreground=c["muted"],
            font=("Segoe UI", 9),
        )

        style.configure(
            "Card.TLabel",
            background=c["panel"],
            foreground=c["fg"],
            font=("Segoe UI", 9),
        )

        style.configure(
            "Heading.TLabel",
            background=c["bg"],
            foreground=c["fg"],
            font=("Segoe UI", 17, "bold"),
        )

        style.configure(
            "Sub.TLabel",
            background=c["bg"],
            foreground=c["muted"],
            font=("Segoe UI", 9),
        )

        style.configure(
            "TLabelframe",
            background=c["panel"],
            foreground=c["fg"],
            bordercolor=c["border"],
            padding=9,
        )

        style.configure(
            "TLabelframe.Label",
            background=c["panel"],
            foreground=c["muted"],
            font=("Segoe UI", 9, "bold"),
        )

        style.configure(
            "TEntry",
            fieldbackground=c["field"],
            foreground=c["fg"],
            insertcolor=c["fg"],
            bordercolor=c["border"],
            padding=7,
        )

        style.configure(
            "TCombobox",
            fieldbackground=c["field"],
            foreground=c["fg"],
            padding=6,
        )

        style.map(
            "TCombobox",
            fieldbackground=[("readonly", c["field"])],
            foreground=[("readonly", c["fg"])],
        )

        style.configure(
            "TButton",
            font=("Segoe UI", 9),
            padding=(10, 7),
            background=c["panel"],
            foreground=c["fg"],
            bordercolor=c["border"],
        )

        style.map(
            "TButton",
            background=[("active", c["select"])],
        )

        style.configure(
            "Accent.TButton",
            background=c["accent"],
            foreground="#FFFFFF",
            bordercolor=c["accent"],
            font=("Segoe UI", 9, "bold"),
        )

        style.map(
            "Accent.TButton",
            background=[("active", c["accent"])],
            foreground=[("active", "#FFFFFF")],
        )

    def build_interface(self):
        c = self.colors()

        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=20, pady=(16, 12))

        title_area = ttk.Frame(header)
        title_area.pack(side="left", fill="x", expand=True)

        ttk.Label(
            title_area,
            text="Wi-Fi Profiles",
            style="Heading.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            title_area,
            text="Manage saved networks and captive portal details",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        self.theme_button = ttk.Button(
            header,
            text="Dark mode",
            command=self.toggle_theme,
        )
        self.theme_button.pack(side="right", anchor="center")

        body = ttk.Frame(self.root)
        body.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 12),
        )

        body.columnconfigure(0, weight=0, minsize=205)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = ttk.LabelFrame(
            body,
            text="SAVED NETWORKS",
            padding=10,
        )

        left.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 12),
        )

        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self.profile_list = tk.Listbox(
            left,
            width=24,
            height=16,
            font=("Segoe UI", 9),
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=c["border"],
            highlightcolor=c["accent"],
            bg=c["field"],
            fg=c["fg"],
            selectbackground=c["select"],
            selectforeground=c["fg"],
            activestyle="none",
            exportselection=False,
        )

        self.profile_list.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="nsew",
        )

        self.profile_list.bind(
            "<<ListboxSelect>>",
            self.select_profile,
        )

        self.count_label = ttk.Label(
            left,
            text="0 / 5 profiles",
            style="Muted.TLabel",
        )

        self.count_label.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(9, 0),
        )

        ttk.Button(
            left,
            text="Delete selected",
            command=self.delete_profile,
        ).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(12, 0),
        )

        right = ttk.LabelFrame(
            body,
            text="NETWORK DETAILS",
            padding=13,
        )

        right.grid(
            row=0,
            column=1,
            sticky="nsew",
        )

        right.columnconfigure(0, weight=1)

        ttk.Label(
            right,
            text="Wi-Fi network name (SSID)",
            style="Card.TLabel",
        ).grid(row=0, column=0, sticky="w")

        self.ssid_entry = ttk.Entry(right)
        self.ssid_entry.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(4, 10),
        )

        ttk.Label(
            right,
            text="Authentication type",
            style="Card.TLabel",
        ).grid(row=2, column=0, sticky="w")

        self.auth_type = tk.StringVar(
            value="Captive Portal"
        )

        self.auth_combo = ttk.Combobox(
            right,
            textvariable=self.auth_type,
            values=["Captive Portal", "Wi-Fi Password"],
            state="readonly",
        )

        self.auth_combo.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(4, 10),
        )

        self.auth_combo.bind(
            "<<ComboboxSelected>>",
            lambda _event: self.update_auth_fields(),
        )

        self.username_label = ttk.Label(
            right,
            text="Portal username",
            style="Card.TLabel",
        )

        self.username_entry = ttk.Entry(right)

        self.password_label = ttk.Label(
            right,
            text="Password",
            style="Card.TLabel",
        )

        self.password_entry = ttk.Entry(
            right,
            show="●",
        )

        self.portal_section = ttk.LabelFrame(
            right,
            text="CAPTIVE PORTAL URLS",
            padding=8,
        )

        self.portal_section.columnconfigure(0, weight=1)

        self.portal_url_frame = ttk.Frame(
            self.portal_section
        )

        self.portal_url_frame.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        self.add_url_button = ttk.Button(
            self.portal_section,
            text="+ Add another URL",
            command=self.add_portal_url,
        )

        self.add_url_button.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(7, 0),
        )

        self.save_button = ttk.Button(
            right,
            text="Save profile",
            style="Accent.TButton",
            command=self.save_profile,
        )

        self.save_button.grid(
            row=8,
            column=0,
            sticky="ew",
            pady=(12, 5),
        )

        self.clear_button = ttk.Button(
            right,
            text="+ New profile / Clear",
            command=self.clear_form,
        )

        self.clear_button.grid(
            row=9,
            column=0,
            sticky="ew",
        )

        self.note_label = ttk.Label(
            right,
            text="Passwords are stored in Windows Credential Manager.",
            style="Muted.TLabel",
            wraplength=390,
        )

        self.note_label.grid(
            row=10,
            column=0,
            sticky="w",
            pady=(10, 0),
        )

        self.add_portal_url(DEFAULT_PORTAL_URL)

        footer = ttk.Frame(self.root)
        footer.pack(
            fill="x",
            padx=20,
            pady=(0, 13),
        )

        ttk.Label(
            footer,
            text="Up to 5 saved networks · Changes are saved on this PC",
            style="Muted.TLabel",
        ).pack(side="left")

        ttk.Button(
            footer,
            text="Close",
            command=self.root.destroy,
        ).pack(side="right")

    def load_profiles(self):
        if not PROFILE_FILE.exists():
            return []

        try:
            data = json.loads(
                PROFILE_FILE.read_text(encoding="utf-8")
            )

            return data[:MAX_PROFILES] if isinstance(data, list) else []

        except (OSError, json.JSONDecodeError):
            messagebox.showerror(
                "Profile error",
                "Could not read saved profiles. Your existing file has not been overwritten.",
            )
            return []

    def save_profiles(self):
        APP_DIR.mkdir(parents=True, exist_ok=True)

        temp = PROFILE_FILE.with_suffix(".tmp")

        temp.write_text(
            json.dumps(self.profiles, indent=4),
            encoding="utf-8",
        )

        temp.replace(PROFILE_FILE)

    def add_portal_url(self, value=""):
        row = ttk.Frame(self.portal_url_frame)
        row.pack(fill="x", pady=3)

        entry = ttk.Entry(row)
        entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 6),
        )

        if value:
            entry.insert(0, value)

        ttk.Button(
            row,
            text="Remove",
            command=lambda: self.remove_portal_url(row),
            width=8,
        ).pack(side="right")

        self.portal_url_entries.append((row, entry))

    def remove_portal_url(self, row):
        self.portal_url_entries = [
            (r, e)
            for r, e in self.portal_url_entries
            if r != row
        ]

        row.destroy()

    def get_portal_urls(self):
        return [
            entry.get().strip()
            for _row, entry in self.portal_url_entries
            if entry.get().strip()
        ]

    def set_portal_urls(self, urls):
        for row, _entry in self.portal_url_entries:
            row.destroy()

        self.portal_url_entries.clear()

        for url in (urls or [DEFAULT_PORTAL_URL]):
            self.add_portal_url(url)

    def update_auth_fields(self):
        for widget in (
            self.username_label,
            self.username_entry,
            self.password_label,
            self.password_entry,
            self.portal_section,
        ):
            widget.grid_forget()

        row = 4

        if self.auth_type.get() == "Captive Portal":
            self.username_label.grid(
                row=row,
                column=0,
                sticky="w",
            )

            self.username_entry.grid(
                row=row + 1,
                column=0,
                sticky="ew",
                pady=(4, 9),
            )

            self.portal_section.grid(
                row=row + 2,
                column=0,
                sticky="ew",
                pady=(2, 4),
            )

            row += 3

        self.password_label.grid(
            row=row,
            column=0,
            sticky="w",
        )

        self.password_entry.grid(
            row=row + 1,
            column=0,
            sticky="ew",
            pady=(4, 8),
        )

        self.save_button.grid_configure(row=row + 2)
        self.clear_button.grid_configure(row=row + 3)
        self.note_label.grid_configure(row=row + 4)

    def refresh_list(self):
        self.profile_list.delete(0, tk.END)

        for profile in self.profiles:
            self.profile_list.insert(
                tk.END,
                f"●  {profile.get('ssid', 'Unknown')}",
            )

        self.count_label.configure(
            text=f"{len(self.profiles)} / {MAX_PROFILES} profiles"
        )

    def select_profile(self, _event=None):
        selected = self.profile_list.curselection()

        if not selected:
            return

        profile = self.profiles[selected[0]]
        self.selected_id = profile["id"]

        self.ssid_entry.delete(0, tk.END)
        self.ssid_entry.insert(
            0,
            profile.get("ssid", ""),
        )

        self.auth_type.set(
            profile.get("auth_type", "Captive Portal")
        )

        self.username_entry.delete(0, tk.END)
        self.username_entry.insert(
            0,
            profile.get("username", ""),
        )

        self.password_entry.delete(0, tk.END)

        try:
            password = keyring.get_password(
                SERVICE_NAME,
                profile["id"],
            )
        except Exception:
            password = None

        if password:
            self.password_entry.insert(0, password)

        urls = profile.get("portal_urls") or [
            profile.get("portal_url") or DEFAULT_PORTAL_URL
        ]

        self.set_portal_urls(urls)
        self.update_auth_fields()

        self.save_button.configure(
            text="Save changes"
        )

    def validate_urls(self, urls):
        if not urls:
            messagebox.showwarning(
                "Missing portal URL",
                "Add at least one captive portal URL.",
            )
            return False

        for url in urls:
            parsed = urlparse(url)

            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                messagebox.showwarning(
                    "Invalid URL",
                    f"Enter a valid HTTP or HTTPS URL:\n{url}",
                )
                return False

        return True

    def save_profile(self):
        ssid = self.ssid_entry.get().strip()
        auth = self.auth_type.get()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not ssid:
            messagebox.showwarning(
                "Missing information",
                "Enter the Wi-Fi network name (SSID).",
            )
            return

        if not password:
            messagebox.showwarning(
                "Missing information",
                "Enter the password.",
            )
            return

        if auth == "Captive Portal" and not username:
            messagebox.showwarning(
                "Missing information",
                "Enter the portal username.",
            )
            return

        urls = (
            self.get_portal_urls()
            if auth == "Captive Portal"
            else []
        )

        if auth == "Captive Portal" and not self.validate_urls(urls):
            return

        for old in self.profiles:
            if (
                old.get("ssid", "").casefold() == ssid.casefold()
                and old.get("id") != self.selected_id
            ):
                messagebox.showwarning(
                    "Duplicate network",
                    "This SSID is already saved. Select it to edit its details.",
                )
                return

        if self.selected_id:
            profile_id = self.selected_id

        else:
            if len(self.profiles) >= MAX_PROFILES:
                messagebox.showwarning(
                    "Profile limit",
                    f"You can save up to {MAX_PROFILES} networks.",
                )
                return

            profile_id = str(uuid.uuid4())

        profile = {
            "id": profile_id,
            "ssid": ssid,
            "auth_type": auth,
            "username": username if auth == "Captive Portal" else "",
        }

        if auth == "Captive Portal":
            profile["portal_urls"] = urls
            profile["portal_url"] = urls[0]

        try:
            keyring.set_password(
                SERVICE_NAME,
                profile_id,
                password,
            )

            if self.selected_id:
                for index, old in enumerate(self.profiles):
                    if old.get("id") == profile_id:
                        self.profiles[index] = profile
                        break

            else:
                self.profiles.append(profile)

            self.save_profiles()

        except Exception as error:
            messagebox.showerror(
                "Save error",
                f"Could not save this profile:\n{error}",
            )
            return

        self.refresh_list()
        self.clear_form()

        messagebox.showinfo(
            "Saved",
            f"{ssid} has been saved successfully.",
        )

    def delete_profile(self):
        selected = self.profile_list.curselection()

        if not selected:
            messagebox.showinfo(
                "Select a profile",
                "Choose a saved network first.",
            )
            return

        index = selected[0]
        profile = self.profiles[index]

        if not messagebox.askyesno(
            "Delete profile",
            f"Remove {profile.get('ssid', 'this network')} from WiFi Connector?",
        ):
            return

        try:
            try:
                keyring.delete_password(
                    SERVICE_NAME,
                    profile["id"],
                )
            except keyring.errors.PasswordDeleteError:
                pass

            del self.profiles[index]
            self.save_profiles()

        except Exception as error:
            messagebox.showerror(
                "Delete error",
                f"Could not delete the profile:\n{error}",
            )
            return

        self.refresh_list()
        self.clear_form()

    def clear_form(self):
        self.selected_id = None

        self.ssid_entry.delete(0, tk.END)
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

        self.auth_type.set("Captive Portal")

        self.set_portal_urls([DEFAULT_PORTAL_URL])
        self.update_auth_fields()

        self.save_button.configure(
            text="Add Wi-Fi profile"
        )

        self.profile_list.selection_clear(0, tk.END)

    def toggle_theme(self):
        self.dark = not self.dark

        self.settings["theme"] = (
            "dark" if self.dark else "light"
        )

        save_settings(self.settings)

        for widget in self.root.winfo_children():
            widget.destroy()

        self.configure_style()
        self.portal_url_entries.clear()
        self.build_interface()
        self.refresh_list()
        self.update_auth_fields()
        self.update_theme_button()

    def update_theme_button(self):
        self.theme_button.configure(
            text="☀ Light mode" if self.dark else "☾ Dark mode"
        )


def main():
    root = tk.Tk()
    app = WiFiProfileManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()