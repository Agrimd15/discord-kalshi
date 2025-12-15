# Discord Kalshi Bot 🤖

A robust Discord bot for the [Kalshi Prediction Market](https://kalshi.com). Browse sports markets, check live lines, manage your portfolio, and track orders directly from your Discord server.

## Features
- **Interactive menu System**: Browse sports (NFL, NBA, EPL, etc.) using Discord buttons and dropdowns.
- **Filtering**: Automatically filters out "fluff" (awards, drafts) to show only **Games**, **Spreads**, and **Totals**.
- **Live Odds**: Displays events with start times and current Yes/No prices (Ask/Bid).
- **Portfolio Management**: Check your balance (`!balance`) and active positions (`!positions`).
- **Real-time Stream**: (Optional) WebSocket integration for live order fill alerts.

## Prerequisites
- Python 3.9 or higher
- A Kalshi Account (verified)
- A Discord Account (to create a bot)

---

## 🛠️ Setup Guide

### 1. Discord Bot Setup
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** and name it (e.g., "KalshiBot").
3. Go to the **Bot** tab on the left and click **Add Bot**.
4. **Token**: Click "Reset Token" to reveal your **Bot Token**. Copy this safe.
5. **Invite**: Go to **OAuth2** -> **URL Generator**.
   - Scopes: check `bot`.
   - Bot Permissions: check `Send Messages`, `Embed Links`, `Read Message History`, `View Channels`.
   - Copy the generated URL and invite the bot to your server.

### 2. Getting the Channel ID
To let the bot know where to post (and for the optional stream), needs a Channel ID.
1. Open Discord App Settings -> **Advanced**.
2. Enable **Developer Mode**.
3. Right-click the channel you want the bot to use and click **Copy Channel ID**.

### 3. Kalshi API Keys
1. Log in to [Kalshi](https://kalshi.com).
2. Go to **Account Settings** -> **API Keys** (or [click here](https://kalshi.com/account/settings/keys)).
3. Click **Add API Key**.
4. This will give you a **Key ID** (UUID) and download a private key file (`.key` or `.pem`).
   - **Key ID**: e.g., `12345678-abcd-1234...`
   - **Private Key**: Save this file (e.g., `kalshi.key`) into the project folder.

---

## 💻 Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/discord-kalshi.git
   cd discord-kalshi
   ```

2. **Install Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Configure Environment**:
   Duplicate the example file:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your details:
   ```ini
   DISCORD_TOKEN=your_discord_token_here
   DISCORD_CHANNEL_ID=123456789012345678
   KALSHI_KEY_ID=your_kalshi_key_id
   KALSHI_PRIVATE_KEY_PATH=kalshi.key
   ```
   *Note: Ensure `kalshi.key` matches the filename you saved in step 3.*

4. **Generate Market Hierarchy**:
   The bot uses a locally cached map of sports series to ensure fast, strict searching.
   Run this script to fetch active markets and build the menu:
   ```bash
   python3 fetch_hierarchy.py
   ```
   *Output: `Successfully wrote Sports hierarchy...`*

5. **Run the Bot**:
   ```bash
   python3 bot.py
   ```

---

## 🎮 Usage

**Prefix**: `!`

| Command | Description |
| :--- | :--- |
| `!search` | Opens the **Interactive Sports Menu** (Football, Basketball, etc.). |
| `!search <query>` | Strict search for a specific ticker (e.g. `!search KXNBAGAMES`). |
| `!balance` | Shows your Cash, Credit, and Portfolio Value. |
| `!positions` | Lists your active positions with Profit/Loss (if available). |
| `!orders` | (Coming Soon) Manage/Cancel open orders. |

---

## 📂 Project Structure
- `bot.py`: Main entry point. Handles Discord commands and Menu UI.
- `fetch_hierarchy.py`: Scraper script. Fetches ~7000 series, filters for "Games", generates `kalshi_hierarchy.py`.
- `kalshi_hierarchy.py`: Auto-generated file containing the sports map.
- `auth.py`: Handles RSA-PSS signing for Kalshi API V2.
- `stream.py`: Async WebSocket listener for order fills.

## Security Note
Never share your `.env` file or your `kalshi.key` private key. The `.gitignore` is set up to exclude them.
