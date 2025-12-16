
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



# Whitelist of Supported Series
# categorized for UI Hierachy
# Whitelist of Supported Series
# categorized for UI Hierachy
# Structure: Category -> League Name -> { "moneyline": Ticker, "spread": Ticker, "total": Ticker }
ALLOWED_SERIES = {
    "Football": {
        "NFL": {
            "moneyline": "KXNFLGAME",
            "spread": "KXNFLSPREAD",
            "total": "KXNFLTOTAL"
        },
        "College Football": {
            "moneyline": "KXNCAAFGAME",
            "spread": "KXNCAAFSPREAD",
            "total": "KXNCAAFTOTAL"
        }
    },
    "Basketball": {
        "NBA": {
            "moneyline": "KXNBAGAME",
            "spread": "KXNBASPREAD",
            "total": "KXNBATOTAL"
        },
        "College (Men)": {
            "moneyline": "KXNCAAMBGAME",
            "spread": "KXNCAAMBSPREAD",
            "total": "KXNCAAMBTOTAL"
        },
        "College (Women)": {
            "moneyline": "KXNCAAWBGAME",
            "spread": "KXNCAAWBSPREAD",
            "total": "KXNCAAWBTOTAL"
        }
    },
    "Hockey": {
        "NHL": {
            "moneyline": "KXNHLGAME",
            "spread": "KXNHLSPREAD",
            "total": "KXNHLTOTAL"
        }
    }
}

async def fetch_sports_series():
    """
    Returns the grouped hierarchy directly (Static for now, but scalable).
    Verifies they exist? We can skip verification for speed since we hardcoded "Allowed".
    Or we can fetch to ensure they are active.
    For this "No AI" approach, static is safer and faster.
    """
    # Simply return the static map.
    # If dynamic fetching is strictly required to check 'active' status, we can do it.
    # But usually these high level series are always 'active' even if empty events.
    return ALLOWED_SERIES


if __name__ == "__main__":
    result = asyncio.run(fetch_sports_series())
    print(json.dumps(result, indent=4))
