import re

def parse_kalshi_ticker(ticker):
    """
    Parses a Kalshi ticker to extract details.
    Format example: KXNFL-25DEC-KCBAL
    Returns: {
        "series": "KXNFL",
        "date_code": "25DEC",
        "matchup": "KCBAL",
        "suffixes": ["KC", "BAL"] # Inferred from matchup if possible, or returned for manual matching
    }
    """
    # Simple regex for the matchup part
    # Assumes format SERIES-DATE-TEAMATEAMB
    parts = ticker.split('-')
    if len(parts) >= 3:
        series = parts[0]
        date_code = parts[1]
        matchup = parts[2]
        
        # Heuristic: Matchup is usually 2 or 3 letter codes concatenated.
        # e.g. KCBAL -> KC, BAL
        # NYGBAL -> NYG, BAL?
        # This is tricky without known codes. 
        # But wait, Kalshi market tickers have specific outcomes.
        # The user input is the SERIES ticker or the MARKET ticker?
        # "KXNFL-25DEC-KCBAL" looks like a text ticker for the event.
        # Individual markets are "KXNFL-25DEC-KCBAL-KC" (Winner market?)
        
        # Let's assume we can split the matchup string into two team codes.
        # For NFL, codes are usually 2-3 chars.
        # If length is 4 (KCBAL), split 2-2.
        # If length is 6 (SEALAR), split 3-3.
        # If 5? (SEAKC) -> SEA, KC or S, EAKC?
        
        # Better strategy: Get valid codes from the Kalshi API response later.
        # For now, just return the components.
        return {
            "series": series,
            "date": date_code,
            "matchup": matchup
        }
    return None

