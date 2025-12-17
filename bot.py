import os
import discord
from discord.ext import commands
import aiohttp
from dotenv import load_dotenv

# Modules
from auth import sign_request
import series_manager
import views # Phase 3 UI
import portfolio_manager
from discord.ext import tasks
import json
import asyncio
from datetime import datetime
import re
import market_manager

# Load environment variables
from pathlib import Path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

if not os.path.exists(env_path):
    print(f"WARNING: No .env file found at {os.path.abspath(env_path)}")
    print("Please make sure you have created a .env file based on .env.example")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH")

if not DISCORD_TOKEN:
    print("ERROR: DISCORD_TOKEN is missing or None.")

BASE_URL = "https://api.elections.kalshi.com"

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
# Disable default help command to use our custom one
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# --- Helper: Fetch Data (retained for Balance/Pos) ---
async def fetch_data(path, method="GET"):
    """Generic helper to fetch data from Kalshi API with signing."""
    try:
        headers = sign_request(method, path, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY_PATH)
    except Exception as e:
        return None, f"Key Error: {e}"

    url = f"{BASE_URL}{path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json(), None
            else:
                text = await response.text()
                return None, f"Status {response.status}: {text}"

# --- Bot Events ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Kalshi Bot Ready: Phase 3 (Interactive Search).")
    
    # Start the order monitor loop if not already running
    if not order_monitor.is_running():
        order_monitor.start()

# --- Background Tasks ---
@tasks.loop(seconds=5)
async def order_monitor():
    """Checks for new fills and logs them to #order-logs."""
    channel = discord.utils.get(bot.get_all_channels(), name="order-logs")
    if not channel:
        print("Warning: #order-logs channel not found.")
        return

    # 1. Fetch recent fills
    fills = await portfolio_manager.get_recent_fills(limit=5)
    if not fills:
        return

    # 2. Load State (Last seen fill ID)
    state_file = "bot_state.json"
    last_fill_trade_id = None
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                state = json.load(f)
                last_fill_trade_id = state.get("last_fill_trade_id")
        except Exception as e:
            print(f"Error reading state file: {e}")

    # 3. Filter New Fills
    # Fills are usually returned newest first.
    # If we have a last_fill_trade_id, stop when we hit it.
    new_fills = []
    
    if last_fill_trade_id:
        for fill in fills:
            if fill.get("trade_id") == last_fill_trade_id:
                break
            new_fills.append(fill)
    else:
        # First run or no state file? 
        # User wants ONLY new trades. So we should NOT log the history.
        # We just set the state to the most recent fill (if any) and wait for next loop.
        if fills:
            # Fills are usually newest first. 
            # We save the newest ID so we only catch things AFTER this.
            latest_id = fills[0].get("trade_id")
            
            # Save State immediately
            try:
                with open(state_file, "w") as f:
                    json.dump({"last_fill_trade_id": latest_id}, f)
            except Exception as e:
                print(f"Error writing state file: {e}")
                
        # Do not process these fills
        return

    if not new_fills:
        return
        
    # Reverse to log oldest to newest
    new_fills.reverse()

    # 4. Log to Discord
    # Fetch balance once for the batch? Or per log? 
    # Fetching once is safer for rate limits and sufficiency.
    current_balance_cents = await portfolio_manager.get_balance()
    current_balance_str = f"${current_balance_cents/100:,.2f}"

    for fill in new_fills:
        # Fill object structure assumption:
        # {
        #   "trade_id": "...",
        #   "ticker": "KX...",
        #   "yes_price": 50,
        #   "count": 10,
        #   "action": "buy",
        #   "side": "yes",
        #   "created_time": "..."
        # }
        
        ticker = fill.get("ticker", "Unknown")
        side = fill.get("side", "yes").upper() # YES or NO
        action = fill.get("action", "buy").upper() # BUY or SELL
        count = fill.get("count", 0)
        # Price might be yes_price or price
        price = fill.get("yes_price") or fill.get("price") or 0

        # --- Enhanced Logic ---
        # 1. Market Info (Title, URL slugs)
        market_info = await market_manager.get_market_info(ticker)
        
        market_title = "Unknown Market"
        market_url = f"https://kalshi.com/events/{ticker}" # Fallback
        
        if market_info:
            market_title = market_info.get("title", market_title)
            subtitle = market_info.get("subtitle", "")
            if subtitle:
                market_title = f"{market_title} ({subtitle})"
                
            # Construct URL: https://kalshi.com/markets/{series_ticker}/{event_ticker}
            # API returns 'series_ticker', 'event_ticker'.
            s_ticker = market_info.get("series_ticker")
            e_ticker = market_info.get("event_ticker")

            # Fallback logic if series_ticker is missing but event_ticker exists (common in some endpoints)
            if not s_ticker and e_ticker and "-" in e_ticker:
                 # e.g. KXNBA-25DEC... -> Series is usually the prefix before the dash? 
                 # Or just try to use the event ticker as the slug if that works?
                 # Actually, Kalshi URLs often work with just /markets/{event_ticker} redirecting?
                 # Safest is to try to extract series from event if possible, or just fail gracefully.
                 # Let's try to extract from Ticker if needed.
                 pass

            if s_ticker and e_ticker:
                 market_url = f"https://kalshi.com/events/{s_ticker}/{e_ticker}"
            elif e_ticker:
                 # Try using just event ticker, often redirects or works
                 market_url = f"https://kalshi.com/events/{e_ticker}"

        # 2. Market Type
        market_type = "Moneyline"
        if "SPREAD" in ticker:
            market_type = "Spread"
        elif "TOTAL" in ticker:
            market_type = "Total"
        
        # 3. Date Parsing (Calendar Emoji)
        # Regex for '25DEC18' inside the ticker string
        # Ticker e.g. KXNFLGAME-25DEC18LASEA
        match = re.search(r'(\d{2})([A-Z]{3})(\d{2})', ticker)
        date_display = ""
        if match:
            yy, mmm, dd = match.groups()
            try:
                # Format: Dec 18
                date_display = f"{mmm.title()} {dd}"
            except:
                pass

        # Formatting
        # Action color
        color = discord.Color.green() if action == "BUY" else discord.Color.red()
        
        # Embed Title Construction
        # "Dec 18 | Los Angeles R at Seattle"
        embed_title = market_title
        if date_display:
            embed_title = f"{date_display} | {embed_title}"

        embed = discord.Embed(
            title=embed_title,
            description=f"**{action} {count}** contracts",
            color=color,
            timestamp=datetime.now() # using local time of log
        )
        
        # Row 1: Core Details
        embed.add_field(name="Details", value=f"**Type:** {market_type}\n**Ticker:** `{ticker}`", inline=False)

        # Row 2: Trade Specifics
        embed.add_field(name="Side", value=f"**{side}**", inline=True)
        embed.add_field(name="Price", value=f"{price}¢", inline=True)
        embed.add_field(name="Cost/Credit", value=f"${(count * price)/100:,.2f}", inline=True)

        # Row 3: Account Status
        embed.add_field(name="Updated Balance", value=f"**{current_balance_str}**", inline=False)
        
        # embed.add_field(name="Links", value=f"[View Market]({market_url})", inline=False) # Removed as per request (Button exists)
        
        # Button View
        view = None
        if market_url:
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="View Market", style=discord.ButtonStyle.link, url=market_url))

        await channel.send(embed=embed, view=view)
        
        # Update Loop Variable to track latest
        last_fill_trade_id = fill.get("trade_id")

    # 5. Save State
    if last_fill_trade_id:
        try:
            with open(state_file, "w") as f:
                json.dump({"last_fill_trade_id": last_fill_trade_id}, f)
        except Exception as e:
            print(f"Error writing state file: {e}")

