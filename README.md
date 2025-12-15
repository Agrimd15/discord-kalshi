# Discord Kalshi Portfolio Bot 🤖

A lightweight Discord bot to track your [Kalshi](https://kalshi.com) portfolio. Check your balance and active positions quickly.

## Features
- **Balance**: View cash available (`!balance`).
- **Positions**: List active market positions and exposure (`!positions`).

## Prerequisites
- Python 3.9+
- Kalshi Account Key
- Discord Bot Token

---

## 🛠️ Setup Guide

### 1. Configuration
1. **Clone Repo**:
   ```bash
   git clone https://github.com/yourusername/discord-kalshi.git
   cd discord-kalshi
   ```
2. **Install**:
   ```bash
   pip3 install -r requirements.txt
   ```
3. **Environment**:
   Copy `.env.example` to `.env` and fill in:
   ```ini
   DISCORD_TOKEN=...
   KALSHI_KEY_ID=...
   KALSHI_PRIVATE_KEY_PATH=kalshi.key
   ```

### 2. Run
```bash
python3 bot.py
```

## 🎮 Commands
| Command | Description |
| :--- | :--- |
| `!balance` | Check current account balance. |
| `!positions` | List active positions. |
