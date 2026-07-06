from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
from database.db import (
    get_or_create_client, get_orders_by_user,
    create_booking, clear_chat_history, update_order_status
)
from utils.keyboards import main_menu_keyboard, persons_keyboard, cancel_keyboard
from utils.ai_assistant import get_ai_response
from handlers.catalog import show_catalog, show_cart, handle_address

BOOKING_NAME, BOOKING_PHONE, BOOKING_DATE, BOOKING_TIME, BOOKING_PERSONS, BOOKING_COMMENT = range(10, 16)

ADMIN_USERNAME = "patsevoleg"

FAQ_TEXT = (
    "Strawberry Diora 🍓 — Частые вопросы\n\n"
    "Как сделать заказ?\n"
    "Нажми «Каталог», выбери сет, добавь в корзину и оформи заказ.\n\n"
    "Сколько времени занимает доставка?\n"
    "От 30 до 60 минут в зависимости от района.\n\n"
    "Способы оплаты:\n"
    "Наличные, банковская карта, онлайн-оплата.\n\n"
    "Как забронировать стол?\n"
    "Нажми «Бронирование» и заполни форму.\n\n"
    "Режим работы:\n"
    "Ежедневно 09:00 — 22:00"
)

CONTACTS_TEXT = (
    "Strawberry Diora 🍓 — Контакты\n\n"
    "Телефон: +7 (XXX) XXX-XX-XX\n"
    "Адрес: г. Москва, ул. Примерная, д. 1\n"
    "Работаем: 09:00 — 22:00 (ежедневно)"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await get_or_create_client(user.id, user.full_name, user.username)
    await update.message.reply_text(
        f"👋 Добро пожаловать в Strawberry Diora 🍓, {user.first_name}!\n\n"
        "Выбери действие в меню 👇",
        reply_markup=main_menu_keyboard()
    )


async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(FAQ_TEXT)


async def contacts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(CONTACTS_TEXT)


async def support_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Написать нам", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])
    await update.message.reply_text(
        "Нажми кнопку ниже чтобы написать нам напрямую:",
        reply_markup=keyboard
    )


async def my_orders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    orders = await get_orders_by_user(user.id)
    if not orders:
        await update.message.reply_text(
            "У вас пока нет заказов. Нажмите 🛍 Каталог, чтобы сделать первый! 🍓"
        )
        return

    status_emoji = {"new": "🆕", "accepted": "✅", "delivery": "🚀", "done": "✔️", "cancelled": "❌"}
    status_text = {"new": "Новый", "accepted": "Принят", "delivery": "В доставке", "done": "Выполнен", "cancelled": "Отменён"}
    cancellable = {"new", "accepted"}

    await update.message.reply_text("📋 Ваши последние заказы:")
    for order in orders:
        emoji = status_emoji.get(order["status"], "❓")
        status = status_text.get(order["status"], order["status"])
        text = (
            f"{emoji} Заказ #{order['id']}\n"
            f"Статус: {status}\n"
            f"Время: {order['created_at'][:16]}"
        )
        if order["status"] in cancellable:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Отменить заказ", callback_data=f"client_cancel_{order['id']}")]
            ])
            await update.message.reply_text(text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text)


async def client_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.split("_")[2])
    await update_order_status(order_id, "cancelled")
    await query.edit_message_text(
        f"❌ Заказ #{order_id} отменён.\n\nЕсли это ошибка — свяжитесь с нами."
    )
    admin_ids = context.bot_data.get("admin_ids", [])
    user = query.from_user
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"❌ Order #{order_id} cancelled by client\n\n"
                    f"Client: {user.full_name} (@{user.username or '-'})"
                )
            )
        except Exception:
            pass


# ─── БРОНИРОВАНИЕ ──────────────────────────────────────────

async def booking_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Бронирование стола\n\nВведите ваше имя:", reply_markup=cancel_keyboard())
    return BOOKING_NAME

async def booking_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["booking_name"] = update.message.text
    await update.message.reply_text("📞 Введите номер телефона:", reply_markup=cancel_keyboard())
    return BOOKING_PHONE

async def booking_get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["booking_phone"] = update.message.text
    await update.message.reply_text("📆 Введите дату:\nФормат: ДД.ММ.ГГГГ", reply_markup=cancel_keyboard())
    return BOOKING_DATE

async def booking_get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["booking_date"] = update.message.text
    await update.message.reply_text("🕐 Введите время:\nФормат: ЧЧ:ММ", reply_markup=cancel_keyboard())
    return BOOKING_TIME

async def booking_get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["booking_time"] = update.message.text
    await update.message.reply_text("👥 Сколько человек?", reply_markup=persons_keyboard())
    return BOOKING_PERSONS

async def booking_get_persons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["booking_persons"] = int(query.data.split("_")[1])
    await query.message.reply_text("💬 Пожелания? (или напишите «нет»):", reply_markup=cancel_keyboard())
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
        f"✅ Бронирование #{booking_id} оформлено!\n\n"
        f"Имя: {data['booking_name']}\n"
        f"Дата: {data['booking_date']} в {data['booking_time']}\n"
        f"Гостей: {data['booking_persons']}\n\n"
        "Подтвердим в ближайшее время! 🍓",
        reply_markup=main_menu_keyboard()
    )
    admin_ids = context.bot_data.get("admin_ids", [])
    from utils.keyboards import booking_action_keyboard
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"New Booking #{booking_id}\n\n"
                    f"Name: {data['booking_name']}\n"
                    f"Phone: {data['booking_phone']}\n"
                    f"Date: {data['booking_date']} at {data['booking_time']}\n"
                    f"Guests: {data['booking_persons']}\n"
                    f"Comment: {comment or 'none'}"
                ),
                reply_markup=booking_action_keyboard(booking_id)
            )
        except Exception:
            pass
    return ConversationHandler.END


# ─── AI ЧАТ ────────────────────────────────────────────────

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    menu_buttons = {
        "🛍 Каталог", "🛒 Корзина", "📅 Бронирование", "🔍 Мои заказы",
        "❓ FAQ", "📞 Контакты", "💬 Поддержка",
        "📋 Orders", "📅 Bookings", "✅ Tasks", "📊 Statistics"
    }
    if text in menu_buttons:
        return

    if await handle_address(update, context):
        return

    # Проверяем ссылку Google Maps
    from handlers.catalog import handle_maps_url
    from utils.delivery import is_google_maps_url
    if is_google_maps_url(text) and await handle_maps_url(update, context):
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    response = await get_ai_response(user.id, text)
    await update.message.reply_text(response)


async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await clear_chat_history(update.effective_user.id)
    await update.message.reply_text("🔄 История диалога очищена!")


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await query.message.reply_text("❌ Отменено.", reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text("❌ Отменено.", reply_markup=main_menu_keyboard())
    context.user_data.clear()
    return ConversationHandler.END