@order_monitor.before_loop
async def before_order_monitor():
    await bot.wait_until_ready()

# --- Commands ---

# 1. SEARCH (New Interactive Flow)
@bot.command()
async def search(ctx):
    """Starts the interactive search menu."""
    # 1. Fetch active sports first
    # Uses series_manager to get the allowed list
    active_sports = await series_manager.fetch_sports_series()
    
    # 2. Check if we have data
    if not active_sports:
        await ctx.send("No active sports series found on Kalshi right now (or API error).")
        return

    # 3. Launch the View
    # active_sports is now a nested dict (Categories -> Series)
    view = views.SportsCategoryView(active_sports)
    await ctx.send("**Select a Sport Category:**", view=view)

# 2. BALANCE
@bot.command(aliases=['bal'])
async def balance(ctx):
    """Check account balance."""
    data, error = await fetch_data("/trade-api/v2/portfolio/balance")
    if error:
        await ctx.send(f"Error: {error}")
        return
    cents = data.get("balance", 0)
    await ctx.send(f"Balance: **${cents/100:,.2f}**")

# 3. POSITIONS
@bot.command(aliases=['pos'])
async def positions(ctx):
    """List active positions."""
    data, error = await fetch_data("/trade-api/v2/portfolio/positions")
    if error:
        await ctx.send(f"Error: {error}")
        return
    
    positions = [p for p in data.get("positions", []) if p.get("position", 0) > 0]
    
    if not positions:
        await ctx.send("You have no active positions.")
        return
        
    embed = discord.Embed(title="Your Active Positions", color=discord.Color.blue())
    for p in positions[:10]:
        t = p.get('ticker')
        c = p.get('position')
        exp = p.get('market_exposure', 0)
        avg = (exp / c) if c else 0
        embed.add_field(name=t, value=f"{c}x @ {avg:.1f}¢", inline=False)
        
    await ctx.send(embed=embed)

# 4. HELP
@bot.command()
async def help(ctx):
    """Shows available commands."""
    embed = discord.Embed(
        title="Welcome to KalshiBot!",
        description="Here are the commands you can use to track your portfolio and browse markets.",
        color=discord.Color.gold()
    )
    
    embed.add_field(name="`!search`", value="Browse sports and check live odds.", inline=False)
    embed.add_field(name="`!balance`", value="Check your available cash balance.", inline=False)
    embed.add_field(name="`!positions`", value="See your active trades and exposure.", inline=False)
    
    embed.set_footer(text="Trade Responsibly! • Kalshi API")
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
