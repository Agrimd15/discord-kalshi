import aiohttp
import asyncio
import os
import json
from auth import sign_request
from dotenv import load_dotenv

load_dotenv()

KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH")

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

async def fetch_all_series():
    """
    Fetches ALL active series from Kalshi /series endpoint.
    Uses pagination if necessary (loop until no cursor).
    """
    all_series = []
    cursor = None
    
    print("Fetching series...", end="", flush=True)

    series_url = f"{BASE_URL}/series"

    while True:
        params = {"limit": 1000} # Max limit
        if cursor: 
            params["cursor"] = cursor
        
        headers = sign_request("GET", "/trade-api/v2/series", KALSHI_KEY_ID, KALSHI_PRIVATE_KEY_PATH)
        
        async with aiohttp.ClientSession() as session:
            try:
                # Need to construct full url with params manually for requests or use params dict
                # aiohttp handles params dict well
                async with session.get(series_url, headers=headers, params=params) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        print(f"\nError fetching series: {resp.status} {text}")
                        break
                    
                    data = await resp.json()
                    series_list = data.get("series", [])
                    cursor = data.get("cursor")
                    
                    all_series.extend(series_list)
                    print(f" {len(all_series)}...", end="", flush=True)
                    
                    if not cursor:
                        break
            except Exception as e:
                print(f"\nException: {e}")
                break
    
    print(f"\nFetched {len(all_series)} series.")
    return all_series

async def main():
    series = await fetch_all_series()

    # Filter List from User Screenshot
    TARGET_SPORTS = [
        "Football", "Basketball", "Hockey", "Soccer", "Golf", 
        "Cricket", "Boxing", "Darts", "Baseball", "Chess", 
        "Esports", "Motorsport"
    ]
    
    # Structure: SportName -> { Title: Ticker }
    grouped = {sport: {} for sport in TARGET_SPORTS}
    
    # Filter Logic
    ALLOW_KW = ["game", "match", "games", "spread", "total", "matchup"]
    DENY_KW = [
        "season", "winner", "champion", "draft", "mvp", "coach", "pick", "prop", 
        "leader", "review", "rating", "approval", "vote", "sign", "trade", 
        "cover", "retire", "mention", "record", "odds", "specials", "win", 
        "lose", "qualifier", "score", "attendance", "viewership"
    ]

    for s in series:
        tags = s.get("tags") or []
        tags = [t.lower() for t in tags]
        ticker = s.get("ticker")
        title = s.get("title", s.get("ticker", "")).strip()
        t_lower = title.lower()

        # Check Sport
        matched_sport = None
        for sport in TARGET_SPORTS:
            if sport.lower() in tags:
                matched_sport = sport
                break
        
        if matched_sport:
            # Check Filtering
            has_allow = any(Kw in t_lower for Kw in ALLOW_KW)
            has_deny = any(Kw in t_lower for Kw in DENY_KW)
            
            # Special Case: "NBA Games" (KXNBAGAMES) -> keep
            # "Pro football wins" -> Deny (contains 'win')
            
            if has_allow and not has_deny:
                grouped[matched_sport][title] = ticker
            
            # Also keep broad "League" series if they don't have deny keywords
            # e.g. "Formula 1" (Motorsport) might not have "Game" in title?
            # Adjust as needed. For now strict.

    # Remove empty categories
    final_group = {k: v for k, v in grouped.items() if v}
    
    # Sort
    sorted_grouped = {}
    for k in sorted(final_group.keys()):
        # Sort sub-items by title
        sorted_grouped[k] = dict(sorted(final_group[k].items()))

    content = f'''# Auto-generated Sports Hierarchy
HIERARCHY = {json.dumps(sorted_grouped, indent=4)}

def get_ticker_by_name(query):
    """
    Strict lookup.
    """
    q = query.lower().strip()
    if q.startswith("kx"): return q.upper()

    for sport, map_data in HIERARCHY.items():
        for name, ticker in map_data.items():
            if name.lower() == q: return ticker
            if ticker.lower() == q: return ticker
    return None
'''
    with open("kalshi_hierarchy.py", "w") as f:
        f.write(content)
    
    print(f"Successfully wrote Sports hierarchy ({len(sorted_grouped)} categories) to kalshi_hierarchy.py")

if __name__ == "__main__":
    asyncio.run(main())
