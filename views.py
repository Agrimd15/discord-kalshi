
import discord
import series_manager
import market_manager
from datetime import datetime

# --- Level 0: Sport Category Selection ---
class SportsCategoryView(discord.ui.View):
    def __init__(self, categories):
        super().__init__(timeout=60)
        self.categories = categories
        
        # Add a button for each major category (Football, Basketball, etc.)
        for category_name in categories.keys():
            self.add_item(CategoryButton(category_name, categories[category_name]))

class CategoryButton(discord.ui.Button):
    def __init__(self, label, sub_map):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.sub_map = sub_map # The dictionary of series for this category
        
    async def callback(self, interaction: discord.Interaction):
        # Transition to Series Selection
        await interaction.response.defer()
        view = SeriesSelectionView(self.label, self.sub_map)
        await interaction.edit_original_response(content=f"**{self.label}**: Select a League", view=view)

# --- Level 1: Series Selection ---
class SeriesSelectionView(discord.ui.View):
    def __init__(self, category_name, sub_map):
        super().__init__(timeout=60)
        self.category_name = category_name
        self.sub_map = sub_map
        
        # sub_map is { "NBA": { "moneyline": "...", ... } }
        for series_name, tickers_dict in sub_map.items():
            self.add_item(SeriesButton(series_name, tickers_dict))
            

class SeriesButton(discord.ui.Button):
    def __init__(self, label, tickers_dict):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.tickers_dict = tickers_dict
        
    async def callback(self, interaction: discord.Interaction):
        # Transition to Market Type
        await interaction.response.defer()
        view = MarketTypeView(self.tickers_dict, self.label) 
        await interaction.edit_original_response(content=f"**{self.label}**: Select Market Type", view=view)

# --- Level 2: Market Type Selection ---
class MarketTypeView(discord.ui.View):
    def __init__(self, tickers_dict, sport_name):
        super().__init__(timeout=60)
        self.tickers_dict = tickers_dict
        self.sport_name = sport_name
        
        # Check available types to enable/disable buttons?
        # Or just show all standard ones.
        self.add_item(MarketTypeButton("Moneyline", "moneyline", "🏆"))
        self.add_item(MarketTypeButton("Spreads", "spread", "📊"))
        self.add_item(MarketTypeButton("Totals", "total", "🔢"))

class MarketTypeButton(discord.ui.Button):
    def __init__(self, label, market_type, emoji):
        super().__init__(label=label, emoji=emoji, style=discord.ButtonStyle.success)
        self.market_type = market_type
        
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        
        # Get specific ticker
        ticker = view.tickers_dict.get(self.market_type)
        if not ticker:
             await interaction.response.send_message(f"Sorry, **{self.market_type.title()}** markets are not mapped for {view.sport_name}.", ephemeral=True)
             return

        await interaction.response.defer()
        await show_results(interaction, ticker, view.sport_name, self.market_type)

