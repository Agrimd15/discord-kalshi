
import aiohttp
import asyncio
from datetime import datetime
from .utils import find_best_match

import os
from dotenv import load_dotenv

load_dotenv()

GAMMA_URL = "https://gamma-api.polymarket.com/events"
POLY_API_KEY = os.getenv("POLY_API_KEY")
POLY_SECRET = os.getenv("POLY_SECRET")
POLY_PASSPHRASE = os.getenv("POLY_PASSPHRASE")
POLY_WALLET_KEY = os.getenv("POLY_WALLET_KEY")
POLY_PROXY_ADDRESS = os.getenv("POLY_PROXY_ADDRESS")

async def get_balance():
    """
    Fetches Polymarket balance.
    Requires complete API Credentials.
    """
    if not all([POLY_API_KEY, POLY_SECRET, POLY_PASSPHRASE, POLY_WALLET_KEY, POLY_PROXY_ADDRESS]):
        return None, "Missing Polymarket Keys. Need: API Key, Secret, Passphrase, Wallet Key, Proxy Address."
        
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds, BalanceAllowanceParams, AssetType
        # from py_clob_client.constants import PolygonChainId # Not found in installed version
        
        # Initialize Client
        # host: https://clob.polymarket.com
        # chain_id: 137 (Polygon Mainnet)
        client = ClobClient(
            host="https://clob.polymarket.com",
            key=POLY_WALLET_KEY,
            chain_id=137, # Polygon
            signature_type=1 # 0 or 1? Usually 1 (EIP712) or 2? Let's try default or 1.
        )
        
        # Set API  Creds
        creds = ApiCreds(
            api_key=POLY_API_KEY,
            api_secret=POLY_SECRET,
            api_passphrase=POLY_PASSPHRASE
        )
        client.set_api_creds(creds)
        
        # Fetch Balance (Collateral)
        params = BalanceAllowanceParams(
            asset_type=AssetType.COLLATERAL
        )
        resp = client.get_balance_allowance(params=params)
        
        # resp format: {'balance': '123456', 'allowance': ...} (integers/wei?)
        # USDC has 6 decimals.
        
        if resp and "balance" in resp:
            # USDC is 6 decimals
            raw_bal = int(resp["balance"])
            bal_usd = raw_bal / 1_000_000.0
            return bal_usd, None
            
        return 0.0, "Could not parse balance response."

    except ImportError:
        return None, "Missing dependency. Run `pip install py-clob-client`."
    except Exception as e:
        return None, f"Polymarket Client Error: {e}"

