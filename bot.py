
import os
import discord
from discord.ext import commands
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

# Global Hierarchy Cache (Dynamic)
hierarchy_cache = {}

# Bot Setup
# We enable 'message_content' so the bot can read commands like "!balance"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # await refresh_hierarchy() # Disabled for stability
    # Start the WebSocket background task
    # bot.loop.create_task(order_fill_listener())

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

async def refresh_hierarchy():
    """
    Fetches all series from Kalshi, organizes them by Category -> Tag,
    and builds the global hierarchy_cache. This enables fast, dynamic menu browsing.
    """
    global hierarchy_cache
    print("Building dynamic hierarchy from Kalshi API...")
    data, error = await fetch_data("/trade-api/v2/series")
    if error:
         print(f"Hierarchy Error: {error}")
         return

    tree = {}
    for s in data.get("series", []):
         category = s.get("category", "Uncategorized")
         tags = s.get("tags") or ["General"]
         tag = tags[0] if tags else "General"
         
         if category not in tree: tree[category] = {}
         if tag not in tree[category]: tree[category][tag] = {}
         
         # Use Title as Label (Truncated for Discord Buttons)
         label = s.get("title", s["ticker"])[:79]
         ticker = s.get("ticker", "")
         
         tree[category][tag][label] = ticker
         
         # Auto-add Futures view for Games (Dynamic #ALL logic)
         if "game" in s.get("title", "").lower() or "game" in ticker.lower():
              f_label = f"{label} (All/Futures)"[:79]
              tree[category][tag][f_label] = ticker + "#ALL"
              
    hierarchy_cache = tree
    print(f"Hierarchy built with {len(tree)} categories.")

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
async def commands(ctx):
    """
    Lists all available commands.
    """
    embed = discord.Embed(
        title="🤖 KalshiBot Commands",
        description="Here are the commands you can use:",
        color=discord.Color.blue()
    )
    
    # 1. Search (Core)
    embed.add_field(
        name="🔍 Market Search",
        value="`!search <query>`: Smart search (e.g. `!search nfl`, `!search politics`)\n`!search sports`: Open the Browse Menu",
        inline=False
    )
    
    # 2. Portfolio / Account
    embed.add_field(
        name="💰 Account & Trading",
        value="`!balance` (or `!bal`): Check your cash balance.\n`!positions` (or `!pos`): View active positions.",
        inline=False
    )
    
    # 3. Meta
    embed.add_field(
        name="ℹ️ Other",
        value="`!commands`: Shows this help message.",
        inline=False
    )
    
    embed.set_footer(text="Tip: Start with !search sports to explore categories!")
    await ctx.send(embed=embed)

# --- Recursive Hierarchy View ---

class HierarchyView(discord.ui.View):
    def __init__(self, ctx, hierarchy_data, path_label="Menu"):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.hierarchy_data = hierarchy_data
        self.path_label = path_label
        
        # Determine if current level is Keys (Sub-menus) or Strings (Tickers)
        # If dict, show keys as buttons to drill down.
        # If string, we shouldn't be here (leaf node).
        
        for key, value in hierarchy_data.items():
            if isinstance(value, dict):
                # Sub-menu button
                self.add_item(HierarchyButton(label=key, value=value, is_leaf=False, ctx=ctx, parent_view=self))
            else:
                # Leaf button (Ticker)
                self.add_item(HierarchyButton(label=key, value=value, is_leaf=True, ctx=ctx, parent_view=self))

class HierarchyButton(discord.ui.Button):
    def __init__(self, label, value, is_leaf, ctx, parent_view):
        style = discord.ButtonStyle.green if is_leaf else discord.ButtonStyle.secondary
        super().__init__(label=label, style=style)
        self.target_value = value
        self.is_leaf = is_leaf
        self.ctx = ctx
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This menu is not for you.", ephemeral=True)
            return

        if self.is_leaf:
            # IT'S A TICKER! Search it.
            await interaction.response.defer()
            await interaction.message.edit(content=f"🔎 Loading Markets for **{self.label}** ({self.target_value})...", view=None)
            await fetch_and_display_markets(self.ctx, self.target_value, f"Menu Selection: {self.label}", interaction.message)
        else:
            # IT'S A SUB-MENU! Drill down.
            await interaction.response.defer()
            new_view = HierarchyView(self.ctx, self.target_value, path_label=f"{self.parent_view.path_label} > {self.label}")
            await interaction.message.edit(content=f"📂 **{self.parent_view.path_label} > {self.label}**", view=new_view)

