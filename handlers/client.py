from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database.db import (
    get_or_create_client, create_order, get_orders_by_user,
    create_booking, clear_chat_history
)
from utils.keyboards import main_menu_keyboard, persons_keyboard, cancel_keyboard
from utils.ai_assistant import get_ai_response

# Состояния для заказа
ORDER_DESCRIPTION, ORDER_ADDRESS = range(2)

# Состояния для бронирования
BOOKING_NAME, BOOKING_PHONE, BOOKING_DATE, BOOKING_TIME, BOOKING_PERSONS, BOOKING_COMMENT = range(10, 16)

FAQ_TEXT = """
🍓 *Часто задаваемые вопросы — Strawberry_Diora*

*📦 Как сделать заказ?*
Нажмите кнопку «📦 Заказать» в меню и следуйте инструкциям.

*🚀 Сколько времени занимает доставка?*
От 30 до 60 минут в зависимости от вашего района.

*💳 Какие способы оплаты доступны?*
Наличные, банковская карта, онлайн-оплата.

*📅 Как забронировать стол?*
Нажмите «📅 Бронирование» и заполните форму.

*⏰ Режим работы:*
Ежедневно с 09:00 до 22:00

*📞 Если остались вопросы — напишите нам или позвоните!*
"""

CONTACTS_TEXT = """
📞 *Контакты Strawberry_Diora* 🍓

📱 Телефон: +7 (XXX) XXX-XX-XX
📧 Email: info@strawberry-diora.ru
📍 Адрес: г. Москва, ул. Примерная, д. 1
🌐 Сайт: www.strawberry-diora.ru

⏰ Работаем: 09:00 — 22:00 (ежедневно)

💬 Или просто напишите нам прямо здесь!
"""


# ─── СТАРТ / МЕНЮ ──────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await get_or_create_client(user.id, user.full_name, user.username)

    await update.message.reply_text(
        f"👋 Добро пожаловать в *Strawberry_Diora* 🍓, {user.first_name}!\n\n"
        "Я — ваш персональный помощник. Чем могу помочь?\n\n"
        "Выберите действие в меню ниже 👇",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )


async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(FAQ_TEXT, parse_mode="Markdown")


async def contacts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(CONTACTS_TEXT, parse_mode="Markdown")


# ─── МОИ ЗАКАЗЫ ────────────────────────────────────────────

async def my_orders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    orders = await get_orders_by_user(user.id)

    if not orders:
        await update.message.reply_text(
            "У вас пока нет заказов. Нажмите *📦 Заказать*, чтобы сделать первый! 🍓",
            parse_mode="Markdown"
        )
        return

    status_emoji = {
        "new": "🆕",
        "accepted": "✅",
        "delivery": "🚀",
        "done": "✔️",
        "cancelled": "❌"
    }
    status_text = {
        "new": "Новый",
        "accepted": "Принят",
        "delivery": "В доставке",
        "done": "Выполнен",
        "cancelled": "Отменён"
    }

    text = "📋 *Ваши последние заказы:*\n\n"
    for order in orders:
        emoji = status_emoji.get(order["status"], "❓")
        status = status_text.get(order["status"], order["status"])
        text += (
            f"{emoji} *Заказ #{order['id']}*\n"
            f"📝 {order['description']}\n"
            f"📍 {order['address']}\n"
            f"📌 Статус: {status}\n"
            f"🕐 {order['created_at'][:16]}\n\n"
        )

    await update.message.reply_text(text, parse_mode="Markdown")


# ─── ОФОРМЛЕНИЕ ЗАКАЗА ─────────────────────────────────────

async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📦 *Оформление заказа*\n\n"
        "Напишите, что хотите заказать (блюда, количество):\n\n"
        "_Например: 2 пиццы Маргарита, 1 бургер, 2 коки_",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    return ORDER_DESCRIPTION


async def order_get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order_description"] = update.message.text
    await update.message.reply_text(
        "📍 Отлично! Теперь укажите адрес доставки:\n\n"
        "_Например: ул. Ленина, д. 5, кв. 12, домофон 12#_",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    return ORDER_ADDRESS


async def order_get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    description = context.user_data.get("order_description", "")
    address = update.message.text

    order_id = await create_order(user.id, description, address)

    await update.message.reply_text(
        f"✅ *Заказ #{order_id} принят!*\n\n"
        f"📝 {description}\n"
        f"📍 {address}\n\n"
        "Наш оператор свяжется с вами для подтверждения. "
        "Среднее время доставки — 30-60 минут 🚀",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

    # Уведомляем администраторов
    admin_ids = context.bot_data.get("admin_ids", [])
    from utils.keyboards import order_status_keyboard
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"🆕 *Новый заказ #{order_id}*\n\n"
                    f"👤 Клиент: {user.full_name} (@{user.username or 'нет'})\n"
                    f"📝 {description}\n"
                    f"📍 {address}"
                ),
                parse_mode="Markdown",
                reply_markup=order_status_keyboard(order_id)
            )
        except Exception:
            pass

    return ConversationHandler.END


