bot.py
# ================== CONFIG ==================
BOT_TOKEN = "8491501428:AAG8C4TUAAFhB8wKsyGqNcdMX9_BIfAgy6o"
ADMIN_IDS = [@Akashme1]  # ← apna Telegram user ID
CHANNEL_ID = -1006994682171  # Telegram channel ID

# ============================================

import os
import json
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yt_dlp

PROGRESS_FILE = "progress.json"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------- Utils ----------
def is_admin(user_id):
    return user_id in ADMIN_IDS

def save_progress(data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        return json.load(open(PROGRESS_FILE))
    return {"uploaded": []}

# ---------- Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Access denied")
        return

    await update.message.reply_text(
        "🔥 PRO Course Extractor Bot Ready\n\n"
        "Commands:\n"
        "/extract <course_url>\n"
        "/status\n"
        "/stop\n\n"
        "Hindi + English mixed support ✅"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    progress = load_progress()
    await update.message.reply_text(
        f"📊 Status:\nUploaded files: {len(progress['uploaded'])}"
    )

# ---------- Extract Logic ----------
def extract_links(course_url):
    html = requests.get(course_url, timeout=20).text
    soup = BeautifulSoup(html, "html.parser")

    links = []

    for video in soup.find_all("video"):
        src = video.get("src")
        if src:
            links.append(src)

    for a in soup.find_all("a"):
        href = a.get("href", "")
        if any(x in href for x in [".mp4", ".pdf", ".zip", ".m3u8"]):
            links.append(href)

    return list(set(links))

# ---------- Download ----------
def download_file(url, index):
    ydl_opts = {
        "outtmpl": f"{DOWNLOAD_DIR}/{index:02d}_%(title)s.%(ext)s",
        "quiet": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

# ---------- Extract Command ----------
async def extract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("❗ Usage: /extract <course_url>")
        return

    course_url = context.args[0]
    await update.message.reply_text("🔍 Course scan ho raha hai…")

    links = extract_links(course_url)
    if not links:
        await update.message.reply_text("❌ Koi content nahi mila")
        return

    progress = load_progress()
    uploaded = progress["uploaded"]

    await update.message.reply_text(f"📦 Total files found: {len(links)}")

    for i, link in enumerate(links, start=1):
        if link in uploaded:
            continue

        await update.message.reply_text(f"⬇️ Downloading {i}/{len(links)}")

        try:
            download_file(link, i)
            file_path = os.listdir(DOWNLOAD_DIR)[-1]
            full_path = os.path.join(DOWNLOAD_DIR, file_path)

            await context.bot.send_document(
                chat_id=CHANNEL_ID,
                document=open(full_path, "rb"),
                caption=f"📘 Lesson {i}"
            )

            uploaded.append(link)
            save_progress({"uploaded": uploaded})
            os.remove(full_path)

        except Exception as e:
            await update.message.reply_text(f"⚠️ Error: {str(e)}")
            break

    await update.message.reply_text("✅ Extraction & Upload completed")

# ---------- Stop ----------
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("⛔ Process manually stopped")

# ---------- Run ----------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("extract", extract))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("stop", stop))

print("🔥 PRO Bot Running…")
app.run_polling()
