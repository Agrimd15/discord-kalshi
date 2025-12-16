
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

3.  **Discord Channel ID**:
    *   In Discord, go to **User Settings** -> **Advanced** -> Enable **Developer Mode**.
    *   Right-click the channel you want the bot to speak in (or stream to).
    *   Click **Copy Channel ID**.

4.  **Create `.env`**:
    ```env
    DISCORD_TOKEN=your_discord_bot_token_here
    KALSHI_KEY_ID=your_kalshi_key_id_uuid_here
    KALSHI_PRIVATE_KEY_PATH=./kalshi.pem
    DISCORD_CHANNEL_ID=your_channel_id_here
    ```

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
| `!search` | | Opens the Interactive Sports Menu. |
| `!balance` | `!bal` | Displays your available cash balance. |
| `!positions` | `!pos` | Lists your active trading positions. |

---

## Customization (Developers) 👨‍💻

### Adding New Sports / Series
To make the bot search for new leagues (e.g., Baseball, Elections), edit **`series_manager.py`**.

1.  Open `series_manager.py`.
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
*   `series_manager.py`: Manages the list of allowed sports and their API tickers.
*   `market_manager.py`: Fetches logic. Groups markets into Types (Spread vs Total).
*   `auth.py`: Handles RSA signature generation for Kalshi API.

---

**Disclaimer**: This bot is for informational purposes. Trade responsibly.
