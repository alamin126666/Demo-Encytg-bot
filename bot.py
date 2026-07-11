#!/usr/bin/env python3
"""
HTML Obfuscator Telegram Bot
Converts HTML/CSS/JS to hex + random pattern obfuscated output
Deploy on Render via GitHub
"""

import os
import re
import random
import string
import logging
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Config ─────────────────────────────────────────────────────────────────
TOKEN       = os.environ.get("BOT_TOKEN", "")
PORT        = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")   # https://your-app.onrender.com

# ─── Obfuscation Engine ─────────────────────────────────────────────────────

def _rvar(n: int = 7) -> str:
    """Random JS variable name."""
    prefix = random.choice(["_", "__", "$", "$$"])
    body   = "".join(random.choices(string.ascii_letters, k=n))
    return prefix + body


def _noise_vars(count: int = 5) -> str:
    """Fake variable lines to confuse readers."""
    lines = []
    for _ in range(count):
        val_type = random.randint(0, 2)
        if val_type == 0:
            val = random.randint(1000, 999999)
            lines.append(f"var {_rvar()}={val};")
        elif val_type == 1:
            s = "".join(random.choices(string.ascii_letters, k=random.randint(4, 10)))
            lines.append(f'var {_rvar()}="{s}";')
        else:
            a, b = _rvar(), _rvar(4)
            lines.append(f"var {a}=function({b}){{return {b};}};")
    return "\n".join(lines)


def obfuscate_html(html: str) -> str:
    """
    Obfuscate HTML/CSS/JS using:
      • Hex character encoding (\\xHH)
      • Array chunking with random chunk sizes
      • Random variable names
      • Noise / dummy variables
      • String split tricks on 'write' and 'document'
    """

    # --- Step 1: hex-encode every character ---
    hex_chars = [f"\\x{ord(c):02x}" for c in html]

    # --- Step 2: split into random-sized chunks ---
    chunks   = []
    i        = 0
    hex_flat = "".join(hex_chars)

    # We chunk by actual hex units (each \xNN = 4 chars in source)
    units = [f"\\x{ord(c):02x}" for c in html]
    idx   = 0
    while idx < len(units):
        size  = random.randint(6, 18)
        chunk = "".join(units[idx : idx + size])
        chunks.append(f'"{chunk}"')
        idx  += size

    # --- Step 3: build variable names ---
    v_arr  = _rvar()
    v_str  = _rvar()
    v_fn   = _rvar()
    v_tmp  = _rvar()
    v_doc1 = _rvar(4)
    v_doc2 = _rvar(4)
    v_wr1  = _rvar(3)
    v_wr2  = _rvar(3)

    chunks_joined = ",\n  ".join(chunks)

    noise_top    = _noise_vars(random.randint(3, 6))
    noise_bottom = _noise_vars(random.randint(2, 4))

    # Split 'document' and 'write' so literal strings don't appear
    doc_split  = f'"{v_doc1}"+"ment"'  # "docu"+"ment"  — we fill v_doc1 below
    writ_split = f'"{v_wr1}"+"te"'     # "wri"+"te"     — we fill v_wr1 below

    script = (
        f"<script>\n"
        f"{noise_top}\n"
        f"var {v_arr}=[\n  {chunks_joined}\n];\n"
        f"var {v_str}={v_arr}.join('');\n"
        f"var {v_fn}=function({v_tmp}){{\n"
        f"  return {v_tmp}.replace(/\\\\x([0-9A-Fa-f]{{2}})/g,\n"
        f"    function(m,p){{return String.fromCharCode(parseInt(p,16));}}\n"
        f"  );\n"
        f"}};\n"
        f"var {v_doc1}='docu';\n"
        f"var {v_wr1}='wri';\n"
        f"var {v_doc2}=window[{doc_split}];\n"
        f"var {v_wr2}=({v_wr1}+'te');\n"
        f"{noise_bottom}\n"
        f"{v_doc2}[{v_wr2}]({v_fn}({v_str}));\n"
        f"</script>"
    )
    return script


# ─── Helpers ────────────────────────────────────────────────────────────────

