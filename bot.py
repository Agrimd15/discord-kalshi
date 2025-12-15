
import os
import discord
from discord.ext import commands, tasks
import aiohttp
import websockets
import json
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
import time

# Import our helper function
from auth import sign_request

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID")
KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini Setup
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    print("Warning: GEMINI_API_KEY not found. AI features will be disabled.")

# Rate Limiting for AI
AI_REQUEST_LIMIT = 15
ai_request_count = 0
ai_window_start = time.time()

# REST API Base URL (For balances, positions, searches)
BASE_URL = "https://api.elections.kalshi.com"

# WebSocket URL (For real-time streaming alerts)
WS_URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"

# Bot Setup
# We enable 'message_content' so the bot can read commands like "!balance"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Start the WebSocket background task
    bot.loop.create_task(order_fill_listener())

async def fetch_data(path, method="GET"):
    """Generic helper to fetch data from Kalshi API with signing."""
    try:
        headers = sign_request(method, path, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY_PATH)
    except Exception as e:
        return None, f"Error signing request: {e}"

    url = f"{BASE_URL}{path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json(), None
            else:
                error_text = await response.text()
                return None, f"Status: {response.status}\nError: {error_text}"

@bot.command(aliases=['bal'])
async def balance(ctx):
    """
    Fetches the user's current cash balance on Kalshi.
    Endpoint: GET /trade-api/v2/portfolio/balance
    """
    path = "/trade-api/v2/portfolio/balance"
    # The 'await' keyword pauses execution here until the API replies, 
    # ensuring the bot doesn't freeze for other users.
    data, error = await fetch_data(path)
    
    if error:
        await ctx.send(f"Failed to fetch balance. {error}")
        return

    # Check structure. Usually data['balance']
    cents = data.get("balance", 0)
    dollars = cents / 100
    formatted_balance = f"${dollars:,.2f}"
    await ctx.send(f"Current Balance: **{formatted_balance}**")

@bot.command(aliases=['pos'])
async def positions(ctx):
    """
    Fetches active positions (where count > 0).
    Endpoint: GET /trade-api/v2/portfolio/positions
    """
    path = "/trade-api/v2/portfolio/positions"
    data, error = await fetch_data(path)

    if error:
        await ctx.send(f"Failed to fetch positions. {error}")
        return

    # Response structure: {"positions": [...]}
    all_positions = data.get("positions", [])
    
    # Filter for active positions only
    active_positions = [p for p in all_positions if p.get('position', 0) > 0]

    if not active_positions:
        await ctx.send("No active positions found.")
        return

    embed = discord.Embed(title="📊 Active Positions", color=discord.Color.blue())
    
    for p in active_positions:
        ticker = p.get('ticker', 'Unknown')
        side = p.get('side', 'Unknown').upper()
        count = p.get('position', 0)
        # Average price is usually 'fees_paid' + 'cost_basis' logic or directly provided?
        # V2 Docs: market_exposure, realization, or sometimes fees are separate.
        # Simple lookup: 'aggr_price' or 'fees_paid' / count?
        # Let's rely on what's typically returned. 'realized_pnl', 'fees_paid', 'cost_basis'.
        # For simplicity, we'll check if 'avg_price' or similar exists, otherwise we might skip it or calc cost/count.
        # Common Kalshi field: `fees_paid` is total cost usually (excluding fees? or including?).
        # Let's assume there is no direct 'avg_price' field in some endpoints.
        # But actually, 'portfolio/positions' usually returns 'market_exposure' (cents risked).
        # Let's try to calculate: (market_exposure / count).
        
        market_exposure = p.get('market_exposure', 0)
        avg_price = (market_exposure / count) if count > 0 else 0
        
        embed.add_field(
            name=ticker, 
            value=f"Side: **{side}**\nCount: `{count}`\nAvg Price: `{avg_price:.1f}¢`", 
            inline=True
        )

    await ctx.send(embed=embed)

