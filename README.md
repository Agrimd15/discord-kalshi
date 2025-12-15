# Discord Kalshi Bot 🤖

A powerful, AI-driven Discord bot for browsing live Kalshi prediction markets. Features smart categorization, typo tolerance, and real-time filtering.

## ✨ Key Features

*   **Smart Search**: `!search nfl` finds games. `!search politics` finds election markets.
*   **Interactive Menu**: `!search sports` opens a clickable menu to browse NFL, NBA, NHL, and more.
*   **Typo Tolerance**: Type `!search footbll` or `!search nhhl` and the bot will figure it out!
*   **Live Game Filters**: 
    *   Shows strictly **imminent games** (Tonight/Tomorrow) to reduce clutter.
    *   Sorts by kickoff time.
*   **Futures Support**: `!search nfl futures` bypasses time filters to show Season Winners and Super Bowl odds.
*   **Account Tools**: Check your `!balance` and active `!positions`.
*   **AI Powered**: Uses Gemini to categorize generic queries (e.g., "funny bets").

## 🚀 Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Environment Variables**:
    Create a `.env` file with your credentials or use the `.env.example` as a template:
    ```env
    DISCORD_TOKEN=your_token
    DISCORD_CHANNEL_ID=your_channel_id
    KALSHI_KEY_ID=your_key_id
    KALSHI_PRIVATE_KEY_PATH=/path/to/key.pem
    GEMINI_API_KEY=your_gemini_key
    ```
    
    ### 🔑 Obtaining Credentials
    
    **1. Discord Token:**
    *   Go to the [Discord Developer Portal](https://discord.com/developers/applications).
    *   Create a "New Application" -> "Bot".
    *   Enable "Message Content Intent" (Critical!).
    *   Click "Reset Token" to get your `DISCORD_TOKEN`.
    *   Invite the bot to your server using the "OAuth2" -> "URL Generator" (scopes: `bot`, permissions: `Read Messages/View Channels`, `Send Messages`).

    **2. Kalshi Keys:**
    *   Log in to [Kalshi](https://kalshi.com/).
    *   Go to **Account** -> **API Management**.
    *   Create a NEW Key. It will give you a **Key ID** (`KALSHI_KEY_ID`) and prompt you to download a `.pem` file.
    *   Save this `.pem` file to your project folder (e.g., `kalshi-key.pem`).
    *   Set `KALSHI_PRIVATE_KEY_PATH` to the full path of this `.pem` file.

    **3. Gemini API Key (for AI):**
    *   Visit [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   Click "Get API Key" -> "Create API Key".
    *   Copy string to `GEMINI_API_KEY`.
3.  **Run the Bot**:
    ```bash
    python3 bot.py
    ```

## 📜 Commands

| Command | Description |
| :--- | :--- |
| `!search <query>` | Search for markets/events. |
| `!search sports` | Open the interactive Sports Menu. |
| `!balance` | View your cash balance. |
| `!positions` | View active trades. |
| `!commands` | Show help menu. |

## 🛠 Troubleshooting

*   **"No relevant series found"**: Try a broader term or check your spelling (though the bot handles most typos!).
*   **Rate Limits**: The AI has a usage limit (15/min). Menus do not consume AI quota.

---
*Built with Discord.py & Kalshi v2 API*
