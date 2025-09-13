import logging
import sqlite3
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database
DB_PATH = os.getenv("DB_PATH", "replacements.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS replacements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT,
                    old TEXT,
                    new TEXT
                )""")
cursor.execute("""CREATE TABLE IF NOT EXISTS connections (
                    user_id INTEGER,
                    channel_id TEXT,
                    PRIMARY KEY(user_id, channel_id)
                )""")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Sagiri-like Channel Manager (demo)\n\n"
        "Commands:\n"
        "/connect <channel_id>  — register a channel to manage\n"
        "/addreplace old::new   — add a replace rule for your connected channel\n"
        "/listrules             — list replace rules for your connected channels\n"
        "/help                  — show this message\n\n"
        "Notes:\n- Bot must be admin in the channel you connect.\n- Provide channel id like -1001234567890"
    )

# Helper: simple admin check (tries to get chat member - may raise)
async def is_bot_admin_in_channel(app, channel_id):
    try:
        member = await app.bot.get_chat_member(chat_id=int(channel_id), user_id=await app.bot.get_me().id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        logger.info("Admin check failed: %s", e)
        return False

async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /connect <channel_id> (example: -1001234567890)")
        return

    channel_id = context.args[0]
    user_id = update.effective_user.id

    # Optional: check bot admin status (best-effort)
    try:
        # get_chat_member requires integer chat_id for channels; may raise BadRequest
        chat_member = await context.bot.get_chat_member(chat_id=int(channel_id), user_id=(await context.bot.get_me()).id)
        if chat_member.status not in ("administrator", "creator"):
            await update.message.reply_text("⚠️ Bot is not admin in that channel. Please add the bot as admin and try again.")
            return
    except Exception:
        # If check fails, warn but still allow registering (user can confirm)
        logger.info("Could not verify admin status for channel %s", channel_id)
        # continue

    cursor.execute("INSERT OR IGNORE INTO connections (user_id, channel_id) VALUES (?, ?)", (user_id, channel_id))
    conn.commit()
    await update.message.reply_text(f"✅ Registered channel `{channel_id}` for your account.", parse_mode="Markdown")

async def addreplace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /addreplace old::new")
        return

    arg = " ".join(context.args)
    if "::" not in arg:
        await update.message.reply_text("Usage: /addreplace old::new  (use :: as a separator)")
        return

    user_id = update.effective_user.id
    cursor.execute("SELECT channel_id FROM connections WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("You have no connected channels. Use /connect <channel_id> first.")
        return

    old, new = arg.split("::", 1)
    # Add rule for all channels user has connected
    for (channel_id,) in rows:
        cursor.execute("INSERT INTO replacements (channel_id, old, new) VALUES (?, ?, ?)", (channel_id, old, new))
    conn.commit()
    await update.message.reply_text(f"✅ Added replace rule for your channel(s): `{old}` → `{new}`", parse_mode="Markdown")

async def listrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT channel_id FROM connections WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("No connected channels. Use /connect <channel_id>.")
        return
    lines = []
    for (channel_id,) in rows:
        cursor.execute("SELECT id, old, new FROM replacements WHERE channel_id=?", (channel_id,))
        rules = cursor.fetchall()
        lines.append(f"Channel {channel_id}:")
        if not rules:
            lines.append("  (no rules)")
            continue
        for r in rules:
            lines.append(f"  {r[0]}: `{r[1]}` → `{r[2]}`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def handle_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only handle channel posts
    chat = update.effective_chat
    if chat is None or chat.type != "channel":
        return

    channel_id = str(chat.id)
    text = update.message.text or ""
    if not text:
        # For simplicity only handle text messages in this demo
        return

    cursor.execute("SELECT old, new FROM replacements WHERE channel_id=?", (channel_id,))
    replacements = cursor.fetchall()
    modified = text
    for old, new in replacements:
        if old:
            modified = modified.replace(old, new)

    if modified != text:
        try:
            # repost modified text as channel (bot must be admin and have post rights)
            await context.bot.send_message(chat_id=channel_id, text=modified)
        except BadRequest as e:
            logger.warning("Failed to send modified message: %s", e)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise RuntimeError("Please set BOT_TOKEN environment variable (see README).")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("connect", connect))
    app.add_handler(CommandHandler("addreplace", addreplace))
    app.add_handler(CommandHandler("listrules", listrules))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_channel_message))

    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()