# ================= KEEP ALIVE =================
from flask import Flask
from threading import Thread

flask_app = Flask("")

@flask_app.route("/")
def home():
    return "Bot 24/7 ishlayapti"

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

# ================= TEXTS =================
TEXTS = {
    "uz": {
        "start": "🇺🇿 O‘zingizga qulay tilni tanlang",
        "welcome": "🎬 Video havolasini yuboring yoki 🎵 musiqa nomini yozing",
        "searching": "🔎",
        "choose": "🎧 Qo‘shiqni tanlang:",
        "downloading": "⏳",
        "done": "@sheraliyev_yuklovchi_bot orqali yuklab olindi",
        "error": "❌ Hech narsa topilmadi",
        "audio": "📥 Qo‘shiqni yuklab olish",
        "cancel": "❌ Bekor qilish",
    },
    "ru": {
        "start": "🇷🇺 Выберите удобный язык",
        "welcome": "🎬 Отправьте ссылку на видео или 🎵 название песни",
        "searching": "🔎",
        "choose": "🎧 Выберите песню:",
        "downloading": "⏳",
        "done": "Скачано через @sheraliyev_yuklovchi_bot",
        "error": "❌ Ничего не найдено",
        "audio": "📥 Скачать MP3",
        "cancel": "❌ Отмена",
    },
    "en": {
        "start": "🇺🇸 Choose the language you like",
        "welcome": "🎬 Send video link or 🎵 song name",
        "searching": "🔎",
        "choose": "🎧 Choose a song:",
        "downloading": "⏳",
        "done": "Downloaded via @sheraliyev_yuklovchi_bot",
        "error": "❌ Nothing found",
        "audio": "📥 Download MP3",
        "cancel": "❌ Cancel",
    }
}

# ================= /START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🇺🇿 O‘zingizga qulay tilni tanlang\n\n"
        "🇷🇺 Выберите удобный язык\n\n"
        "🇺🇸 Choose the language you like"
    )

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇺🇿 O‘zbek", callback_data="lang_uz"),
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
        ]
    ])

    await update.message.reply_text(text, reply_markup=kb)

# ================= LANGUAGE =================
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    lang = q.data.split("_")[1]
    context.user_data["lang"] = lang

    await q.edit_message_text(TEXTS[lang]["welcome"])

# ================= MAIN HANDLER =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lang = context.user_data.get("lang", "uz")

    # ========= AGAR LINK BO‘LSA =========
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
                [
                    InlineKeyboardButton("📥 Qo‘shiqni yuklab olish", callback_data="get_audio")
                ],
                [
                    InlineKeyboardButton(
                        "➕ Guruhga qo‘shish",
                        url=f"https://t.me/{context.bot.username}?startgroup=true"
                    )
                ]
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

    # ========= QO‘SHIQ QIDIRISH =========
    await update.message.reply_text(TEXTS[lang]["searching"])

    ydl_opts = {"quiet": True, "extract_flat": True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch10:{text}", download=False)
    except:
        await update.message.reply_text(TEXTS[lang]["error"])
        return

    entries = result.get("entries", [])[:10]
    if not entries:
        await update.message.reply_text(TEXTS[lang]["error"])
        return

    context.user_data["songs"] = entries

    msg = TEXTS[lang]["choose"] + "\n\n"
    buttons = []

    for i, e in enumerate(entries):
        msg += f"{i+1}. {e.get('title','Noma’lum')}\n"
        buttons.append(InlineKeyboardButton(str(i+1), callback_data=f"song_{i}"))

    keyboard = [
        buttons[i:i+5] for i in range(0, len(buttons), 5)
    ]
    keyboard.append([InlineKeyboardButton(TEXTS[lang]["cancel"], callback_data="cancel")])

    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# ================= CANCEL =================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "uz")
    await q.message.reply_text(TEXTS[lang]["welcome"])

# ================= SONG DOWNLOAD =================
async def download_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    lang = context.user_data.get("lang", "uz")
    index = int(q.data.split("_")[1])
    songs = context.user_data.get("songs")

    if not songs or index >= len(songs):
        await q.message.reply_text(TEXTS[lang]["error"])
        return

    song = songs[index]
    url = song["url"]

    await q.message.reply_text(TEXTS[lang]["downloading"])

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": "song_%(id)s.%(ext)s",
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = f"song_{info['id']}.mp3"

    await q.message.reply_audio(audio=open(filename, "rb"), title=info.get("title"))
    os.remove(filename)

# ================= AUDIO FROM VIDEO =================
async def get_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "uz")

    url = context.user_data.get("last_url")
    if not url:
        return

    await q.message.reply_text(TEXTS[lang]["downloading"])

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": "video_audio.%(ext)s",
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    await q.message.reply_audio(audio=open("video_audio.mp3", "rb"))
    os.remove("video_audio.mp3")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(download_song, pattern="^song_"))
    app.add_handler(CallbackQueryHandler(get_audio, pattern="^get_audio$"))
    app.add_handler(CallbackQueryHandler(cancel, pattern="^cancel$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Bot ishga tushdi")
    app.run_polling()

if __name__ == "__main__":
    main()