async def search_events(query, tag_id=None):
    """
    Search Polymarket events by query string (e.g. Team Name).
    Optional: Filter by Tag ID (e.g. 450 for NFL).
    """
    params = {
        "limit": 10,
        "active": "true",
        "closed": "false",
        "q": query
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # API seems to ignore 'q', so we fetch more and filter locally.
            # Using limit 1000 to catch active sports games from popular feed.
            # If tag_id is provided, filter by it on server side!
            req_params = {
                "limit": 1000,
                "active": "true",
                "closed": "false",
                "q": query 
            }
            if tag_id:
                req_params["tag_id"] = tag_id
                # Keep limit high (1000) even with tag, as categories like NFL have many events (props).
                # req_params["limit"] = 100
            async with session.get(GAMMA_URL, params=req_params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Client-side validation: Ensure query is actually in title
                    # Split query into words to be lenient? 
                    # Or just query.lower() in title.lower()
                    
                    q_low = query.lower()
                    filtered = []
                    for e in data:
                        t = e.get("title", "").lower()
                        # If query is "Seattle", match "Seattle"
                        if q_low in t:
                            filtered.append(e)
                            
                    return filtered 
                else:
                    print(f"Polymarket API Error: {resp.status}")
                    return []
        except Exception as e:
            print(f"Polymarket Request Error: {e}")
            return []

async def get_market_odds(condition_id):
    """
    Fetch specific market odds if needed. 
    However, the search/events endpoint usually returns markets included.
    We'll assume we get markets in the event data.
    """
    pass

async def find_polymarket_match(kalshi_title, sport=None, date_str=None):
    """
    Finds a matching Polymarket event for a Kalshi event.
    kalshi_title: "Los Angeles Lakers vs Golden State Warriors"
    sport: "NFL", "NBA", etc. (Optional, speeds up search)
    date_str: "Dec 25" (Optional, for validation)
    """
    
    tag_id = None
    if sport:
        # Map Kalshi Sport to Poly Tag
        sport_map = {
            "NFL": 450,
            "NBA": 745,
            "MLB": 2217, # Heuristic
            "Football": 10, # Generic generic
            "Basketball": 28
        }
        # Kalshi usually gives "NFL", "NBA".
        tag_id = sport_map.get(sport.upper())
    
    # NFL Team Mapping (Kalshi City/Abbr -> Poly Nickname)
    nfl_map = {
        "arizona": "cardinals", "atlanta": "falcons", "baltimore": "ravens", 
        "buffalo": "bills", "carolina": "panthers", "chicago": "bears",
        "cincinnati": "bengals", "cleveland": "browns", "dallas": "cowboys",
        "denver": "broncos", "detroit": "lions", "green bay": "packers",
        "houston": "texans", "indianapolis": "colts", "jacksonville": "jaguars",
        "kansas city": "chiefs", "las vegas": "raiders", "los angeles c": "chargers",
        "los angeles r": "rams", "miami": "dolphins", "minnesota": "vikings",
        "new england": "patriots", "new orleans": "saints", "new york g": "giants",
        "new york j": "jets", "philadelphia": "eagles", "pittsburgh": "steelers",
        "san francisco": "49ers", "seattle": "seahawks", "tampa bay": "buccaneers",
        "tennessee": "titans", "washington": "commanders"
    }

    # NBA Team Mapping
    nba_map = {
        "atlanta": "hawks", "boston": "celtics", "brooklyn": "nets",
        "charlotte": "hornets", "chicago": "bulls", "cleveland": "cavaliers",
        "dallas": "mavericks", "denver": "nuggets", "detroit": "pistons",
        "golden state": "warriors", "houston": "rockets", "indiana": "pacers",
        "los angeles c": "clippers", "lac": "clippers",
        "los angeles l": "lakers", "lal": "lakers",
        "memphis": "grizzlies", "miami": "heat", "milwaukee": "bucks",
        "minnesota": "timberwolves", "new orleans": "pelicans", "new york": "knicks",
        "oklahoma city": "thunder", "orlando": "magic", "philadelphia": "76ers",
        "phoenix": "suns", "portland": "trail blazers", "sacramento": "kings",
        "san antonio": "spurs", "toronto": "raptors", "utah": "jazz",
        "washington": "wizards"
    }

    # 1. Extract Teams
    # Kalshi: "Team A vs Team B" or "Team A at Team B"
    s_title = kalshi_title.lower().strip()
    team_a = ""
    team_b = ""
    
    if " vs " in s_title:
        parts = s_title.split(" vs ")
        team_a = parts[0].strip()
        if len(parts) > 1: team_b = parts[1].strip()
    elif " at " in s_title:
        parts = s_title.split(" at ")
        team_a = parts[0].strip()
        if len(parts) > 1: team_b = parts[1].strip()
    else:
        # Fallback
        team_a = s_title

    if sport == "NFL":
        team_a = nfl_map.get(team_a, team_a)
        team_b = nfl_map.get(team_b, team_b)

    if sport == "NBA":
        team_a = nba_map.get(team_a, team_a)
        team_b = nba_map.get(team_b, team_b)
            
    # Validated: If team name was translated, using it for search is usually better.
    # e.g. "Kings" works better than "Sacramento".
            
    # Helper to search and filter
    async def try_search(q):
        # Remove single letter suffixes usually found in Kalshi (e.g. "Los Angeles R")
        # Heuristic: If name ends with space + valid letter, strip it?
        # Actually, let's just search raw first, if 0, try stripping.
        
        # Try searching with Tag first (more specific)
        cands = await search_events(q, tag_id=tag_id)
        if cands: 
            return cands
            
        # If no results with Tag, try Global search (Fallback)
        # Sometimes events are tagged incorrectly or API fails with tag filter
        if tag_id:
            cands = await search_events(q, tag_id=None)
            if cands: 
                return cands
        
        # Strip suffix " R", " C" etc from Kalshi names?
        # Only if length > 2
        if len(q.split()) > 1 and len(q.split()[-1]) == 1:
             q_stripped = " ".join(q.split()[:-1])
             # Try stripped with tag
             cands = await search_events(q_stripped, tag_id=tag_id)
             if cands: return cands
             # Try stripped global
             if tag_id:
                 cands = await search_events(q_stripped, tag_id=None)
                 if cands: return cands
             
        return []

    # 2. Search Strategy
    # Try Team A. If < 1 match, try Team B.
    # Polymarket search is usually good with one keyword (e.g. "Seahawks")
    
    candidates = []
    if team_a:
        candidates = await try_search(team_a)
        
    if not candidates and team_b:
        candidates = await try_search(team_b)
        
    if not candidates:
        return None
        
    # 3. Fuzzy Match
    # Candidates structure: List of dicts. We need to map them to simple dicts for utils.
    
    # Construct list for matcher
    cand_list = []
    for c in candidates:
        cand_list.append({
            "title": c.get("title"),
            "id": c.get("id"),
            "markets": c.get("markets"),
            "slug": c.get("slug")
        })
        
    # Use mapped title for matching if we translated it
    match_title = kalshi_title
    if sport == "NFL" and team_a and team_b:
        # Construct "Rams vs Seahawks" to match Poly format
        # Poly format often "Home vs Away" or "Away @ Home" or just "vs".
        # We can try "Team A vs Team B"
        match_title = f"{team_a.title()} vs {team_b.title()}"
    
    match, score = find_best_match(match_title, cand_list, threshold=0.4) # Lower threshold slightly
    
    if match:
        # 4. Extract Odds
        # Polymarket events have multiple markets. We need the "Winner" or main Moneyline market.
        # Usually the first one or one with "Winner" description.
        markets = match.get("markets", [])
        if not markets:
            return None
            
        # Find Moneyline equivalent
        # Often the main market. Look for "match winner" or binary.
        # For simple mapping, let's take the market with highest volume? Or just the first one.
        # Let's take the first one for now.
        
        m = None
        
        # Smart selection of the "Moneyline" / "Winner" market
        # 1. Try Exact Title Match first
        for market in markets:
            if market.get("question") == match.get("title"):
                m = market
                break
                
        # 2. If no exact match, try filtering out props/spreads
        if not m:
            candidates = []
            exclusion_keywords = ["Spread", "Total", "Over", "Under", "Handicap", "Touchdown", "Yards", "Field Goal", "1H", "2H", "Quarter"]
            
            for market in markets:
                q_text = market.get("question", "")
                is_excluded = any(k in q_text for k in exclusion_keywords)
                if not is_excluded:
                    candidates.append(market)
            
            # Pick the shortest question candidate (usually the cleanest "Team A vs Team B")
            if candidates:
                candidates.sort(key=lambda x: len(x.get("question", "")))
                m = candidates[0]
                
        # 3. Fallback
        if not m:
             m = markets[0]
             
        # Use Best Bid/Ask if available for more real-time accuracy, fallback to outcomePrices
        # Check if we have bestBid/bestAsk in the market object (from Gamma)
        
        prices = m.get("outcomePrices") # e.g. '["0.52", "0.48"]' (It's a JSON string!)
        import json
        
        yes_price = 0
        no_price = 0
        
        if m.get("bestAsk") is not None:
             try:
                 yes_price = float(m.get("bestAsk")) * 100
                 # Approx No price = 100 - Yes
                 no_price = 100 - yes_price
             except:
                 pass

        if yes_price == 0 and prices:
            try:
                p_list = json.loads(prices)
                if len(p_list) >= 2:
                    yes_price = float(p_list[0]) * 100 # Convert to cents
                    no_price = float(p_list[1]) * 100
            except:
                 pass
             
        # Get Token IDs (Long Integers)
        # Gamma API returns this as a JSON string '["id1", "id2"]' sometimes, or a list.
        raw_token_ids = m.get("clobTokenIds", [])
        token_ids = []
        
        if isinstance(raw_token_ids, str):
            try:
                token_ids = json.loads(raw_token_ids)
            except:
                token_ids = []
        elif isinstance(raw_token_ids, list):
            token_ids = raw_token_ids
            
        t_yes_id = token_ids[0] if len(token_ids) > 0 else None
        t_no_id = token_ids[1] if len(token_ids) > 1 else None
        
        # Get Outcome Names
        outcomes = m.get("outcomes") 
        # Usually ["TeamA", "TeamB"] or ["Yes", "No"]
        # If not present, default to ["Yes", "No"]
        if not outcomes:
            outcomes = ["Yes", "No"]
        elif isinstance(outcomes, str):
            try:
                outcomes = json.loads(outcomes)
            except:
                outcomes = ["Yes", "No"]
        
        return {
            "title": match["title"],
            "id": m.get("id"), # Short Integer ID
            "condition_id": m.get("conditionId"), # Long 0x ID
            "yes_id": t_yes_id,
            "no_id": t_no_id,
            "yes": yes_price,
            "no": no_price,
            "outcomes": outcomes,
            "url": f"https://polymarket.com/event/{match['slug']}"
        }
        
    return None
