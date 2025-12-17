import aiohttp
import os
import asyncio
from dotenv import load_dotenv
from .auth import sign_request

# Load environment variables
load_dotenv()

KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH")
BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

async def get_recent_fills(limit=10):
    """
    Fetches the recent fills from the portfolio.
    """
    # API Endpoint Suffix
    # API Endpoint Suffix
    endpoint = "/portfolio/fills"
    params = {"limit": limit}
    
    # We must handle the case where keys are missing to avoid crashing if run locally without env
    if not KALSHI_KEY_ID or not KALSHI_PRIVATE_KEY_PATH:
        print("Warning: Missing Kalshi credentials. Cannot fetch fills.")
        return []

    # Full path for signing (must include /trade-api/v2)
    sign_path = f"/trade-api/v2{endpoint}"

    try:
        headers = sign_request("GET", sign_path, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY_PATH)
    except Exception as e:
        print(f"Error signing request: {e}")
        return []

    # URL construction
    # BASE_URL includes /trade-api/v2, so we just append endpoint
    url = f"{BASE_URL}{endpoint}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Response expected: {"fills": [...]}
                    return data.get("fills", [])
                else:
                    text = await resp.text()
                    print(f"Error fetching fills: {resp.status} {text}")
                    return []
        except Exception as e:
            print(f"Exception fetching fills: {e}")
            return []

async def get_balance():
    """
    Fetches the current available balance.
    """
    endpoint = "/portfolio/balance"
    sign_path = f"/trade-api/v2{endpoint}"
    
    if not KALSHI_KEY_ID or not KALSHI_PRIVATE_KEY_PATH:
        return 0

    try:
        headers = sign_request("GET", sign_path, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY_PATH)
    except Exception as e:
        print(f"Error signing request: {e}")
        return 0

    url = f"{BASE_URL}{endpoint}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("balance", 0)
                else:
                    print(f"Error fetching balance: {resp.status}")
                    return 0
        except Exception as e:
            print(f"Exception fetching balance: {e}")
            return 0

if __name__ == "__main__":
    fills = asyncio.run(get_recent_fills())
    print(fills)
