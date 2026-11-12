"""Captive portal login automation."""

import time
import keyring

from app_config import SERVICE_NAME, DEFAULT_PORTAL_URL
from network import has_internet


def get_portal_urls(profile):
    urls = profile.get("portal_urls") or []

    if not urls and profile.get("portal_url"):
        urls = [profile["portal_url"]]

    if not urls:
        urls = [DEFAULT_PORTAL_URL]

    return [
        url.strip()
        for url in urls
        if isinstance(url, str) and url.strip()
    ]


def automatic_portal_login(profile):
    if has_internet():
        return True

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError(
            "Playwright is missing. Install it using the setup instructions."
        ) from error

    profile_id = profile.get("id", "")
    username = profile.get("username", "")

    password = keyring.get_password(
        SERVICE_NAME,
        profile_id,
    )

    if not username or not password:
        raise RuntimeError(
            "This profile has no saved username or password. Open Wi-Fi Profiles."
        )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            for url in get_portal_urls(profile):
                try:
                    page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=15000,
                    )

                    page.wait_for_timeout(1500)

                    if has_internet():
                        return True

                    text_inputs = page.locator(
                        'input:not([type]), '
                        'input[type="text"], '
                        'input[type="email"], '
                        'input[type="tel"]'
                    )

                    password_inputs = page.locator(
                        'input[type="password"]'
                    )

                    if text_inputs.count() and password_inputs.count():
                        text_inputs.first.fill(username)
                        password_inputs.first.fill(password)

                        buttons = page.locator(
                            'button, input[type="submit"]'
                        )

                        clicked = False

                        for index in range(buttons.count()):
                            button = buttons.nth(index)

                            label = (
                                button.inner_text()
                                or button.get_attribute("value")
                                or ""
                            ).strip().lower()

                            if any(
                                word in label
                                for word in (
                                    "agree",
                                    "continue",
                                    "login",
                                    "sign in",
                                    "submit",
                                )
                            ):
                                button.click(timeout=5000)
                                clicked = True
                                break

                        if not clicked:
                            page.keyboard.press("Enter")

                        page.wait_for_timeout(7000)

                        if has_internet():
                            return True

                except Exception as error:
                    print(
                        f"Portal attempt failed for {url}: {error}"
                    )

            return has_internet()

        finally:
            if has_internet():
                browser.close()
            else:
                # Leave the visible browser open so the user
                # can finish the login manually if necessary.
                time.sleep(2)