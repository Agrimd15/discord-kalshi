# Kalshi Discord Bot 📈

A powerful, open-source Discord bot that integrates with the [Kalshi Prediction Market](https://kalshi.com/) API (v2). 

**Features:**
*   💰 **Real-time Balance:** Check your portfolio cash balance instantly with `!balance`.
*   🚨 **Instant Alerts:** Get notified immediately in Discord when your orders are filled.
*   🔒 **Secure:** Uses RSA-SHA256 signing for all requests; keys stay local.

---

## ⚠️ Disclaimer
This software is for educational purposes only. It is not financial advice. Use it at your own risk. The authors are not responsible for any financial losses incurred while using this bot.

---

## Prerequisites
*   **Python 3.9** or higher.
*   A **Kalshi** account.
*   A **Discord** account.

---

## 🛠️ Step-by-Step Setup Guide

### Phase 1: Get Your Credentials

#### 1. 🤖 Create the Discord Bot
1.  Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2.  Click **"New Application"** -> Name it (e.g., "KalshiBot").
3.  Go to the **"Bot"** tab in the left sidebar.
4.  Click **"Reset Token"** -> **Copy** this token. This is your `DISCORD_TOKEN`.
5.  **Critical:** Scroll down to "Privileged Gateway Intents" and enable **"Message Content Intent"**.
6.  Go to **OAuth2** -> **URL Generator**.
    *   Select Scope: `bot`.
    *   Select Permissions: `Send Messages`, `Embed Links`, `Read Message History` (or just `Administrator` for testing).
    *   Copy the URL and open it in your browser to invite the bot to your server.

#### 2. 🆔 Get Discord Channel ID
1.  Open Discord -> User Settings (Gear ⚙️) -> **Advanced**.
2.  Enable **"Developer Mode"**.
3.  Right-click the channel where you want alerts.
4.  Click **"Copy Channel ID"**. This is your `DISCORD_CHANNEL_ID`.

#### 3. 🔑 Get Kalshi API Keys
1.  Log in to [Kalshi.com](https://kalshi.com/).
2.  Go to **Account** -> **Settings** -> **API**.
3.  Create a new API Key.
4.  **Download the `.pem` file.** Save this safely! This is your `KALSHI_PRIVATE_KEY_PATH`.
5.  Copy the **Key ID** (UUID). This is your `KALSHI_KEY_ID`.

---

## 🚀 Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/discord-kalshi.git
    cd discord-kalshi
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Secure Configuration:**
    *   Create a file named `.env` in the project folder.
    *   Copy the following text into it and fill in your keys:

    ```ini
    # .env file
    DISCORD_TOKEN=paste_your_discord_token_here
    DISCORD_CHANNEL_ID=paste_channel_id_here
    KALSHI_KEY_ID=paste_kalshi_key_id_here
    KALSHI_PRIVATE_KEY_PATH=kalshi.key  # The filename of your .pem file
    ```

    *   **Move** your downloaded `.pem` key file into this folder.

---

## ▶️ Usage

1.  **Start the bot:**
    ```bash
    python bot.py
    ```
    *You should see: "Logged in as KalshiBot#1234"*

2.  **Commands:**
    *   `!balance` - Shows your current available cash.

3.  **Auto-Alerts:**
    *   The bot will now silently listen in the background. As soon as one of your orders fills on Kalshi, it will post an Embed to your chosen channel.

---

## 🛡️ Security Note
*   **NEVER** share your `.env` file or your `.pem` key file.
*   This project includes a `.gitignore` file that prevents these sensitive files from being uploaded to GitHub.

## 📄 License
MIT License. Feel free to modify and use!
