# pipeline/get_espn_cookies.py
# Usage:
#   python pipeline/get_espn_cookies.py --league 508419792 --write-github-env /path/to/GITHUB_ENV
#
# Requires repo secrets or env: ESPN_USER, ESPN_PASS
# Writes SWID and ESPN_S2 to the provided $GITHUB_ENV file on success.
from __future__ import annotations
import argparse, os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

LOGIN_URL = "https://www.espn.com/login"
FANTASY_URL_TMPL = "https://fantasy.espn.com/football/team?leagueId={league}"

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
)

def write_github_env(env_path: str, key: str, value: str) -> None:
    Path(env_path).parent.mkdir(parents=True, exist_ok=True)
    with open(env_path, "a", encoding="utf-8") as f:
        f.write(f"{key}={value}\n")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True, dest="league")
    ap.add_argument("--write-github-env", required=True, dest="github_env")
    args = ap.parse_args()

    user = os.getenv("ESPN_USER")
    pwd  = os.getenv("ESPN_PASS")
    if not user or not pwd:
        print("ESPN_USER/ESPN_PASS not set", file=sys.stderr)
        return 2

    screenshots_dir = Path("artifacts"); screenshots_dir.mkdir(exist_ok=True, parents=True)

    with sync_playwright() as p:
        # Use a persistent context so cookies survive page navigations
        browser = p.chromium.launch(headless=True, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ])
        context = browser.new_context(
            user_agent=UA,
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            timezone_id="America/New_York",
        )
        page = context.new_page()

        # 1) Hit the login URL
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60_000)
        page.screenshot(path=str(screenshots_dir / "step1_login_landing.png"))

        try:
            # The login dialog is inside an iframe whose name usually starts with "oneid".
            # Use a locator that will work even if they change the name slightly.
            frame = page.frame_locator("iframe[name^='oneid'], iframe[id^='oneid'], iframe[src*='oneid']").first

            # Wait for inputs by placeholder text shown on your screenshot
            user_input = frame.get_by_placeholder("Username or Email Address")
            pass_input = frame.get_by_placeholder("Password (case sensitive)")

            user_input.wait_for(state="visible", timeout=20_000)
            pass_input.wait_for(state="visible", timeout=20_000)

            user_input.fill(user)
            pass_input.fill(pwd)

            # Click the blue "Log In" button
            frame.get_by_role("button", name="Log In").click()

        except PWTimeout:
            page.screenshot(path=str(screenshots_dir / "step2_login_fields_not_found.png"))
            print("Could not locate login fields", file=sys.stderr)
            context.close(); browser.close()
            return 2

        # 2) Give SSO a moment; then navigate to a league page so the cookies are set for fantasy.*
        page.wait_for_timeout(3000)
        page.goto(FANTASY_URL_TMPL.format(league=args.league), wait_until="domcontentloaded", timeout=60_000)
        page.screenshot(path=str(screenshots_dir / "step3_after_login_league.png"))

        # 3) Pull cookies (both domains matter)
        def find_cookie(name: str):
            for c in context.cookies():
                if c.get("name") == name:
                    return c.get("value")
            return None

        swid = find_cookie("SWID")
        s2   = find_cookie("espn_s2")

        if not swid or not s2:
            # Try fantasy subdomain explicitly once more
            page.goto("https://fantasy.espn.com", wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(1500)
            swid = swid or find_cookie("SWID")
            s2   = s2 or find_cookie("espn_s2")

        context.close(); browser.close()

        if not swid or not s2:
            print("Failed to retrieve SWID/espn_s2 cookies from ESPN after login", file=sys.stderr)
            return 2

        # 4) Write to GITHUB_ENV so later steps can use them
        write_github_env(args.github_env, "SWID", swid)
        write_github_env(args.github_env, "ESPN_S2", s2)

        # Also drop a copy for debugging if you ever need it locally (ignored by git)
        Path(".local_debug").mkdir(exist_ok=True)
        with open(".local_debug/cookies.txt", "w") as f:
            f.write(f"SWID={swid}\nESPN_S2={s2}\n")

        print("Got SWID & ESPN_S2 via Playwright.")
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