# --- Helper to Load Hierarchy ---
def load_hierarchy(query):
    import difflib
    
    # Use Dynamic Cache
    data = hierarchy_cache
    if not data:
        return None
        
    query_str = query.lower()

    # 1. Exact/Fuzzy Keys (Menu Traversal)
    # Check Categories
    cats = list(data.keys())
    # Exact
    if query_str in [c.lower() for c in cats]:
        for c in cats:
            if c.lower() == query_str: return data[c]
    # Fuzzy
    match_cat = difflib.get_close_matches(query_str, cats, n=1, cutoff=0.6)
    if match_cat: return data[match_cat[0]]

    # Check Tags (Sub-level)
    for cat in data:
        tags = list(data[cat].keys())
        if query_str in [t.lower() for t in tags]:
             for t in tags:
                 if t.lower() == query_str: return data[cat][t]
        
        match_tag = difflib.get_close_matches(query_str, tags, n=1, cutoff=0.6)
        if match_tag: return data[cat][match_tag[0]]

    # 2. Leaf Search (Smart Ticker/Title Match) - "The Fix"
    # Search all items to find best match across entire API
    
    potential_matches = []
    
    for cat in data:
        for tag in data[cat]:
            for label, ticker in data[cat][tag].items():
                # Score Candidate
                score = 0
                
                t_raw = ticker.lower()
                t_clean = t_raw.replace("kx", "").replace("#all", "")
                l_clean = label.lower()
                
                # A. Exact Substring in Ticker (Strongest)
                # "nfl" in "nflgame"
                if query_str in t_clean:
                    score = 1.0
                
                # B. Exact Substring in Title
                elif query_str in l_clean:
                    score = 0.9
                
                # C. Fuzzy Matches
                else:
                    # Ticker fuzzy (Good for "nfll" -> "nflgame")
                    r_tick = difflib.SequenceMatcher(None, query_str, t_clean).ratio()
                    # Title fuzzy
                    r_title = difflib.SequenceMatcher(None, query_str, l_clean).ratio()
                    
                    score = max(r_tick, r_title)
                
                # Filter weak matches
                if score > 0.5:
                    potential_matches.append((score, ticker))

    if potential_matches:
        # Sort by Score Descending -> Pick Best
        potential_matches.sort(key=lambda x: x[0], reverse=True)
        return potential_matches[0][1] # Return Ticker String

    return None

