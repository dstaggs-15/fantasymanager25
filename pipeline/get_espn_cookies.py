#!/usr/bin/env python3
# pipeline/get_espn_cookies.py
#
# Logs into fantasy.espn.com with ESPN_USER/ESPN_PASS using Playwright (Chromium),
# grabs SWID and espn_s2 cookies, and exports them to the current job's env by
# appending to the file path passed via --write-github-env (GITHUB_ENV).
#
# Usage:
#   python pipeline/get_espn_cookies.py --league 508419792 --write-github-env "$GITHUB_ENV"
#
# Required env:
#   ESPN_USER, ESPN_PASS
#
# Optional env:
#   PLAYWRIGHT_BROWSERS_PATH  (helpful on self-hosted runners)

import argparse
import os
import sys
import time
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

LOGIN_URL_TMPL = "https://fantasy.espn.com/football/league?leagueId={league_id}"

def fail(msg: str, code: int = 2):
    print(msg, file=sys.stderr)
    sys.exit(code)

def mask(s: str) -> str:
    if not s:
        return ""
    if len(s) <= 8:
        return "*" * len(s)
    return s[:4] + "..." + s[-4:]

def write_github_env(env_path: str, kv: dict):
    # Append VAR=VALUE lines. Do not quote values; newlines are not expected.
    with open(env_path, "a", encoding="utf-8") as f:
        for k, v in kv.items():
            f.write(f"{k}={v}\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--league", required=True, help="ESPN leagueId")
    parser.add_argument("--write-github-env", required=True, help="Path to $GITHUB_ENV file")
    args = parser.parse_args()

    user = os.environ.get("ESPN_USER", "")
    pw = os.environ.get("ESPN_PASS", "")
    if not user or not pw:
        fail("ESPN_USER/ESPN_PASS not set in env")

    league_url = LOGIN_URL_TMPL.format(league_id=args.league)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        # 1) Hit league page (it will redirect to SSO)
        page.goto(league_url, wait_until="domcontentloaded", timeout=120_000)

        # 2) Detect and handle ESPN SSO page
        # ESPN SSO has input[name='username'] and input[name='password'] eventually.
        # There can be interstitials; try to be robust with waits.
        try:
            page.wait_for_selector("input[name='username']", timeout=60_000)
        except Exception:
            # Maybe already logged in or cookie present. Continue.
            pass

        # If username field exists, do login flow.
        if page.locator("input[name='username']").count() > 0:
            page.fill("input[name='username']", user)
            # ESPN SSO uses a “Continue” button then password on next step
            if page.locator("button[type='submit']").count() > 0:
                page.click("button[type='submit']")
            else:
                page.press("input[name='username']", "Enter")

            # Wait for password field
            page.wait_for_selector("input[name='password']", timeout=60_000)
            page.fill("input[name='password']", pw)

            # Submit
            if page.locator("button[type='submit']").count() > 0:
                page.click("button[type='submit']")
            else:
                page.press("input[name='password']", "Enter")

            # give time to redirect back to league page
            page.wait_for_load_state("domcontentloaded", timeout=120_000)

        # 3) Ensure we’ve landed on fantasy.espn.com
        # If still on SSO domain, wait a bit longer to redirect.
        max_wait = time.time() + 30
        while time.time() < max_wait:
            host = urlparse(page.url).hostname or ""
            if "espn.com" in host:
                break
            time.sleep(1)

        # 4) Grab cookies for fantasy.espn.com
        cookies = ctx.cookies()
        swid_val = None
        s2_val = None
        for c in cookies:
            if c.get("name") == "SWID":
                swid_val = c.get("value")
            if c.get("name") == "espn_s2":
                s2_val = c.get("value")

        browser.close()

    if not swid_val or not s2_val:
        fail("Failed to retrieve SWID/espn_s2 cookies from ESPN after login")

    # Write to GITHUB_ENV
    write_github_env(args.write_github_env, {
        "SWID": swid_val,
        "ESPN_S2": s2_val,
    })

    print(f"OK: SWID={mask(swid_val)} ESPN_S2={mask(s2_val)}")

if __name__ == "__main__":
    main()
