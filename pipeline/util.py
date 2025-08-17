import os, time, json, sys
from typing import Dict, Any, Optional
import requests

def auth_headers(swid: str, s2: str) -> Dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari",
        "Accept": "application/json, text/plain, */*",
        "Cookie": f"SWID={swid}; espn_s2={s2}",
        "Referer": "https://fantasy.espn.com/",
    }

def fetch_json(url: str, headers: Dict[str,str], tries: int = 5, backoff: float = 2.0) -> Any:
    last_err: Optional[str] = None
    sess = requests.Session()
    for i in range(1, tries+1):
        r = sess.get(url, headers=headers, timeout=30)
        ctype = r.headers.get("content-type", "")
        if r.status_code == 200 and "application/json" in ctype.lower():
            return r.json()
        last_err = f"Non-JSON (content-type={ctype}) status={r.status_code}"
        time.sleep(backoff * i)
    # cloudscraper fallback
    try:
        import cloudscraper  # type: ignore
        scraper = cloudscraper.create_scraper()
        r = scraper.get(url, headers=headers, timeout=30)
        ctype = r.headers.get("content-type", "")
        if r.status_code == 200 and "application/json" in ctype.lower():
            return r.json()
        last_err = f"Non-JSON (content-type={ctype}) status={r.status_code}"
    except Exception as e:
        last_err = f"cloudscraper failed: {e}"
    raise RuntimeError(f"GET {url} failed after retries: {last_err}")

def write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "data": obj}, f, ensure_ascii=False, indent=2)
