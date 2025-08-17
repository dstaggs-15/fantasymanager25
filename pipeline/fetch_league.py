#!/usr/bin/env python3
"""
Log in to ESPN with Playwright and export SWID + espn_s2 cookies.

ENV (required):
  ESPN_USER   -> your ESPN username/email (from GitHub Secrets)
  ESPN_PASS   -> your ESPN password (from GitHub Secrets)

ARGS:
  --league <id>                 (optional) visit a league page to make sure cookies apply to fantasy domain
  --write-github-env <filepath> (optional) append SWID/ESPN_S2 to $GITHUB_ENV so later steps can read them

Outputs:
  - prints masked cookie values
  - writes docs/data/espn_cookies.json (for debugging/timestamps)
  - optionally appends SWID/ESPN_S2 to a GitHub Actions env file
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError


LOGIN_URL = "https://www.espn.com/login/"
FANTASY_LEAGUE_URL = "https://fantasy.espn.com/football/league?leagueId={league_id}"
COOKIE_DOMAINS = ["espn.com", "fantasy.espn.com", ".espn.com", ".fantasy.espn.com"]


def find_cookie(cookies, name: str) -> Optional[str]:
    for c in cookies:
        if c.get("name") == name and any(d in (c.get("domain") or "") for d in COOKIE_DOMAINS):
            return c.get("value")
    return None


def mask(s: str, keep: int = 6) -> str:
    if not s:
        return ""
    return s[:keep] + "…" + s[-keep:]


def main():
    league_id = None
    gh_env_path = None

    # crude arg parse
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--league" and i + 1 < len(args):
            league_id = args[i + 1].strip()
            i += 2
        elif args[i] == "--write-github-env" and i + 1 < len(args):
            gh_env_path = args[i + 1].strip()
            i += 2
        else:
            print(f"Unknown arg: {args[i]}", file=sys.stderr)
            i += 1

    user = os.getenv("ESPN_USER")
    pwd = os.getenv("ESPN_PASS")

    if not user or not pwd:
        print("ERROR: ESPN_USER and/or ESPN_PASS not set in environment.", file=sys.stderr)
        sys.exit(2)

    out_json = Path("docs/data/espn_cookies.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)  # runner is headless VPS
        ctx = browser.new_context()  # fresh context
        page = ctx.new_page()

        try:
            # 1) hit login page
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)

            # Some ESPN pages embed the login iframe; guard both cases
            # Try common selectors:
            # Email / username
            selectors = [
                'input[name="email"]',
                'input#InputLoginValue',
                'input[type="email"]',
            ]
            email_input = None
            for sel in selectors:
                try:
                    email_input = page.locator(sel).first
                    email_input.wait_for(state="visible", timeout=10_000)
                    break
                except PWTimeoutError:
                    email_input = None

            if not email_input:
                # Some flows require clicking "Log In" button first
                try:
                    page.get_by_role("button", name="Log In", exact=False).first.click(timeout=5_000)
                    page.wait_for_timeout(1000)
                except Exception:
                    pass
                # Try again:
                for sel in selectors:
                    try:
                        email_input = page.locator(sel).first
                        email_input.wait_for(state="visible", timeout=10_000)
                        break
                    except PWTimeoutError:
                        email_input = None

            if not email_input:
                raise RuntimeError("Could not find login email field on ESPN.")

            email_input.fill(user)

            # Password
            pwd_selectors = [
                'input[name="password"]',
                'input#InputPassword',
                'input[type="password"]',
            ]
            pwd_input = None
            for sel in pwd_selectors:
                try:
                    pwd_input = page.locator(sel).first
                    pwd_input.wait_for(state="visible", timeout=10_000)
                    break
                except PWTimeoutError:
                    pwd_input = None
            if not pwd_input:
                raise RuntimeError("Could not find password field on ESPN.")
            pwd_input.fill(pwd)

            # Submit (common submit button)
            try:
                page.get_by_role("button", name="Log In", exact=False).first.click(timeout=10_000)
            except Exception:
                # fallback: hit Enter in password field
                pwd_input.press("Enter")

            # Wait a bit for navigation/session setup
            page.wait_for_timeout(3000)

            # 2) Touch a fantasy league page so cookies are scoped to fantasy.espn.com
            if league_id:
                page.goto(FANTASY_LEAGUE_URL.format(league_id=league_id), wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(3000)

            # 3) Grab cookies from context
            cookies = ctx.cookies()
            swid = find_cookie(cookies, "SWID")
            s2 = find_cookie(cookies, "espn_s2")

            if not swid or not s2:
                # ESPN may require MFA or extra step
                raise RuntimeError("Could not capture SWID/espn_s2 cookies. If this account has MFA, complete it or use an app password.")

            # Write json for debugging + timestamp
            out = {
                "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "league_id": league_id,
                "SWID": swid,
                "espn_s2": s2,
                "note": "Saved by Playwright login on self-hosted runner.",
            }
            out_json.write_text(json.dumps(out, indent=2))
            print(f"Wrote {out_json} (SWID={mask(swid)}, espn_s2={mask(s2)})")

            # Optionally export to GitHub Actions environment
            if gh_env_path:
                with open(gh_env_path, "a", encoding="utf-8") as f:
                    f.write(f"SWID={swid}\n")
                    f.write(f"ESPN_S2={s2}\n")
                print(f"Exported SWID/ESPN_S2 to GITHUB_ENV")

        finally:
            ctx.close()
            browser.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