# --- Helper to Display Markets (Used by both auto-select and button click) ---
async def fetch_and_display_markets(ctx, series_ticker, query, message_to_edit=None):
    import datetime
    import re
    
    # Check for #ALL flag (Exempt from filters)
    force_all = False
    if series_ticker.endswith("#ALL"):
        series_ticker = series_ticker.replace("#ALL", "")
        force_all = True

    path = f"/trade-api/v2/markets?series_ticker={series_ticker}&status=open"
    
    data, error = await fetch_data(path)
    if error:
        msg = f"❌ Error fetching markets: {error}"
        if message_to_edit: await message_to_edit.edit(content=msg)
        else: await ctx.send(msg)
        return

    markets = data.get("markets", [])
    if not markets:
         msg = f"❌ No open markets found in series `{series_ticker}`."
         if message_to_edit: await message_to_edit.edit(content=msg)
         else: await ctx.send(msg)
         return

    # --- Robust Filtering Logic ---
    live_markets = []
    now_utc = datetime.datetime.utcnow().replace(tzinfo=None)
    cutoff_time = now_utc + datetime.timedelta(hours=36) # Broad window for "Imminent"
    
    seen_events = set()
    
    def parse_ticker_date(ticker):
        match = re.search(r"-(\d{2})([A-Z]{3})(\d{2})", ticker)
        if match:
            yy, m_str, dd = match.groups()
            year = 2000 + int(yy)
            day = int(dd)
            months = {"JAN":1, "FEB":2, "MAR":3, "APR":4, "MAY":5, "JUN":6, 
                      "JUL":7, "AUG":8, "SEP":9, "OCT":10, "NOV":11, "DEC":12}
            month = months.get(m_str, 0)
            if month:
                try: return datetime.datetime(year, month, day)
                except: return None
        return None

    # Determine if this is a "Game" series that should be filtered by date
    # HEURISTIC: Filter filter ONLY IF:
    # 1. "GAME" in ticker
    # 2. NOT force_all (Futures)
    is_time_sensitive_series = "GAME" in series_ticker.upper() and not force_all

    for m in markets:
        event_id = m.get("event_ticker", "")
        if event_id in seen_events:
            continue
            
        market_date = parse_ticker_date(event_id)
        
        should_show = True
        
        # Apply Time Filter
        if is_time_sensitive_series and market_date:
            if market_date > cutoff_time:
                should_show = False
        
        if should_show:
            m['_sort_date'] = market_date if market_date else datetime.datetime.max
            live_markets.append(m)
            seen_events.add(event_id)
    
    # Sort: Earliest games first. Futures (max date) last.
    live_markets.sort(key=lambda x: x['_sort_date'])

    # Footer with AI Usage if available
    global ai_request_count
    
    # User requested AI Usage counter primarily
    current_time_str = datetime.datetime.now().strftime('%H:%M:%S')
    footer_text = f"Series: {series_ticker} | AI Usage: {ai_request_count}/{AI_REQUEST_LIMIT} | {current_time_str}"
    
    if not live_markets:
        embed = discord.Embed(
            title=f"🔴 Active Search: '{query}'", 
            description=f"**No active matches for {series_ticker} in next 36h.**",
            color=discord.Color.red()
        )
        embed.set_footer(text=footer_text)
        if message_to_edit: await message_to_edit.edit(content="", embed=embed)
        else: await ctx.send(embed=embed)
        return
        
    embed = discord.Embed(
        title=f"🟢 Active Markets: {series_ticker}",
        description=f"Found {len(live_markets)} active events.",
        color=discord.Color.green()
    )
    
    # Increased Limit to 10
    display_limit = 10
    for m in live_markets[:display_limit]:
            # Format date for display if available
            date_str = ""
            if '_sort_date' in m and m['_sort_date'] != datetime.datetime.max:
                date_str = f" | 📅 {m['_sort_date'].strftime('%b %d')}"
            
            embed.add_field(
            name=f"{m.get('title')}{date_str}",
            value=f"ID: `{m.get('event_ticker')}`\nYes: `{m.get('yes_bid', 'N/A')}¢` | No: `{m.get('no_bid', 'N/A')}¢`",
            inline=False
        )
    
    embed.set_footer(text=footer_text)
    
    if message_to_edit: await message_to_edit.edit(content="", embed=embed)
    else: await ctx.send(embed=embed)


@bot.command()
async def search(ctx, *, query):
    """
    Search is currently disabled for maintenance.
    """
    await ctx.send("🚧 **Search is temporarily disabled for maintenance.**\nPlease try `!balance` or `!positions` instead.")
    return


async def order_fill_listener():
    """
    Background task to listen for 'fill' messages on Kalshi WebSocket.
    This runs parallel to the main bot loop.
    """
    # Wait until the bot is fully ready before connecting
    await bot.wait_until_ready()
    await bot.wait_until_ready()
    
    try:
        channel = await bot.fetch_channel(DISCORD_CHANNEL_ID)
    except Exception as e:
        print(f"Error fetching channel {DISCORD_CHANNEL_ID}: {e}")
        return

    print(f"WebSocket Listener attached to channel: {channel.name}")


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
