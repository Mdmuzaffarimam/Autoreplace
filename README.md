# Sagiri-like Channel Manager Bot 🤖

A Telegram bot that auto-replaces text in your channel messages.  
Built with **python-telegram-bot** and SQLite.

## ✨ Features
- `/connect <channel_id>` → connect a channel (bot must be admin).
- `/addreplace old::new` → add auto-replace rules.
- `/listrules` → list rules for your connected channels.

## 🚀 Deploy

### Deploy to Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template?repo=https://github.com/YOUR-USERNAME/sagiri-bot)

### Deploy to Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR-USERNAME/sagiri-bot)

*(Replace `YOUR-USERNAME/sagiri-bot` with your actual GitHub repository URL)*

## 🖥️ Local / VPS Setup
1. Clone the repo or download ZIP.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your `BOT_TOKEN`.
4. Run:
   ```bash
   python main.py
   ```

## 📦 Files
- `main.py` → Bot code.
- `requirements.txt` → Dependencies.
- `Procfile` → For Heroku/Render.
- `start.sh` → Startup script.
- `.env.example` → Environment example.
- `README.md` → This guide.

Enjoy! 🚀