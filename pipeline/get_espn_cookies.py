#!/usr/bin/env python3
import argparse, os, sys, time
from typing import Optional, Tuple
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

LOGIN_URLS = [
    "https://www.espn.com/login/",
    "https://registerdisney.go.com/login"  # fallback
]
LEAGUE_URL_TMPL = "https://fantasy.espn.com/football/league?leagueId={league}"
API_PING_TMPL = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/2025/segments/0/leagues/{league}?view=mTeam"

def write_env_line(github_env_path: str, key: str, value: str) -> None:
    with open(github_env_path, "a", encoding="utf-8") as f:
        f.write(f"{key}={value}\n")

def save(page, folder: str, name: str):
    try:
        os.makedirs(folder, exist_ok=True)
        page.screenshot(path=os.path.join(folder, f"{name}.png"), full_page=True)
    except Exception:
        pass

def find_login_frame(page):
    for fr in page.frames:
        url = (fr.url or "").lower()
        name = (fr.name or "").lower()
        if any(k in url for k in ["disney", "did", "login"]) or any(k in name for k in ["disney","login"]):
            return fr
    # fallback: first child frame
    for fr in page.frames:
        if fr != page.main_frame:
            return fr
    return page.main_frame

def try_fill(fr, selectors, text) -> bool:
    for sel in selectors:
        try:
            el = fr.wait_for_selector(sel, timeout=6000)
            el.fill(text)
            return True
        except Exception:
            continue
    return False

def try_click(fr, selectors) -> bool:
    for sel in selectors:
        try:
            el = fr.wait_for_selector(sel, timeout=6000)
            el.click()
            return True
        except Exception:
            continue
    return False

def harvest_cookies(ctx, domain_filter: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    swid = None
    s2 = None
    for c in ctx.cookies():
        if domain_filter and domain_filter not in (c.get("domain") or ""):
            continue
        if c.get("name") == "SWID":
            swid = c.get("value")
        elif c.get("name") == "espn_s2":
            s2 = c.get("value")
    return swid, s2

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True)
    ap.add_argument("--write-github-env", required=True, help="Path to $GITHUB_ENV")
    ap.add_argument("--screenshot-dir", default="", help="Folder to drop debug screenshots")
    args = ap.parse_args()

    user = os.getenv("ESPN_USER")
    pw = os.getenv("ESPN_PASS")
    if not user or not pw:
        print("ESPN_USER/ESPN_PASS missing", file=sys.stderr)
        sys.exit(2)

    league_url = LEAGUE_URL_TMPL.format(league=args.league)
    api_ping = API_PING_TMPL.format(league=args.league)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari"
        )
        page = ctx.new_page()

        # 1) Hit a login page
        ok_login = False
        for url in LOGIN_URLS:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                ok_login = True
                break
            except PWTimeout:
                continue
        if not ok_login:
            save(page, args.screenshot_dir, "step0_login_nav_fail")
            print("Could not reach ESPN/Disney login", file=sys.stderr)
            browser.close()
            sys.exit(2)

        save(page, args.screenshot_dir, "step1_login_landing")

        # Sometimes there's a visible 'Log In' trigger to open the iframe
        for sel in ["button:has-text('Log In')", "a:has-text('Log In')", "[data-testid='log-in-btn']"]:
            try:
                if page.query_selector(sel):
                    page.click(sel, timeout=3000)
                    break
            except Exception:
                pass

        # 2) Find login frame and fill credentials
        frame = find_login_frame(page)
        user_ok = try_fill(frame, ["#did-ui-view input[type=email]", "input[name=email]", "input[type=text]"], user)
        pass_ok = try_fill(frame, ["#did-ui-view input[type=password]", "input[name=password]"], pw)

        if not (user_ok and pass_ok):
            # give the iframe a second pass
            time.sleep(1.5)
            frame = find_login_frame(page)
            if not user_ok:
                user_ok = try_fill(frame, ["#did-ui-view input[type=email]", "input[name=email]", "input[type=text]"], user)
            if not pass_ok:
                pass_ok = try_fill(frame, ["#did-ui-view input[type=password]", "input[name=password]"], pw)

        if not (user_ok and pass_ok):
            save(page, args.screenshot_dir, "step2_login_fields_not_found")
            print("Could not locate login fields", file=sys.stderr)
            browser.close()
            sys.exit(2)

        if not try_click(frame, ["#did-ui-view button[type=submit]", "button[type=submit]", "[data-testid='log-in-btn']"]):
            save(page, args.screenshot_dir, "step3_submit_not_clicked")
            print("Could not click submit", file=sys.stderr)
            browser.close()
            sys.exit(2)

        # Wait for login to settle
        try:
            page.wait_for_load_state("networkidle", timeout=60000)
        except Exception:
            pass

        save(page, args.screenshot_dir, "step4_after_submit")

        # 3) Go to league landing (sets fantasy cookies on subdomain)
        try:
            page.goto(league_url, wait_until="networkidle", timeout=60000)
        except Exception:
            save(page, args.screenshot_dir, "step5_league_nav_fail")
            print("League page failed to load after login", file=sys.stderr)
            browser.close()
            sys.exit(2)

        time.sleep(2.0)  # give cookies time
        save(page, args.screenshot_dir, "step6_league_loaded")

        swid, s2 = harvest_cookies(ctx)
        # 4) Force an API request in-page to ensure cookies are valid for the API
        if not (swid and s2):
            try:
                page.goto(api_ping, wait_until="domcontentloaded", timeout=60000)
                time.sleep(1.5)
                swid, s2 = harvest_cookies(ctx)
            except Exception:
                pass

        browser.close()

    if not swid or not s2:
        print("Failed to retrieve SWID/espn_s2 cookies from ESPN after login", file=sys.stderr)
        sys.exit(2)

    write_env_line(args.write_github_env, "SWID", swid)
    write_env_line(args.write_github_env, "ESPN_S2", s2)
    print("Got cookies ✔")

if __name__ == "__main__":
    main()
