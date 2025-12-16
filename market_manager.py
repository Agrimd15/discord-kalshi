import aiohttp
import asyncio
import os
import json
from dotenv import load_dotenv
from auth import sign_request

# Load environment variables
load_dotenv()

KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH")
BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

async def get_games_with_odds(series_ticker):
    """
    Fetches active games and drills down into markets (Moneyline, Spread, Total).
    """
    results = []
    
    # Step A: Get Active Events
    # params: status=active (Kalshi uses 'open' usually for status?), API spec says 'active' or 'open'
    # trying 'active' as per user instruction. If fails, try 'open'.
    # Actually standard is usually "status=open" or "status=active". Let's try 'active' first.
    
    events_url = f"{BASE_URL}/events"
    events_params = {"series_ticker": series_ticker, "status": "open"} 
    
    # Sign 'GET /trade-api/v2/events'
    headers = sign_request("GET", "/trade-api/v2/events", KALSHI_KEY_ID, KALSHI_PRIVATE_KEY_PATH)
    
    async with aiohttp.ClientSession() as session:
        # 1. Fetch Events
        try:
            async with session.get(events_url, headers=headers, params=events_params) as resp:
                if resp.status != 200:
                    print(f"Error fetching events: {resp.status} {await resp.text()}")
                    return "Error fetching events."
                
                data = await resp.json()
                events = data.get("events", [])
                
        except Exception as e:
            return f"Exception fetching events: {e}"
            
        if not events:
            return "No active games."
            
        # 2. Loop through Events to get Markets
        for event in events:
            event_ticker = event.get("event_ticker")
            event_title = event.get("title")
            start_time = event.get("start_time")
            
            # Step B: Get Markets for Each Event
            # Using /markets endpoint with event_ticker param
            markets_url = f"{BASE_URL}/markets"
            mkts_params = {"event_ticker": event_ticker}
            
            # Sign 'GET /trade-api/v2/markets'
            m_headers = sign_request("GET", "/trade-api/v2/markets", KALSHI_KEY_ID, KALSHI_PRIVATE_KEY_PATH)
            
            game_data = {
                "event_title": event_title,
                "start_time": start_time,
                "markets": {
                    "moneyline": [],
                    "spread": [],
                    "total": []
                }
            }
            
            try:
                async with session.get(markets_url, headers=m_headers, params=mkts_params) as m_resp:
                    if m_resp.status == 200:
                        m_data = await m_resp.json()
                        market_list = m_data.get("markets", [])
                        
                        for m in market_list:
                            m_title = m.get("title", "").lower()
                            m_subtitle = m.get("subtitle", "").lower()
                            ticker = m.get("ticker")
                            yes_bid = m.get("yes_bid")
                            no_bid = m.get("no_bid")
                            
                            market_obj = {
                                "ticker": ticker,
                                "yes_bid": yes_bid,
                                "no_bid": no_bid,
                                "title": m.get("title"), # Store original title for display
                                "subtitle": m.get("subtitle")
                            }
                            
                            # Classification Logic
                            # Moneyline: "Winner", or matches team names? 
                            # Usually basic markets have no spread/total numbers
                            # Classification Logic
                            # Moneyline: "Winner", or matches team names? 
                            # Usually basic markets have no spread/total numbers
                            
                            # Prioritize "Wins by" as Spread (e.g. "Values wins by over 7 points")
                            # Also check subtitle for spread numbers
                            is_spread = (
                                "wins by" in m_title or 
                                "spread" in m_title or 
                                "spread" in m_subtitle or 
                                any(c.isdigit() and ("-" in c or "+" in c) for c in m_subtitle.split())
                            )
                            
                            if is_spread:
                                game_data["markets"]["spread"].append(market_obj)
                                
                            elif "over" in m_title or "under" in m_title or "total" in m_title:
                                game_data["markets"]["total"].append(market_obj)
                                
                            else:
                                # Default to Moneyline for now, or check "Winner"
                                # If it's the main market (e.g. "Lakers vs Warriors Winner?")
                                game_data["markets"]["moneyline"].append(market_obj)
                                
            except Exception as e:
                print(f"Error fetching markets for {event_ticker}: {e}")
            
            results.append(game_data)
            
    return results

if __name__ == "__main__":
    # Test with NFL if available, or NBA
    # Assuming KXNBAGAME is in our allow list
    TEST_TICKER = "KXNBAGAME" 
    print(f"Fetching data for {TEST_TICKER}...")
    result = asyncio.run(get_games_with_odds(TEST_TICKER))
    print(json.dumps(result, indent=4))
