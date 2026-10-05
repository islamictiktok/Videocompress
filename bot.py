import os
import subprocess
from pyrogram import Client, filters

# قراءة المتغيرات من بيئة Railway
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client(
    "video_compressor_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

def compress_video(input_path, output_path):
    # استخدام preset أسرع لتسريع الضغط مع الحفاظ على الكفاءة
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx265",
        "-preset", "superfast",  # تم التغيير من medium لزيادة سرعة المعالجة
        "-crf", "30",
        "-c:a", "aac",
        "-b:a", "96k",
        "-movflags", "+faststart",
        output_path
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return os.path.exists(output_path) and os.path.getsize(output_path) > 0

@app.on_message(filters.video | filters.document)
async def handle_video(client, message):
    # التأكد من أن الملف هو فيديو
    if message.document and not message.document.mime_type.startswith('video/'):
        await message.reply("⚠️ أرسل ملفات الفيديو فقط.")
        return

    msg = await message.reply("📥 جاري التنزيل بأقصى سرعة...")
    
    try:
        # مسار التنزيل
        file_path = await message.download()
        original_size = os.path.getsize(file_path) / (1024 * 1024)
        
        await msg.edit(f"⚙️ جاري ضغط الفيديو (الحجم الأصلي: {original_size:.2f} MB)...")
        
        out_path = f"{file_path}_compressed.mp4"
        success = compress_video(file_path, out_path)
        
        if success:
            new_size = os.path.getsize(out_path) / (1024 * 1024)
            saving = (1 - (new_size / original_size)) * 100
            
            await msg.edit("🚀 جاري الرفع...")
            
            caption = (
                f"✅ تم الضغط بنجاح!\n"
                f"📉 الحجم السابق: {original_size:.2f} MB\n"
                f"📈 الحجم الجديد: {new_size:.2f} MB\n"
                f"🔥 نسبة التوفير: {saving:.1f}%"
            )
            
            # رفع الفيديو كرسالة فيديو مباشرة
            await message.reply_video(video=out_path, caption=caption)
            os.remove(out_path)
        else:
            await msg.edit("❌ فشلت عملية الضغط.")
            
    except Exception as e:
        await msg.edit(f"❌ حدث خطأ: {str(e)}")
        
    finally:
        # تنظيف الملفات المؤقتة لتجنب امتلاء مساحة السيرفر
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    print("🤖 البوت يعمل الآن...")
    app.run()