def generate_arbitrage_mapping(kalshi_event_data, poly_event_data):
    """
    Generates the arbitrage mapping config string.
    
    kalshi_event_data: {
        "ticker": "KXNFL-25DEC-KCBAL",
        "markets": [
            {"ticker": "KX...-KC", "outcome": "KC"}, 
            {"ticker": "KX...-BAL", "outcome": "BAL"}
        ]
    }
    
    poly_event_data: {
        "id": "...",
        "slug": "nfl-chiefs-ravens",
        "markets": [
            {"groupItemTitle": "Chiefs", "id": "123"}, # Yes ID
            {"groupItemTitle": "Ravens", "id": "456"}  # Yes ID
        ]
    }
    """
    
    mapping = {}
    
    # 1. Extract Kalshi Codes
    # We iterate Kalshi markets to find Team Codes
    k_teams = [] # [{"code": "KC", "ticker": "..."}, {"code": "BAL", "ticker": "..."}]
    
    for m in kalshi_event_data.get("markets", []):
        # Ticker: KXNFL-25DEC-KCBAL-KC
        # The suffix is the team code.
        t = m.get("ticker", "")
        parts = t.split('-')
        if parts:
            code = parts[-1] 
            k_teams.append({"code": code, "ticker": t})
            
    # 2. Extract Poly Teams
    # Poly markets usually have 'groupItemTitle' or similar for the team name.
    p_teams = [] # [{"name": "Chiefs", "id": "123"}]
    
    for m in poly_event_data.get("markets", []):
        # We need the YES token ID.
        # Usually 'id' in the market list IS the clobTokenId for Yes? NO.
        # We need to check structure. 
        # ClobTokenIds is typically [YesID, NoID].
        # If using Gamma API /events, markets have "clobTokenIds".
        
        token_ids = m.get("clobTokenIds", [])
        yes_id = token_ids[0] if len(token_ids) > 0 else None
        
        title = m.get("groupItemTitle", "") or m.get("question", "")
        # Clean title?
        p_teams.append({"name": title, "yes_id": yes_id})

    # 3. Match Suffixes
    # "KC" -> matches "Chiefs"?
    # "BAL" -> matches "Ravens"?
    
    # We need a robust matcher.
    # We can use the SLUG tokens logic from the user spec.
    slug = poly_event_data.get("slug", "").lower()
    slug_tokens = slug.split("-")
    
    # Manual map or generic matcher?
    # User spec: "Iterate tokens... if token.upper() == kalshi_suffix"
    # This implies Kalshi Suffix might be present in slug.
    # e.g. Slug: "nfl-kc-bal" -> tokens "kc", "bal".
    # Kalshi: "KC", "BAL". Match!
    
    # But what if slug is "nfl-chiefs-ravens"? "KC" != "Chiefs".
    # We might need the Map from earlier step.
    
    matched_pairs = [] # (KalshiTeam, PolyTeam)
    
    for kt in k_teams:
        k_code = kt["code"]
        found_poly = None
        
        # Try finding code in slug tokens
        if k_code.lower() in slug_tokens:
             # Find the Poly market that corresponds?
             # Slug doesn't tell us which ID is which directly, 
             # unless markets are ordered or named.
             pass
             
        # Better: Match Kalshi Code against Poly Name (heuristic or map)
        for pt in p_teams:
            p_name = pt["name"]
            # Check heuristic: p_name starts with Code? Contains Code?
            # Or use nfl_map reversed?
            
            # Simple check:
            if k_code.lower() in p_name.lower():
                found_poly = pt
                break
                
            # Use NFL Map for Nicknames
            # We can borrow the nfl_map from polymarket_manager logic or define a strict suffix map
            # User spec implied simple suffix match, but reality is "KC" != "Chiefs".
            # Mapping is needed.
            
            # Limited Map for verify
            suffix_map = {
                "KC": "Chiefs",
                "BAL": "Ravens",
                "BUF": "Bills",
                "NYJ": "Jets",
                "SEA": "Seahawks",
                "LAR": "Rams",
                "LAC": "Chargers",
                "SF": "49ers",
                "PHI": "Eagles",
                "DAL": "Cowboys",
                "NYG": "Giants",
                "WAS": "Commanders",
                "CHI": "Bears",
                "DET": "Lions",
                "GB": "Packers",
                "MIN": "Vikings",
                "ATL": "Falcons",
                "CAR": "Panthers",
                "NO": "Saints",
                "TB": "Buccaneers",
                "ARI": "Cardinals",
                "HOU": "Texans",
                "IND": "Colts",
                "JAX": "Jaguars",
                "TEN": "Titans",
                "DEN": "Broncos",
                "LV": "Raiders",
                "MIA": "Dolphins",
                "NE": "Patriots",
                "PIT": "Steelers",
                "CIN": "Bengals",
                "CLE": "Browns"
            }
            mapped_name = suffix_map.get(k_code.upper())
            if mapped_name and mapped_name.lower() in p_name.lower():
                found_poly = pt
                break
            
        if found_poly:
            matched_pairs.append((kt, found_poly))
            
    # 4. Generate Inversion Config
    # Rule:
    # K_TeamA_Yes -> P_TeamB_Yes (Opposite)
    # K_TeamA_No  -> P_TeamA_Yes (Same)
    
    # We need to know who is Team A and Team B to find "Opposite".
    # Assume 2 teams exactly.
    if len(p_teams) != 2:
        return "# Error: Poly event does not have exactly 2 teams/outcomes."
        
    for k_team, p_team in matched_pairs:
        # P_Team is the SAME side.
        # Find OPPOSITE Poly Team.
        opposite_poly = None
        for pt in p_teams:
            if pt["yes_id"] != p_team["yes_id"]:
                opposite_poly = pt
                break
        
        if opposite_poly:
            # Add to mapping
            # Key: K_Ticker-yes -> Value: Opposite_Poly_Yes_ID
            mapping[f"{k_team['ticker']}-yes"] = opposite_poly["yes_id"]
            
            # Key: K_Ticker-no -> Value: Same_Poly_Yes_ID
            mapping[f"{k_team['ticker']}-no"] = p_team["yes_id"]
            
    # Format as Python Block
    output = "NEW_PAIR = {\n"
    for k, v in mapping.items():
        output += f'    "{k}": "{v}",\n'
    output += "}"
    
    return output
