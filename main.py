import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
import yt_dlp
from aiohttp import web  # Thêm cái này để làm Fake Server

# --- CONFIG ---
TOKEN = '8149933374:AAG4Eww9ASKbAkL9zx5lrVkgsz4y_i3IXLQ' # Cẩn thận lộ token nhé Boss
logging.basicConfig(level=logging.INFO)

# Khởi tạo Bot
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- CÔNG CỤ TẢI VIDEO ---
async def download_tiktok_video(url):
    output_filename = f"video_{int(asyncio.get_event_loop().time())}.mp4"
    ydl_opts = {
        'outtmpl': output_filename,
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        # Fake User-Agent để tránh bị TikTok chặn IP server
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: _yt_download(ydl_opts, url))
        return output_filename
    except Exception as e:
        logging.error(f"Download shit happened: {e}")
        return None

def _yt_download(opts, url):
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

# --- HANDLERS ---
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.answer("🚀 **V-System TikTok Downloader**\n\nNém link vào đây Boss ơi.")

@dp.message(F.text.contains("tiktok.com"))
async def handle_tiktok(message: types.Message):
    url = message.text.strip()
    status_msg = await message.answer("⚡ Đang xử lý... Boss đợi V một chút.")
    
    video_path = await download_tiktok_video(url)
    
    if not video_path or not os.path.exists(video_path):
        await status_msg.edit_text("☠️ TikTok nó chặn IP server rồi Boss ạ. Thử lại sau.")
        return

    await status_msg.edit_text("⬆️ Đang upload...")
    try:
        video_file = FSInputFile(video_path)
        await message.answer_video(
            video=video_file, 
            caption="✅ Của Boss đây.",
            reply_to_message_id=message.message_id
        )
    except Exception as e:
        await message.answer(f"Shit, lỗi upload: {e}")
    finally:
        await status_msg.delete()
        if os.path.exists(video_path):
            os.remove(video_path)

# --- FAKE WEB SERVER (Để lừa Render) ---
async def handle_ping(request):
    return web.Response(text="I'm alive, Boss! Don't kill me.")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render sẽ cấp cổng qua biến môi trường PORT, mặc định là 10000 nếu test local
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Fake Server running on port {port}")

# --- ENTRY POINT ---
async def main():
    # Chạy song song cả Web Server và Bot Polling
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())