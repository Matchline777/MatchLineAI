import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from handlers.start import router as start_router
from handlers.live import router as live_router
from handlers.statistics import router as statistics_router
from handlers.events import router as events_router
from handlers.ai import router as ai_router
from services.live_scanner import scan_live_matches
from services.result_checker import check_finished_matches

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
SIGNAL_CHAT_ID = os.getenv("SIGNAL_CHAT_ID")

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(live_router)
dp.include_router(statistics_router)
dp.include_router(events_router)
dp.include_router(ai_router)


async def main():
    print("=" * 40)
    print("🚀 MATCHLINE AI VERSION 0.4")
    print("=" * 40)

    asyncio.create_task(
        scan_live_matches(bot, SIGNAL_CHAT_ID)
    )
    asyncio.create_task(
        check_finished_matches()
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
