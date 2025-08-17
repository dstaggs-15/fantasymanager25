#!/usr/bin/env python3
import argparse, json, os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

def write_to_github_env(env_file, pairs):
    # pairs: dict of {NAME: VALUE}
    with open(env_file, "a", encoding="utf-8") as f:
        for k, v in pairs.items():
            f.write(f"{k}={v}\n")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True, help="ESPN league id")
    ap.add_argument("--write-github-env", required=True, help="Path to $GITHUB_ENV")
    args = ap.parse_args()

    username = os.getenv("ESPN_USER", "").strip()
    password = os.getenv("ESPN_PASS", "").strip()
    if not username or not password:
        print("ESPN_USER/ESPN_PASS env vars are required", file=sys.stderr)
        sys.exit(2)

    league = args.league.strip()

    login_url = f"https://www.espn.com/login/"
    league_hub = f"https://fantasy.espn.com/football/league?leagueId={league}"

    # Optional artifacts dir for screenshots if you want them
    artifacts = os.getenv("ARTIFACTS_DIR")
    Path(artifacts).mkdir(parents=True, exist_ok=True) if artifacts else None

    # Reuse browsers downloaded under the runner user if provided
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(Path.home() / ".cache" / "ms-playwright"))

    with sync_playwright() as p:
        # Make headless look less “automation-y”
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        ctx = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"),
            locale="en-US",
        )
        # Remove navigator.webdriver flag
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")

        page = ctx.new_page()
        page.goto(league_hub, wait_until="domcontentloaded")
        # Force open the ESPN login modal
        page.goto(login_url, wait_until="domcontentloaded")

        # The login form is in an iframe titled “Sign in”
        try:
            frame = page.frame_locator("iframe[title='Sign in']")
            # Wait for placeholders EXACTLY as seen in your screenshot
            user_input = frame.get_by_placeholder("Username or Email Address")
            pass_input = frame.get_by_placeholder("Password (case sensitive)")
            user_input.wait_for(timeout=15000)
            pass_input.wait_for(timeout=15000)
        except PWTimeout:
            if artifacts:
                page.screenshot(path=f"{artifacts}/step_fields_timeout.png", full_page=True)
            print("Could not locate login fields", file=sys.stderr)
            sys.exit(2)

        # Fill and submit
        user_input.fill(username)
        pass_input.fill(password)
        frame.get_by_role("button", name="Log In").click()

        # After login, ESPN sets cookies on *.espn.com and fantasy.espn.com
        # Wait for cookies to appear
        swid, s2 = None, None
        deadline = time.time() + 20
        while time.time() < deadline and (not swid or not s2):
            cookies = ctx.cookies()
            for c in cookies:
                if c["name"].upper() in ("SWID", "ESPN_S2", "ESPN_s2", "espn_s2"):
                    if c["name"].upper() == "SWID":
                        swid = c["value"]
                    else:
                        s2 = c["value"]
            if not swid or not s2:
                time.sleep(1)

        if artifacts:
            page.screenshot(path=f"{artifacts}/post_login.png", full_page=True)

        if not swid or not s2:
            print("Failed to retrieve SWID/espn_s2 cookies from ESPN after login", file=sys.stderr)
            sys.exit(2)

        # Normalize names we use in the rest of the pipeline
        write_to_github_env(args.write_github_env, {
            "ESPN_SWID": swid,
            "ESPN_S2": s2,
        })

        print("Got cookies. ✅")
        ctx.close()
        browser.close()

if __name__ == "__main__":
    sys.exit(main())
