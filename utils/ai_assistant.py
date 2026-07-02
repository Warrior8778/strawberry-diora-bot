import anthropic
import os
from database.db import get_chat_history, save_message

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Ты — умный администратор-помощник компании Strawberry_Diora 🍓 (доставка еды).

Твоя роль:
- Вежливо и профессионально общаться с клиентами
- Отвечать на вопросы о меню, доставке, оплате, бронированиях
- Помогать оформлять заказы и бронирования
- Решать проблемы и жалобы клиентов

Информация о компании:
- Название: Strawberry_Diora 🍓
- Направление: доставка еды / ресторан
- Режим работы: 09:00 — 22:00
- Доставка: по городу, от 30 минут
- Минимальный заказ: уточнять у оператора
- Оплата: наличные, карта, онлайн

Правила общения:
- Всегда будь дружелюбным и на "вы" с клиентами
- Используй эмодзи умеренно
- Если не знаешь ответа — предложи связаться с оператором
- На вопросы о ценах на конкретные блюда — говори что уточнишь у менеджера

Если клиент хочет сделать заказ — попроси его нажать кнопку "📦 Заказ" в меню.
Если хочет забронировать стол — кнопку "📅 Бронирование".
"""


async def get_ai_response(telegram_id: int, user_message: str) -> str:
    """Получить ответ от AI с учётом истории диалога"""
    # Сохраняем сообщение пользователя
    await save_message(telegram_id, "user", user_message)

    # Получаем историю
    history = await get_chat_history(telegram_id, limit=10)

    messages = [
        {"role": msg["role"], "content": msg["message"]}
        for msg in history
    ]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=messages
        )

        ai_reply = response.content[0].text

        # Сохраняем ответ AI
        await save_message(telegram_id, "assistant", ai_reply)

        return ai_reply

    except Exception as e:
        print(f"AI Error: {e}")
        return ("Извините, произошла ошибка. Пожалуйста, попробуйте позже "
                "или свяжитесь с нами напрямую. 🙏")