# ─── БРОНИРОВАНИЕ ──────────────────────────────────────────

async def booking_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📅 *Бронирование стола*\n\n"
        "Введите ваше имя:",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    return BOOKING_NAME


async def booking_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["booking_name"] = update.message.text
    await update.message.reply_text(
        "📞 Введите ваш номер телефона:",
        reply_markup=cancel_keyboard()
    )
    return BOOKING_PHONE


async def booking_get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["booking_phone"] = update.message.text
    await update.message.reply_text(
        "📆 Введите дату бронирования:\n_Формат: ДД.ММ.ГГГГ (например: 25.07.2024)_",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    return BOOKING_DATE


async def booking_get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["booking_date"] = update.message.text
    await update.message.reply_text(
        "🕐 Введите желаемое время:\n_Формат: ЧЧ:ММ (например: 19:00)_",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    return BOOKING_TIME


async def booking_get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["booking_time"] = update.message.text
    await update.message.reply_text(
        "👥 Сколько человек?",
        reply_markup=persons_keyboard()
    )
    return BOOKING_PERSONS


async def booking_get_persons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    persons = int(query.data.split("_")[1])
    context.user_data["booking_persons"] = persons
    await query.message.reply_text(
        "💬 Есть пожелания или комментарии? (или напишите «нет»):",
        reply_markup=cancel_keyboard()
    )
    return BOOKING_COMMENT


async def booking_get_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    comment = update.message.text
    if comment.lower() in ("нет", "no", "-"):
        comment = ""

    data = context.user_data
    booking_id = await create_booking(
        telegram_id=user.id,
        name=data["booking_name"],
        phone=data["booking_phone"],
        date=data["booking_date"],
        time=data["booking_time"],
        persons=data["booking_persons"],
        comment=comment
    )

    await update.message.reply_text(
        f"✅ *Бронирование #{booking_id} оформлено!*\n\n"
        f"👤 {data['booking_name']}\n"
        f"📞 {data['booking_phone']}\n"
        f"📆 {data['booking_date']} в {data['booking_time']}\n"
        f"👥 {data['booking_persons']} чел.\n"
        f"💬 {comment or 'нет'}\n\n"
        "Мы подтвердим бронирование в ближайшее время! 🍓",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )

    # Уведомляем администраторов
    admin_ids = context.bot_data.get("admin_ids", [])
    from utils.keyboards import booking_action_keyboard
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"📅 *Новое бронирование #{booking_id}*\n\n"
                    f"👤 {data['booking_name']}\n"
                    f"📞 {data['booking_phone']}\n"
                    f"📆 {data['booking_date']} в {data['booking_time']}\n"
                    f"👥 {data['booking_persons']} чел.\n"
                    f"💬 {comment or 'нет'}"
                ),
                parse_mode="Markdown",
                reply_markup=booking_action_keyboard(booking_id)
            )
        except Exception:
            pass

    return ConversationHandler.END


# ─── AI ЧАТ ────────────────────────────────────────────────

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных текстовых сообщений — отправляем в AI"""
    user = update.effective_user
    text = update.message.text

    # Исключаем кнопки меню
    menu_buttons = {"📦 Заказать", "📅 Бронирование", "🔍 Мои заказы",
                    "❓ FAQ", "📞 Контакты", "💬 Написать нам",
                    "📋 Заказы", "📅 Брони", "✅ Задачи",
                    "📊 Статистика", "👥 Клиенты", "⚙️ Настройки"}
    if text in menu_buttons:
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )
    response = await get_ai_response(user.id, text)
    await update.message.reply_text(response)


async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await clear_chat_history(update.effective_user.id)
    await update.message.reply_text("🔄 История диалога очищена!")


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text(
            "❌ Действие отменено.",
            reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ Действие отменено.",
            reply_markup=main_menu_keyboard()
        )
    context.user_data.clear()
    return ConversationHandler.END
