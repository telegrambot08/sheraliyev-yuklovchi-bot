# ================= TEXT HANDLER =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lang = context.user_data.get("lang", "uz")

    # ================= LINK BO'LSA =================
    if text.startswith("http"):

        loading_msg = await update.message.reply_text(TEXTS[lang]["downloading"])

        ydl_opts = {
            "format": "best",
            "outtmpl": "video_%(id)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "nocheckcertificate": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0"
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                filename = ydl.prepare_filename(info)

            await update.message.reply_video(
                video=open(filename, "rb"),
                caption=TEXTS[lang]["done"]
            )

            await loading_msg.delete()   # ⏳ o‘chadi
            os.remove(filename)

        except Exception as e:
            await loading_msg.delete()   # xatoda ham ⏳ o‘chadi
            await update.message.reply_text("❌ Yuklab bo‘lmadi")
        return

    # ================= QO‘SHIQ QIDIRISH =================
    searching_msg = await update.message.reply_text(TEXTS[lang]["searching"])

    try:
        with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
            result = ydl.extract_info(f"ytsearch10:{text}", download=False)
    except:
        await searching_msg.delete()   # 🔎 o‘chadi
        await update.message.reply_text(TEXTS[lang]["error"])
        return

    entries = result.get("entries", [])[:10]

    if not entries:
        await searching_msg.delete()   # 🔎 o‘chadi
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

    await searching_msg.delete()   # 🔎 o‘chadi

    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