@bot.command()
async def search(ctx, *, query):
    """
    Search for active markets utilizing AI for semantic relevance if available.
    Endpoint: GET /trade-api/v2/markets
    """
    global ai_request_count, ai_window_start

    # Fetch more results to give the AI a good pool to choose from
    path = f"/trade-api/v2/markets?query={query}&limit=20&status=open"
    data, error = await fetch_data(path)
    
    if error:
        await ctx.send(f"Search failed. {error}")
        return

    markets = data.get("markets", [])
    if not markets:
        await ctx.send(f"No active markets found for '{query}'.")
        return

    # AI Reranking Logic
    final_markets = []
    headers_text = ""
    
    # Check if Gemini is configured and we are within rate limits
    current_time = time.time()
    if current_time - ai_window_start > 60:
        # Reset window
        ai_request_count = 0
        ai_window_start = current_time

    use_ai = False
    if GEMINI_API_KEY and ai_request_count < AI_REQUEST_LIMIT:
        use_ai = True
        ai_request_count += 1
        
        # Prepare data for AI
        market_list_str = "\n".join([f"{m['ticker']}: {m['title']}" for m in markets])
        prompt = f"""
        You are a financial assistant. 
        Select the top 5 most relevant markets for the query '{query}' from the list below.
        Return ONLY the tickers, separated by commas. Nothing else.
        
        List:
        {market_list_str}
        """
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            
            # Parse response (Comm separated tickers)
            relevant_tickers = [t.strip() for t in response.text.split(',')]
            
            # Filter markets based on AI selection, preserving order of relevance
            market_map = {m['ticker']: m for m in markets}
            for t in relevant_tickers:
                if t in market_map:
                    final_markets.append(market_map[t])
            
            # Fallback if AI hallucinates tickers or returns nothing valid
            if not final_markets:
                final_markets = markets[:5]
                
            headers_text = f"✨ Results curated by Gemini AI (Usage: {ai_request_count}/{AI_REQUEST_LIMIT})"
            
        except Exception as e:
            print(f"AI Error: {e}")
            final_markets = markets[:5]
            headers_text = "⚠️ AI failed, showing top standard results."
    
    else:
        # Fallback to standard top 5
        final_markets = markets[:5]
        if GEMINI_API_KEY:
             headers_text = f"⚠️ Rate limit reached ({ai_request_count}/{AI_REQUEST_LIMIT}), showing top standard results."

    embed = discord.Embed(
        title=f"🔎 Search Results: '{query}'", 
        description=headers_text,
        color=discord.Color.gold()
    )

    for m in final_markets:
        try:
            ticker = m.get("ticker")
            event_ticker = m.get("event_ticker", "N/A")
            title = m.get("title")
            yes_price = m.get("yes_bid")
            no_price = m.get("no_bid")

            y_txt = f"{yes_price}¢" if yes_price else "N/A"
            n_txt = f"{no_price}¢" if no_price else "N/A"

            embed.add_field(
                name=ticker,
                value=f"**{title}**\nEvent ID: `{event_ticker}`\n🟢 Yes: `{y_txt}` | 🔴 No: `{n_txt}`",
                inline=False
            )
        except Exception as e:
            print(f"Error processing a market result: {e}")
            continue
    
    await ctx.send(embed=embed)

async def order_fill_listener():
    """
    Background task to listen for 'fill' messages on Kalshi WebSocket.
    This runs parallel to the main bot loop.
    """
    # Wait until the bot is fully ready before connecting
    await bot.wait_until_ready()
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    
    if not channel:
        print(f"Error: Channel with ID {DISCORD_CHANNEL_ID} not found.")
        return

    print("Starting WebSocket Listener...")

    while not bot.is_closed():
        try:
            # 1. Sign the connection request (Handshake)
            path = "/trade-api/ws/v2"

            method = "GET"
            headers = sign_request(method, path, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY_PATH)
            
            # Note: websockets library expects headers as a dict or list of tuples.
            # Our sign_request returns a dict, which is compatible.

            async with websockets.connect(WS_URL, additional_headers=headers) as websocket:
                print("Connected to Kalshi WebSocket.")

                # 2. Subscribe to 'fill' channel
                subscribe_msg = {
                    "id": 1,
                    "cmd": "subscribe",
                    "params": {
                        "channels": ["fill"]
                    }
                }
                await websocket.send(json.dumps(subscribe_msg))
                print("Subscribed to fills.")

                # 3. Listen for messages
                async for message_str in websocket:
                    try:
                        message = json.loads(message_str)
                        
                        # Check message type
                        msg_type = message.get("type")
                        
                        if msg_type == "fill":
                            # Extract details
                            # Example payload structure from docs/experience:
                            # {"type": "fill", "msg": { "ticker": "NBX", "is_taker": true, "side": "yes", "count": 10, "price": 50, ... } }
                            # Adjust based on actual message structure.
                            
                            # Usually the data is inside 'msg' or top level depending on version.
                            # Let's inspect 'msg' if present, else use top level.
                            data = message.get("msg", message)
                            
                            ticker = data.get("ticker", "Unknown")
                            side = data.get("side", "Unknown").upper() # buy/sell or yes/no
                            action = data.get("action", side) # Sometimes 'action' is 'buy'/'sell'
                            price = data.get("price", 0) / 100 # Assuming price is in cents? Often Kalshi uses probability 1-99 or cents. 
                            # Actually price on Kalshi is typically 1-99 cents for Yes/No contracts. 
                            # If it's pure 1-99, we might not divide by 100 if we want to show '50c'.
                            # But usually formatted as $0.50 is safer or 50¢. Let's assume cents integer.
                            
                            count = data.get("count", 0)

                            # different format for price display maybe?
                            price_display = f"{data.get('price', 0)}¢"

                            embed = discord.Embed(
                                title="🚨 Order Filled!",
                                color=discord.Color.green()
                            )
                            embed.add_field(name="Ticker", value=ticker, inline=True)
                            embed.add_field(name="Action", value=action, inline=True)
                            embed.add_field(name="Price", value=price_display, inline=True)
                            embed.add_field(name="Count", value=str(count), inline=True)
                            
                            await channel.send(embed=embed)
                        
                        elif msg_type == "error":
                            print(f"WS Error: {message}")

                    except json.JSONDecodeError:
                        print(f"Failed to decode JSON: {message_str}")
                    except Exception as e:
                        print(f"Error processing message: {e}")

        except Exception as e:
            print(f"WebSocket connection lost: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not found in .env")
    else:
        bot.run(DISCORD_TOKEN)
