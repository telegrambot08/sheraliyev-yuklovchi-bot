# ================= KEEP ALIVE =================
from flask import Flask
from threading import Thread

flask_app = Flask("")

@flask_app.route("/")
def home():
    return "Bot ishlayapti"

def run():
    flask_app.run(host="0.0.0.0", port=8080)

Thread(target=run).start()

# ================= IMPORTS =================
import os
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

TEXTS = {
    "uz": {
        "start": "🇺🇿 O‘zingizga qulay tilni tanlang",
        "welcome": "🎬 Video link yuboring yoki 🎵 qo‘shiq nomini yozing",
        "searching": "🔎 Qidirilmoqda...",
        "choose": "🎧 Qo‘shiqni tanlang:\n\n",
        "downloading": "⏳ Yuklanmoqda...",
        "done": "✅ Yuklab olindi",
        "error": "❌ Xatolik yuz berdi",
        "cancel": "❌ Bekor qilish",
    }
}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇿 O‘zbek", callback_data="lang_uz")]
    ])
    await update.message.reply_text(
        "🇺🇿 Tilni tanlang",
        reply_markup=kb
    )

# ================= LANGUAGE =================
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["lang"] = "uz"
    await q.edit_message_text(TEXTS["uz"]["welcome"])

# ================= TEXT HANDLER =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lang = "uz"

    # ===== LINK BO'LSA =====
    if text.startswith("http"):
        await update.message.reply_text(TEXTS[lang]["downloading"])

        ydl_opts = {
            "format": "best[height<=720]",
            "outtmpl": "video_%(id)s.%(ext)s",
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)

            context.user_data["last_url"] = text

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎵 Faqat audio", callback_data="get_audio")]
            ])

            await update.message.reply_video(
                video=open(filename, "rb"),
                caption=TEXTS[lang]["done"],
                reply_markup=kb
            )

            os.remove(filename)

        except:
            await update.message.reply_text(TEXTS[lang]["error"])
        return

    # ===== QO'SHIQ QIDIRISH =====
    await update.message.reply_text(TEXTS[lang]["searching"])

    try:
        with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
            result = ydl.extract_info(f"ytsearch10:{text}", download=False)
    except:
        await update.message.reply_text(TEXTS[lang]["error"])
        return

    entries = result.get("entries", [])[:10]

    if not entries:
        await update.message.reply_text(TEXTS[lang]["error"])
        return

    context.user_data["songs"] = entries

    msg = TEXTS[lang]["choose"]
    buttons = []

    for i, e in enumerate(entries):
        msg += f"{i+1}. {e.get('title')}\n"
        buttons.append(InlineKeyboardButton(str(i+1), callback_data=f"song_{i}"))

    keyboard = [buttons[i:i+5] for i in range(0, len(buttons), 5)]
    keyboard.append([InlineKeyboardButton(TEXTS[lang]["cancel"], callback_data="cancel")])

    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================= SONG DOWNLOAD =================
async def download_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    songs = context.user_data.get("songs")
    index = int(q.data.split("_")[1])

    if not songs:
        return

    url = songs[index]["url"]

    await q.message.reply_text("⏳ Yuklanmoqda...")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": "song_%(id)s.%(ext)s",
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    await q.message.reply_audio(
        audio=open(filename, "rb"),
        title=info.get("title")
    )

    os.remove(filename)

# ================= AUDIO FROM VIDEO =================
async def get_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    url = context.user_data.get("last_url")
    if not url:
        return

    await q.message.reply_text("⏳ Yuklanmoqda...")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio",
        "outtmpl": "video_audio.%(ext)s",
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    await q.message.reply_audio(audio=open(filename, "rb"))
    os.remove(filename)

# ================= CANCEL =================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(TEXTS["uz"]["welcome"])

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(download_song, pattern="^song_"))
    app.add_handler(CallbackQueryHandler(get_audio, pattern="^get_audio$"))
    app.add_handler(CallbackQueryHandler(cancel, pattern="^cancel$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot ishga tushdi")
    app.run_polling()

if __name__ == "__main__":
    main()
