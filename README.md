# Kalshi Discord Bot 🤖

A sophisticated Discord bot for tracking your Kalshi portfolio and browsing prediction markets in real-time. Features an interactive button-based menu for fetching live odds.

## Features ✨

*   **Interactive Search** (`!search`): Browse sports (NFL, NBA, NHL, etc.), select market types (Moneyline, Spreads, Totals), and see live Bids/Asks.
*   **Portfolio Tracking**: Check your real-time Balance (`!bal`) and Active Positions (`!pos`).
*   **Clean UI**: Color-coded embeds, pagination-safe displays, and formatted headers.
*   **Real-Time Data**: Live fetching from Kalshi API v2.

---

## Setup Guide 🛠️

### 1. Prerequisites
*   Python 3.10+
*   A Kalshi Account (with API Access enabled).
*   A Discord Bot Token.

### 2. Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/discord-kalshi.git
    cd discord-kalshi
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### 3. API Keys & Configuration

You need to create a `.env` file in the root directory.

1.  **Discord Token**:
    *   Go to [Discord Developer Portal](https://discord.com/developers/applications).
    *   Create a New Application -> Bot -> Reset Token.
    *   Copy the Token.

2.  **Kalshi Keys**:
    *   Log in to Kalshi. Go to **Settings** -> **API**.
    *   Create a new Key Pair.
    *   Copy the **Key ID** (UUID).
    *   **IMPORTANT**: Download the `.pem` file (Private Key). Save it as `kalshi.pem` in the bot folder (or note its path).

3.  **Polymarket Keys (Optional for !bal p)**:
    *   Log in to [Polymarket](https://polymarket.com).
    *   Go to **Profile** (Top Right) -> **Settings** -> **API Keys**.
    *   Click **Create API Key**.
    *   Copy the **API Key**, **Secret**, and **Passphrase**.

4.  **Discord Channel ID**:
    *   In Discord, go to **User Settings** -> **Advanced** -> Enable **Developer Mode**.
    *   Right-click the channel you want the bot to speak in (or stream to).
    *   Click **Copy Channel ID**.

5.  **Create `.env`**:
    ```env
    DISCORD_TOKEN=your_discord_bot_token_here
    KALSHI_KEY_ID=your_kalshi_key_id_uuid_here
    KALSHI_PRIVATE_KEY_PATH=./kalshi.pem
    DISCORD_CHANNEL_ID=your_channel_id_here
    
    # Polymarket
    POLY_API_KEY=your_key_here
    POLY_SECRET=your_secret_here
    POLY_PASSPHRASE=your_passphrase_here
    POLY_PROXY_ADDRESS=your_proxy_address_0x...
    POLY_WALLET_KEY=your_wallet_private_key_0x...
    ```
    *   **Note**: To fetch balances, Polymarket requires signing requests with your Wallet Private Key (the one connected to Polymarket/Metamask) and knowing your Proxy Address.
    *   **Security**: Be extremely careful with your Private Key. Never share it. ensure `.env` is in `.gitignore`.

### 4. Running the Bot

```bash
python3 bot.py
```
If successful, you will see `Logged in as KalshiBot`.

---

## Commands 📜

| Command | Alias | Description |
| :--- | :--- | :--- |
| `!help` | | Shows the welcome menu and command list. |
| `!search` | | Opens the Interactive Sports Menu (with Auto-Polymarket Matching). |
| `!balance` | `!bal` | Displays balances. `!bal k` (Kalshi), `!bal p` (Poly), or `!bal` (Both). |
| `!positions` | `!pos` | Lists your active trading positions. |
| `/setup_arb` | | **(Admin)** Interactive tool to map Kalshi events to Polymarket for Arbitrage. |

---

## Customization (Developers) 👨‍💻

### Adding New Sports / Series
To make the bot search for new leagues (e.g., Baseball, Elections), edit **`managers/series_manager.py`**.

1.  Open `managers/series_manager.py`.
2.  Locate the `ALLOWED_SERIES` dictionary.
3.  Add a new entry following the format:

```python
    "SportName": {
        "LeagueName": {
            "moneyline": "TICKER_FOR_GAME",    # e.g., KXMLBGM
            "spread": "TICKER_FOR_SPREAD",     # e.g., KXMLBSPREAD
            "total": "TICKER_FOR_TOTAL"        # e.g., KXMLBTOTAL
        }
    }
```
*   *Note: You can find Series Tickers by exploring the Kalshi API or Website URL structure.*

### modifying Display Logic
*   **Results Limit**: To change how many games are shown (default 5 to avoid limits), edit `limit_per_game` or the loop break in **`views.py`**.

---

## Structure
*   `bot.py`: Main entry point. Handles commands and startup.
*   `views.py`: Contains the Discord UI logic (Buttons, Selects, Embeds).
*   `cogs/`:
    *   `mapper.py`: Slash command for interactive Arbitrage Mapping.
*   `managers/`:
    *   `market_manager.py`: Kalshi API fetching logic.
    *   `series_manager.py`: Manages the list of allowed sports and their API tickers.
    *   `portfolio_manager.py`: Handles Balance and Position fetching.
    *   `polymarket_manager.py`: Polymarket API fetching and matching logic.
    *   `mapping_logic.py`: Logic for parsing tickers and matching arbitrage pairs.
    *   `auth.py`: Handles RSA signature generation for Kalshi API.

## Marketplace Integration 🌐
The bot automatically searches for matching events on Polymarket using fuzzy string matching on the event title.
-   If a match is found, it displays the Polymarket odds (Yes/No cents) below the Kalshi data.
-   A link to the Polymarket event is added.

**Arbitrage Mapping**:
Admins can use `/setup_arb <KALSHI_TICKER>` to interactively find and map Polymarket events to Kalshi events, generating the configuration code needed for arbitrage strategies.


---

**Disclaimer**: This bot is for informational purposes. Trade responsibly.
