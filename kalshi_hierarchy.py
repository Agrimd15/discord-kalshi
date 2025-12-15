# Auto-generated Sports Hierarchy
HIERARCHY = {
    "Baseball": {
        "Pro Baseball Spread": "KXMLBSPREAD",
        "Pro Baseball Total Points": "KXMLBTOTAL",
        "Professional Baseball All-Star Game": "KXMLBASGAME",
        "Professional Baseball Game": "KXMLBGAME",
        "Professional Baseball Series Total Games": "KXMLBSERIESGAMETOTAL"
    },
    "Basketball": {
        "Chinese Basketball Association Game": "KXCBAGAME",
        "College Basketball Game": "KXNCAABGAME",
        "College Basketball Women's Game": "KXNCAAWBGAME",
        "Eurocup Basketball Game": "KXEUROCUPGAME",
        "Euroleague Game": "KXEUROLEAGUEGAME",
        "MVE NBA Multi Game": "KXMVENBAMULTIGAMEEXTENDED",
        "MVE NBA Single Game": "KXMVENBASINGLEGAME",
        "Men's College Basketball Men's Game": "KXNCAAMBGAME",
        "Men's College Basketball Spread": "KXNCAAMBSPREAD",
        "Men's College Basketball Total Points": "KXNCAAMBTOTAL",
        "NBA All-Star game": "KXNBAALLSTAR",
        "NBL Basketball Game": "KXNBLGAME",
        "Pro Basketball Spread": "KXNBASPREAD",
        "Pro Basketball Total Points": "KXNBATOTAL",
        "Professional Basketball Game": "KXNBAGAME",
        "Professional Women's Basketball Game": "KXWNBAGAME",
        "WNBA All Star Game": "KXWNBAASGAME",
        "Women's College Basketball Spread": "KXNCAAWBSPREAD",
        "Women's College Basketball Total Points": "KXNCAAWBTOTAL"
    },
    "Cricket": {
        "Cricket ODI Match": "KXCRICKETODIMATCH",
        "Cricket T20I Match": "KXCRICKETT20IMATCH",
        "Cricket Test Match": "KXCRICKETTESTMATCH",
        "Cricket Women ODI Match": "KXCRICKETWOMENODIMATCH",
        "Cricket Women T20I Match": "KXCRICKETWOMENT20IMATCH",
        "Cricket Women Test Match": "KXCRICKETWOMENTESTMATCH",
        "Indian Premier League Cricket Game": "KXIPLGAME"
    },
    "Darts": {
        "Darts Match": "KXDARTSMATCH"
    },
    "Esports": {
        "Call of Duty Games": "KXCODGAME",
        "Counter-Strike 2 Games": "KXCSGOGAME",
        "Cs2 Games": "KXCS2GAMES",
        "Dota 2 Game": "KXDOTA2GAME",
        "League of Legends Game": "KXLOLGAME",
        "League of Legends Games": "KXLOLGAMES",
        "League of Legends Total Maps Played": "KXLOLTOTAL",
        "R6 Game": "KXR6GAME"
    },
    "Football": {
        "College Football FCS Game": "KXNCAAFCSGAME",
        "College Football Game": "KXNCAAFGAME",
        "College Football Spread": "KXNCAAFSPREAD",
        "College Football Total Points": "KXNCAAFTOTAL",
        "MVE NFL Multi Game": "KXMVENFLMULTIGAME",
        "MVE NFL Multi Game Extended": "KXMVENFLMULTIGAMEEXTENDED",
        "MVE NFL Single Game": "KXMVENFLSINGLEGAME",
        "NFL games times": "KXEVENTTIMES",
        "Pro Football Spread": "KXNFLSPREAD",
        "Pro Football Team Total Points": "KXNFLTEAMTOTAL",
        "Pro Football Total Points": "KXNFLTOTAL",
        "Professional Football Game": "KXNFLGAME"
    },
    "Golf": {
        "PGA Ryder Cup Matchups": "KXPGARYDERMATCH"
    },
    "Hockey": {
        "NHL Game": "KXNHLGAME",
        "NHL Goal Total": "KXNHLTOTAL",
        "NHL Spread": "KXNHLSPREAD"
    },
    "Soccer": {
        "Argentina Primera Division Game": "KXARGPREMDIVGAME",
        "Australian A League Game": "KXALEAGUEGAME",
        "Belgian Pro League Game": "KXBELGIANPLGAME",
        "Brasileiro Serie A Game": "KXBRASILEIROGAME",
        "Bundesliga Game": "KXBUNDESLIGAGAME",
        "Bundesliga Spread": "KXBUNDESLIGASPREAD",
        "Bundesliga Total": "KXBUNDESLIGATOTAL",
        "Club World Club Game": "KXCLUBWCGAME",
        "Copa Del Rey Game": "KXCOPADELREYGAME",
        "Coppa Italia Game": "KXCOPPAITALIAGAME",
        "Croatia HNL Game": "KXHNLGAME",
        "DFB Pokal Game": "KXDFBPOKALGAME",
        "Danish Superliga Game": "KXDANISHSUPERLIGAGAME",
        "EFL Cup Game": "KXEFLCUPGAME",
        "English Premier League Game": "KXEPLGAME",
        "English Premier League Spread": "KXEPLSPREAD",
        "English Premier League Total Goals": "KXEPLTOTAL",
        "Eredivisie Game": "KXEREDIVISIEGAME",
        "Fifa Game": "KXFIFAGAME",
        "Japan J League Game": "KXJLEAGUEGAME",
        "Korea K League Game": "KXKLEAGUEGAME",
        "La Liga Game": "KXLALIGAGAME",
        "La Liga Spread": "KXLALIGASPREAD",
        "La Liga Total": "KXLALIGATOTAL",
        "Liga MX Game": "KXLIGAMXGAME",
        "Liga Portugal Game": "KXLIGAPORTUGALGAME",
        "Ligue 1 Game": "KXLIGUE1GAME",
        "Ligue 1 Spread": "KXLIGUE1SPREAD",
        "Ligue 1 Total": "KXLIGUE1TOTAL",
        "MLS Spread": "KXMLSSPREAD",
        "MLS Total": "KXMLSTOTAL",
        "Major League Soccer Game": "KXMLSGAME",
        "Polish Ekstraklasa Game": "KXEKSTRAKLASAGAME",
        "Saudi Pro League Game": "KXSAUDIPLGAME",
        "Scottish Premiership Game": "KXSCOTTISHPREMGAME",
        "Serie A Game": "KXSERIEAGAME",
        "Serie A Spread": "KXSERIEASPREAD",
        "Serie A Total": "KXSERIEATOTAL",
        "Soccer Goal Total": "KXSOCCERTOTAL",
        "Soccer Spread": "KXSOCCERSPREAD",
        "Swiss Super League Game": "KXSWISSLEAGUEGAME",
        "Taca de Portugal Game": "KXTACAPORTGAME",
        "Turkish Super Lig Game": "KXSUPERLIGGAME",
        "UEFA Conference League Game": "KXUECLGAME",
        "UEFA Europa League Game": "KXUELGAME",
        "UEFA Soccer Games": "KXUEFAGAME"
    }
}

def get_ticker_by_name(query):
    """
    Strict lookup.
    """
    q = query.lower().strip()
    if q.startswith("kx"): return q.upper()

    for sport, map_data in HIERARCHY.items():
        for name, ticker in map_data.items():
            if name.lower() == q: return ticker
            if ticker.lower() == q: return ticker
    return None
