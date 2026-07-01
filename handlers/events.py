from aiogram import Router
from aiogram.types import CallbackQuery

from services.football_api import get_events

router = Router()


@router.callback_query(lambda c: c.data.startswith("events_"))
async def show_events(callback: CallbackQuery):

    fixture_id = callback.data.split("_")[1]

    data = get_events(fixture_id)

    if not data:
        await callback.message.answer("❌ Не удалось получить события.")
        await callback.answer()
        return

    events = data["response"]

    if len(events) == 0:
        await callback.message.answer("📋 События пока отсутствуют.")
        await callback.answer()
        return

    text = "📋 События матча\n\n"

    icons = {
        "Goal": "⚽",
        "Card": "🟨",
        "subst": "🔄",
        "Var": "📺"
    }

    for event in events:

        minute = event["time"]["elapsed"]

        team = event["team"]["name"]

        player = event["player"]["name"] if event["player"] else ""

        event_type = event["type"]

        detail = event["detail"]

        icon = icons.get(event_type, "📌")

        text += (
            f"{icon} {minute}'\n"
            f"{team}\n"
            f"{player}\n"
            f"{detail}\n\n"
        )

    if len(text) > 4000:
        text = text[:3900] + "\n..."

    await callback.message.answer(text)

    await callback.answer()