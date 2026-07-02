import os
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, filters
from database.db import (
    get_all_orders, update_order_status,
    get_pending_bookings, update_booking_status,
    get_open_tasks, create_task, close_task
)
from utils.keyboards import (
    admin_menu_keyboard, order_status_keyboard,
    booking_action_keyboard, task_done_keyboard
)

# Состояния для создания задачи
TASK_TITLE, TASK_DESC, TASK_PRIORITY = range(20, 23)


def is_admin(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    admin_ids = context.bot_data.get("admin_ids", [])
    return user_id in admin_ids


# ─── ГЛАВНОЕ МЕНЮ АДМНА ────────────────────────────────────

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        await update.message.reply_text("⛔ У вас нет доступа к панели администратора.")
        return

    await update.message.reply_text(
        "🛠 *Панель администратора — Strawberry_Diora* 🍓\n\nВыберите раздел:",
        parse_mode="Markdown",
        reply_markup=admin_menu_keyboard()
    )


# ─── ЗАКАЗЫ ────────────────────────────────────────────────

async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return

    orders = await get_all_orders(status="new")
    if not orders:
        await update.message.reply_text("✅ Новых заказов нет!")
        return

    await update.message.reply_text(f"📋 *Новые заказы ({len(orders)}):*", parse_mode="Markdown")

    for order in orders[:10]:  # Максимум 10 за раз
        await update.message.reply_text(
            f"🆕 *Заказ #{order['id']}*\n"
            f"📝 {order['description']}\n"
            f"📍 {order['address']}\n"
            f"🕐 {order['created_at'][:16]}",
            parse_mode="Markdown",
            reply_markup=order_status_keyboard(order["id"])
        )


# ─── БРОНИРОВАНИЯ ──────────────────────────────────────────

async def admin_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return

    bookings = await get_pending_bookings()
    if not bookings:
        await update.message.reply_text("✅ Ожидающих бронирований нет!")
        return

    await update.message.reply_text(
        f"📅 *Ожидающие бронирования ({len(bookings)}):*",
        parse_mode="Markdown"
    )

    for b in bookings:
        await update.message.reply_text(
            f"📅 *Бронирование #{b['id']}*\n"
            f"👤 {b['name']}\n"
            f"📞 {b['phone']}\n"
            f"📆 {b['date']} в {b['time']}\n"
            f"👥 {b['persons']} чел.\n"
            f"💬 {b['comment'] or 'нет'}",
            parse_mode="Markdown",
            reply_markup=booking_action_keyboard(b["id"])
        )


# ─── ЗАДАЧИ ────────────────────────────────────────────────

async def admin_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return

    tasks = await get_open_tasks()
    if not tasks:
        await update.message.reply_text("✅ Открытых задач нет!")
        return

    priority_emoji = {"high": "🔴", "normal": "🟡", "low": "🟢"}

    await update.message.reply_text(
        f"✅ *Открытые задачи ({len(tasks)}):*",
        parse_mode="Markdown"
    )

    for task in tasks:
        emoji = priority_emoji.get(task["priority"], "⚪")
        await update.message.reply_text(
            f"{emoji} *Задача #{task['id']}*\n"
            f"📌 {task['title']}\n"
            f"📝 {task['description']}\n"
            f"🕐 {task['created_at'][:16]}",
            parse_mode="Markdown",
            reply_markup=task_done_keyboard(task["id"])
        )


async def create_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return ConversationHandler.END

    await update.message.reply_text(
        "📝 *Создание задачи*\n\nВведите название задачи:",
        parse_mode="Markdown"
    )
    return TASK_TITLE


async def task_get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_title"] = update.message.text
    await update.message.reply_text("📋 Введите описание задачи:")
    return TASK_DESC


async def task_get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_desc"] = update.message.text
    await update.message.reply_text(
        "🎯 Приоритет:\nВведите: *высокий*, *обычный* или *низкий*",
        parse_mode="Markdown"
    )
    return TASK_PRIORITY


async def task_get_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    priority_map = {
        "высокий": "high", "high": "high",
        "обычный": "normal", "normal": "normal",
        "низкий": "low", "low": "low"
    }
    priority = priority_map.get(update.message.text.lower(), "normal")

    task_id = await create_task(
        title=context.user_data["task_title"],
        description=context.user_data["task_desc"],
        created_by=update.effective_user.id,
        priority=priority
    )

    await update.message.reply_text(
        f"✅ *Задача #{task_id} создана!*\n"
        f"📌 {context.user_data['task_title']}",
        parse_mode="Markdown",
        reply_markup=admin_menu_keyboard()
    )
    return ConversationHandler.END


# ─── CALLBACK ОБРАБОТЧИКИ ──────────────────────────────────

async def order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id, context):
        await query.answer("⛔ Нет доступа", show_alert=True)
        return

    data = query.data
    parts = data.split("_")
    action = parts[1]
    order_id = int(parts[2])

    status_map = {
        "accept": "accepted",
        "delivery": "delivery",
        "done": "done",
        "cancel": "cancelled"
    }
    status_labels = {
        "accepted": "✅ Принят",
        "delivery": "🚀 В доставке",
        "done": "✔️ Выполнен",
        "cancelled": "❌ Отменён"
    }

    new_status = status_map.get(action, "new")
    await update_order_status(order_id, new_status)

    label = status_labels.get(new_status, new_status)
    await query.edit_message_text(
        f"{query.message.text}\n\n🔄 Статус обновлён: *{label}*",
        parse_mode="Markdown"
    )


async def booking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id, context):
        await query.answer("⛔ Нет доступа", show_alert=True)
        return

    data = query.data
    parts = data.split("_")
    action = parts[1]
    booking_id = int(parts[2])

    if action == "confirm":
        await update_booking_status(booking_id, "confirmed")
        await query.edit_message_text(
            f"{query.message.text}\n\n✅ *Бронирование подтверждено!*",
            parse_mode="Markdown"
        )
    elif action == "reject":
        await update_booking_status(booking_id, "rejected")
        await query.edit_message_text(
            f"{query.message.text}\n\n❌ *Бронирование отклонено.*",
            parse_mode="Markdown"
        )


async def task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id, context):
        await query.answer("⛔ Нет доступа", show_alert=True)
        return

    task_id = int(query.data.split("_")[2])
    await close_task(task_id)
    await query.edit_message_text(
        f"{query.message.text}\n\n✔️ *Задача выполнена!*",
        parse_mode="Markdown"
    )
