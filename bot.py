import os
import subprocess
import telebot

# استدعاء التوكن فقط من بيئة Railway
BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

def compress_video(input_path, output_path):
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx265",
        "-preset", "superfast",
        "-crf", "30",
        "-c:a", "aac",
        "-b:a", "96k",
        "-movflags", "+faststart",
        output_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 0

@bot.message_handler(content_types=['video', 'document'])
def handle_video(message):
    # التأكد من أن الملف فيديو إذا تم إرساله كمستند
    if message.content_type == 'document' and not message.document.mime_type.startswith('video/'):
        bot.reply_to(message, "⚠️ أرسل ملفات الفيديو فقط.")
        return

    # التحقق من الحجم (الحد الأقصى 20 ميجابايت عبر Bot API)
    file_size = message.video.file_size if message.content_type == 'video' else message.document.file_size
    if file_size > 20 * 1024 * 1024:
        bot.reply_to(message, "❌ حجم الملف يتجاوز 20 ميجابايت (الحد الأقصى المسموح به للبوتات بدون استخدام حساب شخصي).")
        return

    msg = bot.reply_to(message, "📥 جاري التنزيل...")
    
    input_path = ""
    output_path = ""
    
    try:
        # الحصول على مسار الملف من سيرفر تيليجرام وتنزيله
        file_id = message.video.file_id if message.content_type == 'video' else message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_path = f"{file_id}.mp4"
        output_path = f"{file_id}_compressed.mp4"
        
        with open(input_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        original_size = os.path.getsize(input_path) / (1024 * 1024)
        bot.edit_message_text(f"⚙️ جاري ضغط الفيديو (الحجم الأصلي: {original_size:.2f} MB)...", chat_id=msg.chat.id, message_id=msg.message_id)
        
        success = compress_video(input_path, output_path)
        
        if success:
            new_size = os.path.getsize(output_path) / (1024 * 1024)
            saving = (1 - (new_size / original_size)) * 100
            
            bot.edit_message_text("🚀 جاري الرفع...", chat_id=msg.chat.id, message_id=msg.message_id)
            
            caption = (
                f"✅ تم الضغط بنجاح!\n"
                f"📉 الحجم السابق: {original_size:.2f} MB\n"
                f"📈 الحجم الجديد: {new_size:.2f} MB\n"
                f"🔥 نسبة التوفير: {saving:.1f}%"
            )
            
            with open(output_path, 'rb') as video_file:
                bot.send_video(message.chat.id, video_file, caption=caption, reply_to_message_id=message.message_id)
        else:
            bot.edit_message_text("❌ فشلت عملية الضغط.", chat_id=msg.chat.id, message_id=msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ: {str(e)}", chat_id=msg.chat.id, message_id=msg.message_id)
        
    finally:
        # تنظيف مساحة السيرفر بعد الانتهاء
        if input_path and os.path.exists(input_path): os.remove(input_path)
        if output_path and os.path.exists(output_path): os.remove(output_path)

if __name__ == "__main__":
    print("🤖 البوت يعمل الآن باستخدام التوكن فقط...")
    bot.infinity_polling()
