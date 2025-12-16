import os
import discord
from discord.ext import commands
import aiohttp
from dotenv import load_dotenv

# Modules
from auth import sign_request
import series_manager
import views # Phase 3 UI

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH")
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
        await ctx.send("⚠️ No active sports series found on Kalshi right now (or API error).")
        return

    # 3. Launch the View
    # active_sports is now a nested dict (Categories -> Series)
    view = views.SportsCategoryView(active_sports)
    await ctx.send("🔍 **Select a Sport Category:**", view=view)

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
        title="🤖 Welcome to KalshiBot!",
        description="Here are the commands you can use to track your portfolio and browse markets.",
        color=discord.Color.gold()
    )
    
    embed.add_field(name="🔎 `!search`", value="Browse sports and check live odds.", inline=False)
    embed.add_field(name="💰 `!balance`", value="Check your available cash balance.", inline=False)
    embed.add_field(name="📊 `!positions`", value="See your active trades and exposure.", inline=False)
    
    embed.set_footer(text="Trade Responsibly! • Kalshi API")
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