async def _send_result(update: Update, result: str):
    """Send obfuscated output — text if small, file if large."""
    if len(result) <= 3800:
        # Telegram max message = 4096; leave room for caption
        preview = result[:3800]
        await update.message.reply_text(
            f"✅ *Obfuscated Output:*\n\n```html\n{preview}\n```",
            parse_mode="Markdown",
        )
    else:
        # Write to temp file and send
        with tempfile.NamedTemporaryFile(
            suffix=".html", delete=False, mode="w", encoding="utf-8"
        ) as f:
            f.write(result)
            tmp_path = f.name

        with open(tmp_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename="obfuscated.html",
                caption=(
                    "✅ *Obfuscated Output* (ফাইল হিসেবে)\n\n"
                    "📋 ফাইলটি ডাউনলোড করে ব্যবহার করুন।"
                ),
                parse_mode="Markdown",
            )
        os.unlink(tmp_path)


# ─── Handlers ───────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📖 How to Use", callback_data="help")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")],
    ]
    await update.message.reply_text(
        "🔐 *HTML Obfuscator Bot*\n\n"
        "আপনার HTML / CSS / JS কোড পাঠান।\n"
        "আমি সেটাকে *hex + random pattern* দিয়ে obfuscate করে\n"
        "`<script>...</script>` ব্লকে রিটার্ন করব!\n\n"
        "▶ শুধু কোড পেস্ট করুন বা `.html` ফাইল আপলোড করুন।",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *ব্যবহার পদ্ধতি:*\n\n"
        "1️⃣ আপনার HTML/CSS/JS কোড কপি করুন\n"
        "2️⃣ সেটা এই বটে পেস্ট করে পাঠান\n"
        "3️⃣ অথবা `.html` ফাইল সরাসরি আপলোড করুন\n\n"
        "✅ বট আপনাকে একটি obfuscated `<script>` ব্লক দেবে\n"
        "✅ সেই স্ক্রিপ্ট HTML-এ embed করলে পেজ আগের মতোই কাজ করবে\n\n"
        "📌 *Commands:*\n"
        "/start — হোম\n"
        "/help  — সাহায্য\n\n"
        "⚠️ বড় ফাইলের ক্ষেত্রে output `.html` ফাইলে আসবে।",
        parse_mode="Markdown",
    )


async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help":
        await query.message.reply_text(
            "📖 *ব্যবহার পদ্ধতি:*\n\n"
            "• HTML / CSS / JS কোড পেস্ট করুন\n"
            "• বা `.html` ফাইল আপলোড করুন\n"
            "• obfuscated `<script>` ব্লক পাবেন\n\n"
            "বড় output ফাইলে পাঠানো হবে।",
            parse_mode="Markdown",
        )
    elif query.data == "about":
        await query.message.reply_text(
            "ℹ️ *About*\n\n"
            "এই বট HTML/CSS/JS কে *hex encoding* ও "
            "*random variable pattern* দিয়ে obfuscate করে।\n\n"
            "🛡️ Source code protection-এর জন্য ব্যবহার করুন।",
            parse_mode="Markdown",
        )


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle plain-text HTML sent by user."""
    html = update.message.text.strip()
    if not html:
        await update.message.reply_text("⚠️ খালি message পাঠাবেন না।")
        return

    status = await update.message.reply_text("⏳ Obfuscating…")
    try:
        result = obfuscate_html(html)
        await status.delete()
        await _send_result(update, result)
    except Exception as exc:
        logger.exception("Obfuscation error")
        await status.edit_text(f"❌ Error: {exc}")


async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle uploaded .html files."""
    doc = update.message.document
    if not (doc.file_name or "").lower().endswith(".html"):
        await update.message.reply_text("❌ শুধুমাত্র `.html` ফাইল সাপোর্ট করা হয়।")
        return

    status = await update.message.reply_text("⏳ ফাইল পড়ছি ও obfuscate করছি…")
    try:
        tg_file = await doc.get_file()
        raw     = await tg_file.download_as_bytearray()
        html    = raw.decode("utf-8", errors="replace")
        result  = obfuscate_html(html)
        await status.delete()
        await _send_result(update, result)
    except Exception as exc:
        logger.exception("File obfuscation error")
        await status.edit_text(f"❌ Error: {exc}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable not set!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    if WEBHOOK_URL:
        logger.info(f"Starting webhook on port {PORT}")
        app.run_webhook(
            listen      = "0.0.0.0",
            port        = PORT,
            url_path    = TOKEN,           # secret path
            webhook_url = f"{WEBHOOK_URL}/{TOKEN}",
        )
    else:
        logger.info("Starting polling (local mode)")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