# --- Level 3: Results Display ---
async def show_results(interaction, ticker, sport_name, market_type):
    games = await market_manager.get_games_with_odds(ticker)
    
    if isinstance(games, str):
        await interaction.edit_original_response(content=f"Error: {games}", view=None)
        return
        
    filtered_events = []
    
    # Pre-calculate Date limit (48 hours)
    import re
    from datetime import timedelta
    now = datetime.now() 
    # Note: Server time might differ from Game time (US/ET). 
    # We'll be lenient, maybe 3-4 days to be safe given TZ diffs, but user asked for 48h.
    # Ticker format: YYMMMDD -> 25DEC15.
    
    cutoff = now + timedelta(days=3) # Using 3 days to catch "next 48h" fully including today remainder
    
    processed_games = []

    for g in games:
        # Check markets
        markets = g["markets"].get(market_type, [])
        if not markets:
            continue
            
        # Parse Date from first market ticker to filter Event
        # Ticker e.g. KXNBAGAME-25DEC15MEMLAC...
        # We need to find the date part.
        m_ticker = markets[0].get("ticker", "")
        # Regex for '25DEC15' inside the string
        match = re.search(r'(\d{2})([A-Z]{3})(\d{2})', m_ticker)
        
        game_date = datetime.max # Default to far future if no date found
        date_str_display = ""
        
        if match:
            yy, mmm, dd = match.groups()
            try:
                # Parse "25Dec15"
                dt_str = f"{yy}{mmm}{dd}"
                game_date = datetime.strptime(dt_str, "%y%b%d")
                
                # Format for display: Dec 15
                date_str_display = f"📅 {mmm.title()} {dd}"
            except ValueError:
                pass
        
        # Filter Logic (Next ~48h/72h)
        # Check if game_date is within range. Allow Today/Yesterday (active)
        # Ignoring past games? API status=open means incomplete.
        # Strict "upcoming" filter:
        if game_date > cutoff:
            continue # Skip far future
            
        processed_games.append({
            "game": g,
            "markets": markets,
            "sort_date": game_date,
            "date_display": date_str_display
        })
        
    # Sort by Date
    processed_games.sort(key=lambda x: x["sort_date"])
    
    if not processed_games:
        await interaction.edit_original_response(content=f"No active **{market_type}** markets found in the next 48h for {sport_name}.", view=None)
        return
        
    embed = discord.Embed(
        title=f"{sport_name} - {market_type.title()} (Next 48h)",
        color=discord.Color.brand_green()
    )
    
    count = 0
    for item in processed_games:
        if count >= 4: break # Safety Cap for Total Embed Size (6000 chars). 4-5 games max with 5 markets each.
        
        g = item["game"]
        markets = item["markets"]
        date_str = item["date_display"]
        title = g.get("event_title")

        # Deduplicate Markets for Display
        # Group by Base ID only for Moneyline to avoid redundancy (showing both Team A and Team B sides)
        # For Spreads/Totals, multiple markets exist (different lines), so we show them all (capped).
        
        displayed_base_ids = set()
        
        market_lines_str = []
        
        # Sort markets by useful value? E.g. spread value?
        # For now, API order is usually fine.
        
        limit_per_game = 5 if market_type != "moneyline" else 2
        
        for m in markets[:limit_per_game]: # Safety cap to avoid Embed Field limit (1024 chars)
            raw_ticker = m.get("ticker", "")
            
            # Extract Base ID (Remove suffix)
            if "-" in raw_ticker:
                base_id = raw_ticker.rsplit("-", 1)[0]
            else:
                base_id = raw_ticker
            
            # Only deduplicate strict Base ID for Moneyline
            if market_type == "moneyline":
                if base_id in displayed_base_ids:
                    continue # Skip duplicate side
                displayed_base_ids.add(base_id)
            
            # Format
            header = m.get("title")
            sub = m.get("subtitle", "")
            if sub:
                header = f"{header} ({sub})"
            
            # Add Date to Header only for Moneyline? No, we moved it to Field Name.
            
            yes_p = m.get("yes_bid")
            no_p = m.get("no_bid")
            
            # ID Display Logic
            # Moneyline: Generic Event ID (Base ID)
            # Spreads/Totals: Full Market ID (Specific Ticker)
            display_id = base_id if market_type == "moneyline" else raw_ticker
            
            line_str = f"**{header}**\n**ID:** `{display_id}`\n**Yes:** {yes_p}¢ | **No:** {no_p}¢"
            market_lines_str.append(line_str)
            
            
        if market_lines_str:
            # Add Date to Field Name
            field_name = title
            if date_str:
                field_name = f"{title} | {date_str}"
            
            # Use double newline for readability as requested
            embed.add_field(name=field_name, value="\n\n".join(market_lines_str), inline=False)
            count += 1
        
    await interaction.edit_original_response(content=None, embed=embed, view=None)
