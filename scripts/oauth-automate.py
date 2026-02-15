#!/usr/bin/env python3
"""
oauth-automate.py — Headless Autodesk OAuth login automation via Playwright.

Accepts an Autodesk authorization URL and automates the login + consent flow
so that `raps auth login --default` can complete without manual interaction.

Usage:
    python oauth-automate.py <AUTH_URL> [--headed] [--timeout 60]

Environment variables:
    APS_USERNAME  — Autodesk account email
    APS_PASSWORD  — Autodesk account password
"""

import argparse
import os
import sys
import time

def main():
    parser = argparse.ArgumentParser(
        description="Automate Autodesk OAuth login via Playwright"
    )
    parser.add_argument("auth_url", help="Full authorization URL from raps auth login")
    parser.add_argument(
        "--headed", action="store_true", help="Run browser in headed mode for debugging"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Max seconds to wait for the flow to complete (default: 60)",
    )
    parser.add_argument(
        "--screenshot-dir",
        default=None,
        help="Directory to save failure screenshots (default: cwd)",
    )
    args = parser.parse_args()

    username = os.environ.get("APS_USERNAME")
    password = os.environ.get("APS_PASSWORD")
    if not username or not password:
        print("ERROR: APS_USERNAME and APS_PASSWORD must be set", file=sys.stderr)
        sys.exit(2)

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
    except ImportError:
        print(
            "ERROR: playwright not installed. Run: pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(2)

    screenshot_dir = args.screenshot_dir or os.getcwd()
    profile_dir = os.path.join(os.path.expanduser("~"), ".raps-oauth-profile")

    print(f"[oauth] Launching browser (headed={args.headed})")
    print(f"[oauth] Profile dir: {profile_dir}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            profile_dir,
            headless=not args.headed,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(args.timeout * 1000)

        try:
            print(f"[oauth] Navigating to auth URL...")
            page.goto(args.auth_url, wait_until="domcontentloaded")
            time.sleep(2)

            # Detect page state and act accordingly.
            # The Autodesk login flow can land on:
            #   1. Login page (email/password form)
            #   2. Consent/allow page
            #   3. Already redirected to localhost callback (session cached)

            if _is_callback_redirect(page):
                print("[oauth] Already redirected to callback (session cached)")
                _wait_for_callback(page, args.timeout)
                context.close()
                print("[oauth] SUCCESS")
                sys.exit(0)

            # --- Login form ---
            if _has_login_form(page):
                print(f"[oauth] Login form detected, entering credentials...")
                _fill_login(page, username, password)
                time.sleep(3)

            # --- Consent page ---
            if _has_consent_button(page):
                print("[oauth] Consent page detected, clicking Allow...")
                _click_consent(page)
                time.sleep(2)

            # --- Wait for redirect to localhost callback ---
            _wait_for_callback(page, args.timeout)
            context.close()
            print("[oauth] SUCCESS")
            sys.exit(0)

        except PwTimeout as e:
            _save_screenshot(page, screenshot_dir, "timeout")
            print(f"[oauth] TIMEOUT: {e}", file=sys.stderr)
            context.close()
            sys.exit(1)
        except Exception as e:
            _save_screenshot(page, screenshot_dir, "error")
            print(f"[oauth] ERROR: {e}", file=sys.stderr)
            context.close()
            sys.exit(1)


def _is_callback_redirect(page):
    """Check if the page already redirected to the localhost callback."""
    return "localhost" in page.url and "/callback" in page.url


def _has_login_form(page):
    """Detect whether an Autodesk login form is present."""
    # Multiple selectors for resilience against page updates
    selectors = [
        'input[name="userName"]',
        'input[type="email"]',
        'input#userName',
        '#user_email',
    ]
    for sel in selectors:
        if page.query_selector(sel):
            return True
    return False


def _fill_login(page, username, password):
    """Fill email, click Next, fill password, submit."""
    # --- Email step ---
    email_selectors = [
        'input[name="userName"]',
        'input[type="email"]',
        'input#userName',
        '#user_email',
    ]
    email_field = None
    for sel in email_selectors:
        email_field = page.query_selector(sel)
        if email_field:
            break
    if not email_field:
        raise RuntimeError("Could not find email input field")

    email_field.fill(username)
    time.sleep(0.5)

    # Click Next / Continue button
    next_selectors = [
        'button[id="verify_user_btn"]',
        'button:has-text("Next")',
        'button:has-text("Continue")',
        'input[type="submit"]',
        '#btnSubmit',
    ]
    for sel in next_selectors:
        btn = page.query_selector(sel)
        if btn and btn.is_visible():
            btn.click()
            break
    time.sleep(2)

    # --- Password step ---
    pwd_selectors = [
        'input[name="password"]',
        'input[type="password"]',
        'input#password',
    ]
    pwd_field = None
    for sel in pwd_selectors:
        pwd_field = page.query_selector(sel)
        if pwd_field:
            break
    if not pwd_field:
        raise RuntimeError("Could not find password input field")

    pwd_field.fill(password)
    time.sleep(0.5)

    # Submit
    submit_selectors = [
        'button[id="btnSubmit"]',
        'button[type="submit"]',
        'button:has-text("Sign in")',
        'button:has-text("Log in")',
        'input[type="submit"]',
    ]
    for sel in submit_selectors:
        btn = page.query_selector(sel)
        if btn and btn.is_visible():
            btn.click()
            break


def _has_consent_button(page):
    """Detect whether an OAuth consent/allow page is showing."""
    selectors = [
        'button:has-text("Allow")',
        'button:has-text("Accept")',
        'button:has-text("Authorize")',
        'input[value="Allow"]',
        '#allow_btn',
    ]
    for sel in selectors:
        el = page.query_selector(sel)
        if el and el.is_visible():
            return True
    return False


def _click_consent(page):
    """Click the Allow/Accept/Authorize button."""
    selectors = [
        'button:has-text("Allow")',
        'button:has-text("Accept")',
        'button:has-text("Authorize")',
        'input[value="Allow"]',
        '#allow_btn',
    ]
    for sel in selectors:
        el = page.query_selector(sel)
        if el and el.is_visible():
            el.click()
            return
    raise RuntimeError("Consent button not found")


def _wait_for_callback(page, timeout_sec):
    """Wait until the page URL contains localhost/callback."""
    if _is_callback_redirect(page):
        print("[oauth] Callback redirect confirmed")
        return

    print(f"[oauth] Waiting up to {timeout_sec}s for callback redirect...")
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if _is_callback_redirect(page):
            print("[oauth] Callback redirect confirmed")
            return
        # Also check if a new page/popup received the redirect
        for p in page.context.pages:
            if "localhost" in p.url and "/callback" in p.url:
                print("[oauth] Callback redirect confirmed (via popup)")
                return
        time.sleep(1)
    raise RuntimeError(f"Callback redirect not received within {timeout_sec}s")


def _save_screenshot(page, directory, label):
    """Save a screenshot for debugging on failure."""
    try:
        ts = int(time.time())
        path = os.path.join(directory, f"oauth-{label}-{ts}.png")
        page.screenshot(path=path)
        print(f"[oauth] Screenshot saved: {path}", file=sys.stderr)
    except Exception:
        pass


if __name__ == "__main__":
    main()
