import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from handlers.start import router as start_router
from handlers.live import router as live_router
load_dotenv()
import os

print("BOT =", os.getenv("BOT_TOKEN"))
print("API =", os.getenv("FOOTBALL_API_KEY"))
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(live_router)

async def main():
    print("=" * 40)
    print("🚀 MATCHLINE AI VERSION 0.2")
    print("=" * 40)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())