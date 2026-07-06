import anthropic
import os
from database.db import get_chat_history, save_message

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a friendly assistant for Strawberry Diora 🍓 — a chocolate-covered strawberry delivery brand.

Your role:
- Answer customer questions politely and professionally
- Help with orders, delivery, toppings, and reservations
- Resolve issues and complaints

About the brand:
- Name: Strawberry Diora 🍓
- Product: chocolate-covered strawberry sets
- Sets: Diora XS (4 pcs, 140 Rp), Diora S (12-15 pcs, 420 Rp), Diora M (20-23 pcs, 650 Rp)
- Toppings: Peanut, Coconut, Oreo (free)
- Extras: Fresh berries +90 Rp
- Working hours: 09:00 — 22:00 daily
- Delivery: 30-60 minutes

Rules:
- Always be friendly and professional
- Use emojis moderately
- If unsure — offer to connect with a manager
- For orders tap the Catalog button, for reservations tap the Reservation button
"""


async def get_ai_response(telegram_id: int, user_message: str) -> str:
    await save_message(telegram_id, "user", user_message)
    history = await get_chat_history(telegram_id, limit=10)
    messages = [{"role": msg["role"], "content": msg["message"]} for msg in history]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        ai_reply = response.content[0].text
        await save_message(telegram_id, "assistant", ai_reply)
        return ai_reply
    except Exception as e:
        print(f"AI Error: {e}")
        return "Sorry, something went wrong. Please try again later or contact us directly. 🙏"
