
import os
import discord
from discord.ext import commands
import aiohttp
from dotenv import load_dotenv

# Modules
from auth import sign_request

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
# DISCORD_CHANNEL_ID not stricly needed for balance/pos if they are reply commands, 
# but good to keep if restricting bot to channel later.
KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH")

BASE_URL = "https://api.elections.kalshi.com"

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Helper: Fetch Data ---
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
    print("Minimal Kalshi Bot Ready: Accounts Only Mode.")

# --- Commands ---

# 1. BALANCE
@bot.command(aliases=['bal'])
async def balance(ctx):
    """Check account balance."""
    data, error = await fetch_data("/trade-api/v2/portfolio/balance")
    if error:
        await ctx.send(f"Error: {error}")
        return
    cents = data.get("balance", 0)
    await ctx.send(f"Balance: **${cents/100:,.2f}**")

# 2. POSITIONS
@bot.command(aliases=['pos'])
async def positions(ctx):
    """List active positions."""
    data, error = await fetch_data("/trade-api/v2/portfolio/positions")
    if error:
        await ctx.send(f"Error: {error}")
        return
    
    # Filter for active positions (>0)
    positions = [p for p in data.get("positions", []) if p.get("position", 0) > 0]
    
    if not positions:
        await ctx.send("You have no active positions.")
        return
        
    embed = discord.Embed(title="Your Active Positions", color=discord.Color.blue())
    for p in positions[:10]: # Limit 10
        t = p.get('ticker')
        c = p.get('position')
        # Cost basis (exposure / count)
        exp = p.get('market_exposure', 0)
        avg = (exp / c) if c else 0
        
        embed.add_field(name=t, value=f"{c}x @ {avg:.1f}¢", inline=False)
        
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
