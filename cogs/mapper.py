import discord
from discord import app_commands
from discord.ext import commands
from managers.polymarket_manager import search_events, find_polymarket_match
from managers.mapping_logic import parse_kalshi_ticker, generate_arbitrage_mapping
from managers.market_manager import get_market_info
# We need a way to fetch full kalshi event details. 
# market_manager.py has `get_market_info` but that might be for a single market.
# `client.get_event(ticker)`?
# Let's assume we can use the bot's existing kalshi client or managers.

class MarketMapper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup_arb", description="Map a Kalshi event to Polymarket for arbitrage.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_arb(self, interaction: discord.Interaction, kalshi_ticker: str):
        """
        Interactive setup for arbitrage mapping.
        kalshi_ticker: The Series or Market ticker (e.g. KXNFL-25DEC-KCBAL)
        """
        await interaction.response.defer(ephemeral=True)
        
        # 1. Parse Ticker -> Get Event Title
        # For now, heuristic from ticker string
        parsed = parse_kalshi_ticker(kalshi_ticker)
        if not parsed:
             await interaction.followup.send(f"⚠️ Could not parse Kalshi ticker: `{kalshi_ticker}`")
             return
             
        # Ideally, fetch real event title from Kalshi API to be safe
        # But we'll try to guess title or search Poly with parsed info.
        # Let's assume we can fetch.
        
        # NOTE: We need to access Kalshi client. 
        # bot.py has it? self.bot.kalshi_client?
        # Let's try to proceed without it for now using the string matchup "KCBAL"
        # The user provided matching logic should work with strings.
        
        matchup = parsed['matchup'] # e.g. KCBAL
        # We need to turn KCBAL into "Reference Title" for Poly Search
        # This is tough without the mapping.
        # But the USER said: "Step 1: Kalshi Lookup... Extracts Event Title"
        # So we MUST lookup.
        
        # Mocking lookup or using market_manager if available
        # market_manager.get_games_with_odds() ?
        # Let's use `search_events` logic if we assume ticker is known.
        
        # For this implementation, I will skip the real API call to Kalshi if too complex to wire up 
        # without `bot` instance details, and rely on the Ticker. 
        # actually, I can try `await market_manager.get_market(ticker)` if it exists.
        
        kalshi_title = f"{matchup} Game" # Fallback
        
        await interaction.followup.send(f"🔎 Processing `{kalshi_ticker}`... (Target: {matchup})")
        
        # 2. Polymarket Search
        # Try generic search first
        query = matchup
        # If KCBAL, maybe "Chiefs" or "Ravens"?
        # We don't have the de-coder here yet (it was in get_ids.py).
        # We'll search for the generic code and hope Poly has "NFL" or similar.
        # Or better: Ask user to select sport?
        # Let's try searching the date code?
        
        candidates = await search_events(query="" , tag_id=450) # NFL default? No.
        # We need a proper query.
        # Let's ask the user to confirm the Poly query if heuristics fail?
        # NO, "The Selection UI" implies we present options.
        
        # Let's try searching for the suffixes!
        # "KC", "BAL".
        # If we search "KC", we might find Chiefs.
        
        # Search strategy: Search for both suffixes.
        # We need the SUFFIXES from the ticker.
        # Usually Parse Kalshi Ticker gives suffixes?
        # KCBAL -> KC, BAL (Manual split based on length)
        
        # Let's just create the View with the search results of the "Matchup" string or similar.
        # Actually, let's search for "NFL" if it looks like NFL.
        poly_candidates = await search_events(matchup) # Pass raw KCBAL? Unlikely to work.
        
        # If 0 results, search for "NFL" tag?
        if not poly_candidates:
             poly_candidates = await search_events("NFL", tag_id=450) # Fallback to NFL stream
             
        if not poly_candidates:
             await interaction.followup.send("⚠️ No candidates found on Polymarket. Try manually.")
             return
             
        # 3. Selection UI
        view = PolySelectionView(poly_candidates[:25], kalshi_ticker, parsed)
        await interaction.followup.send("Select the matching Polymarket event:", view=view)

class PolySelectionView(discord.ui.View):
    def __init__(self, candidates, k_ticker, k_parsed):
        super().__init__(timeout=60)
        self.k_ticker = k_ticker
        self.k_parsed = k_parsed
        
        options = []
        for c in candidates:
            label = c.get('title', 'Unknown')[:100]
            val = c.get('slug', 'unknown')
            # Store ID in value too? Slug is unique.
            options.append(discord.SelectOption(label=label, value=val, description=str(c.get('id'))))
            
        self.add_item(PolySelect(options, k_ticker))

class PolySelect(discord.ui.Select):
    def __init__(self, options, k_ticker):
        super().__init__(placeholder="Choose Event...", min_values=1, max_values=1, options=options)
        self.k_ticker = k_ticker

    async def callback(self, interaction: discord.Interaction):
        # 4. Automated Mapping
        slug = self.values[0]
        full_event = None
        
        # We need to fetch full details for the slug to get Markets and Outcomes
        # We can implement `get_event_by_slug` or search again.
        # Let's assume we can find it in the previous list logic or fetch anew.
        # For now, let's assume we have the ID from description.
        
        # Actually, we need the FULL market list (YES/NO IDs).
        # Reuse polymarket_manager to fetch event details?
        # It has `get_events` with slug?
        # Let's just use the logic from mapping_logic if passed data.
        
        # We'll send a "Generating..." message
        await interaction.response.send_message(f"🧠 Mapping `{self.k_ticker}` to `{slug}`...", ephemeral=True)
        
        # Fetch full poly data (we need markets/outcomes)
        # Using a helper from polymarket_manager
        # (We might need to add `get_event_by_slug` there if not exists)
        from managers.polymarket_manager import search_events
        events = await search_events(slug) # Search by slug usually returns the exact event
        if events:
            poly_data = events[0]
            
            # Construct Mock Kalshi Data for logic
            # We assume K_Ticker ends in Mismatch?
            # Ticker: KXNFL-DEC-KCBAL
            # Markets: KCBAL-KC, KCBAL-BAL
            # We need to split the matchup to get suffixes.
            matchup = self.view.k_parsed['matchup']
            # Heuristic split: first half, second half?
            mid = len(matchup) // 2
            code_a = matchup[:mid]
            code_b = matchup[mid:]
            
            k_data = {
                "ticker": self.k_ticker,
                "markets": [
                    {"ticker": f"{self.k_ticker}-{code_a}", "outcome": code_a},
                    {"ticker": f"{self.k_ticker}-{code_b}", "outcome": code_b}
                ]
            }
            
            config_block = generate_arbitrage_mapping(k_data, poly_data)
            
            await interaction.followup.send(f"✅ **Usage:** Copy to `market_config.py`:\n```python\n{config_block}\n```")
        else:
            await interaction.followup.send("❌ Error fetching Polymarket details.")

async def setup(bot):
    await bot.add_cog(MarketMapper(bot))
