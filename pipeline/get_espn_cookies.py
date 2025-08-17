#!/usr/bin/env python3
import argparse
import os
import sys
import time
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

LEAGUE_URL = "https://fantasy.espn.com/football/league?leagueId={league}"

def write_github_env(path, key, value):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{key}={value}\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True)
    ap.add_argument("--write-github-env", required=True, help="Path to $GITHUB_ENV")
    args = ap.parse_args()

    user = os.getenv("ESPN_USER")
    pw = os.getenv("ESPN_PASS")
    if not user or not pw:
        print("ESPN_USER/ESPN_PASS missing", file=sys.stderr)
        sys.exit(2)

    login_url = "https://www.espn.com/login/"
    league_url = LEAGUE_URL.format(league=args.league)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()

        # Go to login
        page.goto(login_url, wait_until="networkidle")
        # ESPN login is in an iframe
        # Try common selectors (ESPN changes UI, so we check a couple)
        try:
            # The login iframe usually contains id or name like "disneyid-iframe" or similar
            frame = None
            for f in page.frames:
                if "login" in (f.name or "").lower() or "disney" in (f.name or "").lower():
                    frame = f
                    break
            if frame is None:
                # Fallback: pick any non-main frame
                frames = [f for f in page.frames if f != page.main_frame]
                frame = frames[0] if frames else page.main_frame
        except Exception:
            frame = page.main_frame

        # Username / password fields (try multiple selectors defensively)
        user_selectors = ["#did-ui-view input[type=email]", "input[name=email]", "input[type=text]"]
        pass_selectors = ["#did-ui-view input[type=password]", "input[name=password]", "input[type=password]"]
        submit_selectors = ["#did-ui-view button[type=submit]", "button[type=submit]", "button[data-testid=log-in-btn]"]

        for sel in user_selectors:
            if frame.query_selector(sel):
                frame.fill(sel, user)
                break
        for sel in pass_selectors:
            if frame.query_selector(sel):
                frame.fill(sel, pw)
                break
        for sel in submit_selectors:
            if frame.query_selector(sel):
                frame.click(sel)
                break

        # Wait for login to propagate
        page.wait_for_load_state("networkidle", timeout=30000)

        # Hit the league page (sets the fantasy cookies)
        page.goto(league_url, wait_until="networkidle")

        # Give cookies time to settle
        time.sleep(2)

        cookies = ctx.cookies()
        swid = None
        s2 = None
        for c in cookies:
            if c.get("name") == "SWID":
                swid = c.get("value")
            if c.get("name") == "espn_s2":
                s2 = c.get("value")

        browser.close()

    if not swid or not s2:
        print("Failed to retrieve SWID/espn_s2 cookies from ESPN after login", file=sys.stderr)
        sys.exit(2)

    # Write to GitHub env so following steps can use them
    write_github_env(args.write_github_env, "SWID", swid)
    write_github_env(args.write_github_env, "ESPN_S2", s2)
    print("Got cookies ✔")

if __name__ == "__main__":
    main()
