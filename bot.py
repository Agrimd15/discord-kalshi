
import os
import discord
from discord.ext import commands
import aiohttp
import asyncio
from dotenv import load_dotenv
import datetime

# Modules
from auth import sign_request
import stream
import kalshi_hierarchy # NEW: Static Hierarchy

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH")

BASE_URL = "https://api.elections.kalshi.com"

# Setup Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- UI Views (Menus) ---

class SubMenuView(discord.ui.View):
    def __init__(self, category_name, sub_items, page=0):
        super().__init__(timeout=60)
        self.category = category_name
        self.items_map = sub_items
        self.page = page
        
        # Pagination Logic
        ITEMS_PER_PAGE = 23 # Leave 2 slots for nav
        items_list = list(sub_items.items())
        total_pages = (len(items_list) - 1) // ITEMS_PER_PAGE + 1
        
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        page_items = items_list[start:end]
        
        # Add Item Buttons
        for label, ticker in page_items:
            # Truncate label to 80 chars (Discord Limit)
            safe_label = (label[:77] + '...') if len(label) > 80 else label
            self.add_item(SubMenuButton(safe_label, ticker))
            
        # Add Nav Buttons
        if page > 0:
            self.add_item(NavButton(category_name, sub_items, page - 1, "⬅️ Prev"))
        if page < total_pages - 1:
            self.add_item(NavButton(category_name, sub_items, page + 1, "Next ➡️"))

class NavButton(discord.ui.Button):
    def __init__(self, category, items, target_page, label):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.category = category
        self.items = items
        self.target_page = target_page

    async def callback(self, interaction: discord.Interaction):
        # view = SubMenuView(self.category, self.items, self.target_page)
        # await interaction.response.edit_message(view=view)
        # Better: Send new ephemeral to avoid clearing history? 
        # Actually edit is cleaner for pagination.
        view = SubMenuView(self.category, self.items, self.target_page)
        await interaction.response.edit_message(view=view)

class SubMenuButton(discord.ui.Button):
    def __init__(self, label, ticker):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.ticker = ticker

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await perform_search(interaction.channel, self.ticker, f"Menu: {self.label}")

class MainMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        # Add buttons for Top Categories
        for cat in kalshi_hierarchy.HIERARCHY.keys():
            self.add_item(MainMenuButton(cat))

class MainMenuButton(discord.ui.Button):
    def __init__(self, label):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        # Determine sub-items
        sub_items = kalshi_hierarchy.HIERARCHY.get(self.label, {})
        if not sub_items:
            await interaction.response.send_message(f"No items found for {self.label}", ephemeral=True)
            return
            
        view = SubMenuView(self.label, sub_items)
        await interaction.response.send_message(f"📂 **{self.label}** - Select a Series:", view=view, ephemeral=True)

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
    # Stream is disabled by default
    # bot.loop.create_task(stream.start_stream(bot, DISCORD_CHANNEL_ID, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY_PATH))

# --- Core Search Logic (Reusable) ---
async def perform_search(channel, series_ticker, query_context):
    """
    Executes the API fetch and Embed display for a known series ticker.
    Used by !search command AND Menu Buttons.
    """
    params = f"status=open&series_ticker={series_ticker}"
    path = f"/trade-api/v2/events?{params}"
    
    data, error = await fetch_data(path)
    if error:
        await channel.send(f"API Error: {error}")
        return

    events = data.get("events", [])
    if not events:
        await channel.send(f"No active events found for **{series_ticker}**.")
        return

    # Sort by Start Time (ISO 8601 string sort works for date)
    events.sort(key=lambda x: x.get("start_time", "9999"))
    
    # Top 10 Only
    top_events = events[:10]

    embed = discord.Embed(
        title=f"Active Markets: {series_ticker} ({query_context})",
        description=f"Found {len(events)} events (Showing top {len(top_events)}).",
        color=0x00FF00
    )
    
    for e in top_events:
        e_title = e.get("title", "Unknown")
        e_ticker = e.get("event_ticker", "ID")
        start_time = e.get("start_time", "")
        
        # Format Date
        date_str = "TBD"
        if start_time:
            try:
                dt = datetime.datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                # Convert to shorter format e.g. "Dec 25 20:00"
                date_str = dt.strftime("%b %d, %H:%M UTC")
            except ValueError:
                date_str = start_time
        
        # Get Prices from first Market
        markets = e.get("markets", [])
        price_line = ""
        if markets:
            m = markets[0]
            yes_ask = m.get("yes_ask", "N/A")
            no_ask = m.get("no_ask", "N/A")
            price_line = f"Yes: {yes_ask}¢ | No: {no_ask}¢"
        
        embed.add_field(
            name=f"📅 {date_str} | {e_title}",
            value=f"ID: `{e_ticker}`\n💰 {price_line}" if price_line else f"ID: `{e_ticker}`",
            inline=False
        )

    await channel.send(embed=embed)


# --- Commands ---

# 1. SEARCH (Menu or Direct)
@bot.command()
async def search(ctx, *, query=None):
    """
    Interactive Search.
    No args -> Shows Main Menu.
    Args -> Tries to match known series.
    """
    if not query:
        # Show Menu
        view = MainMenuView()
        await ctx.send("🔎 **Kalshi Market Menu**\nSelect a category to browse:", view=view)
        return

    # Try mapping
    ticker = kalshi_hierarchy.get_ticker_by_name(query)
    if ticker:
        await perform_search(ctx.channel, ticker, query)
    else:
        await ctx.send(f"Couldn't map '{query}' to a series. Try `!search` (no args) to use the menu.")

# 2. BALANCE
@bot.command(aliases=['bal'])
async def balance(ctx):
    data, error = await fetch_data("/trade-api/v2/portfolio/balance")
    if error:
        await ctx.send(f"Error: {error}")
        return
    cents = data.get("balance", 0)
    await ctx.send(f"Balance: **${cents/100:,.2f}**")

# 3. POSITIONS
@bot.command(aliases=['pos'])
async def positions(ctx):
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

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
