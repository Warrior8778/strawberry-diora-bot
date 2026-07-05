from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database.db import (
    get_all_orders, update_order_status,
    get_pending_bookings, update_booking_status,
    get_open_tasks, create_task, close_task
)
from utils.keyboards import (
    admin_menu_keyboard, order_status_keyboard,
    booking_action_keyboard, task_done_keyboard
)
import aiosqlite
from datetime import datetime, timedelta

TASK_TITLE, TASK_DESC, TASK_PRIORITY = range(20, 23)
DB_PATH = "strawberry_diora.db"


def is_admin(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    return user_id in context.bot_data.get("admin_ids", [])


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        await update.message.reply_text("Нет доступа.")
        return
    await update.message.reply_text(
        "Панель администратора Strawberry Diora 🍓\n\nВыберите раздел:",
        reply_markup=admin_menu_keyboard()
    )


# ─── ЗАКАЗЫ ────────────────────────────────────────────────

async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 Новые", callback_data="orders_new"),
         InlineKeyboardButton("✅ Принятые", callback_data="orders_accepted")],
        [InlineKeyboardButton("🚀 В доставке", callback_data="orders_delivery"),
         InlineKeyboardButton("📋 История", callback_data="orders_history")],
    ])
    await update.message.reply_text("Выбери раздел заказов:", reply_markup=keyboard)


async def orders_section_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id, context):
        return

    section = query.data.split("_")[1]

    status_map = {
        "new": ("new", "🆕 Новые заказы"),
        "accepted": ("accepted", "✅ Принятые заказы"),
        "delivery": ("delivery", "🚀 Заказы в доставке"),
        "history": (None, "📋 История заказов"),
    }

    status, title = status_map.get(section, (None, "Заказы"))

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if section == "history":
            async with db.execute(
                "SELECT * FROM orders WHERE status IN ('done','cancelled') ORDER BY updated_at DESC LIMIT 30"
            ) as cursor:
                orders = [dict(r) for r in await cursor.fetchall()]
        else:
            async with db.execute(
                "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC LIMIT 20",
                (status,)
            ) as cursor:
                orders = [dict(r) for r in await cursor.fetchall()]

    if not orders:
        await query.edit_message_text(f"{title}\n\nЗаказов нет.")
        return

    await query.edit_message_text(f"{title} ({len(orders)}):")

    status_labels = {
        "new": "Новый", "accepted": "Принят",
        "delivery": "В доставке", "done": "Выполнен", "cancelled": "Отменён"
    }

    for order in orders:
        status_label = status_labels.get(order["status"], order["status"])
        text = (
            f"Заказ #{order['id']} — {status_label}\n"
            f"{order['description']}\n"
            f"Адрес: {order['address']}\n"
            f"Время: {order['created_at'][:16]}"
        )
        if order["status"] in ("new", "accepted", "delivery"):
            await query.message.reply_text(text, reply_markup=order_status_keyboard(order["id"]))
        else:
            await query.message.reply_text(text)


# ─── БРОНИРОВАНИЯ ──────────────────────────────────────────

async def admin_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return
    bookings = await get_pending_bookings()
    if not bookings:
        await update.message.reply_text("Ожидающих бронирований нет!")
        return
    await update.message.reply_text(f"Бронирования ({len(bookings)}):")
    for b in bookings:
        await update.message.reply_text(
            f"Бронирование #{b['id']}\n"
            f"Имя: {b['name']}\n"
            f"Тел: {b['phone']}\n"
            f"Дата: {b['date']} в {b['time']}\n"
            f"Гостей: {b['persons']}\n"
            f"Коммент: {b['comment'] or 'нет'}",
            reply_markup=booking_action_keyboard(b["id"])
        )


# ─── ЗАДАЧИ ────────────────────────────────────────────────

async def admin_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return
    tasks = await get_open_tasks()
    if not tasks:
        await update.message.reply_text("Открытых задач нет!")
        return
    await update.message.reply_text(f"Открытые задачи ({len(tasks)}):")
    for task in tasks:
        await update.message.reply_text(
            f"Задача #{task['id']}\n"
            f"{task['title']}\n"
            f"{task['description']}",
            reply_markup=task_done_keyboard(task["id"])
        )


# ─── АНАЛИТИКА ─────────────────────────────────────────────

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("За сегодня", callback_data="stats_day"),
         InlineKeyboardButton("За неделю", callback_data="stats_week")],
        [InlineKeyboardButton("За месяц", callback_data="stats_month"),
         InlineKeyboardButton("За всё время", callback_data="stats_all")],
    ])
    await update.message.reply_text("Выбери период:", reply_markup=keyboard)


async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id, context):
        return

    period = query.data.split("_")[1]
    now = datetime.now()

    if period == "day":
        since = now.replace(hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
        label = "сегодня"
    elif period == "week":
        since = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        label = "за неделю"
    elif period == "month":
        since = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        label = "за месяц"
    else:
        since = "2000-01-01 00:00:00"
        label = "за всё время"

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Все выполненные заказы за период
        async with db.execute(
            "SELECT * FROM orders WHERE status='done' AND created_at >= ?", (since,)
        ) as cursor:
            done_orders = [dict(r) for r in await cursor.fetchall()]

        # Все заказы за период
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM orders WHERE created_at >= ?", (since,)
        ) as cursor:
            total_orders = (await cursor.fetchone())["cnt"]

        # Отменённые
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM orders WHERE status='cancelled' AND created_at >= ?", (since,)
        ) as cursor:
            cancelled = (await cursor.fetchone())["cnt"]

        # Уникальные клиенты
        async with db.execute(
            "SELECT COUNT(DISTINCT telegram_id) as cnt FROM orders WHERE created_at >= ?", (since,)
        ) as cursor:
            clients = (await cursor.fetchone())["cnt"]

    # Считаем выручку из описаний выполненных заказов
    revenue = 0
    set_counts = {}
    for order in done_orders:
        desc = order.get("description", "")
        for line in desc.split("\n"):
            if "Итого:" in line:
                try:
                    revenue += int(line.replace("Итого:", "").replace("р", "").strip())
                except Exception:
                    pass
            if line.startswith("- "):
                parts = line.split(" x")[0].replace("- ", "")
                name = parts.split(" (")[0].strip()
                if name:
                    set_counts[name] = set_counts.get(name, 0) + 1

    avg_check = round(revenue / len(done_orders)) if done_orders else 0

    popular = ""
    if set_counts:
        sorted_sets = sorted(set_counts.items(), key=lambda x: x[1], reverse=True)
        popular = "\n".join(f"  {name}: {cnt} шт." for name, cnt in sorted_sets[:3])

    text = (
        f"Аналитика {label}:\n\n"
        f"Всего заказов: {total_orders}\n"
        f"Выполнено: {len(done_orders)}\n"
        f"Отменено: {cancelled}\n"
        f"Клиентов: {clients}\n\n"
        f"Выручка: {revenue}р\n"
        f"Средний чек: {avg_check}р\n"
    )
    if popular:
        text += f"\nПопулярные сеты:\n{popular}"

    await query.edit_message_text(text)


# ─── СОЗДАНИЕ ЗАДАЧИ ───────────────────────────────────────

async def create_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return ConversationHandler.END
    await update.message.reply_text("Введите название задачи:")
    return TASK_TITLE


async def task_get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_title"] = update.message.text
    await update.message.reply_text("Введите описание:")
    return TASK_DESC


async def task_get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_desc"] = update.message.text
    await update.message.reply_text("Приоритет: высокий, обычный или низкий?")
    return TASK_PRIORITY


async def task_get_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    priority_map = {"высокий": "high", "обычный": "normal", "низкий": "low"}
    priority = priority_map.get(update.message.text.lower(), "normal")
    task_id = await create_task(
        title=context.user_data["task_title"],
        description=context.user_data["task_desc"],
        created_by=update.effective_user.id,
        priority=priority
    )
    await update.message.reply_text(f"Задача #{task_id} создана!", reply_markup=admin_menu_keyboard())
    return ConversationHandler.END


# ─── CALLBACKS ─────────────────────────────────────────────

async def order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id, context):
        return
    parts = query.data.split("_")
    action = parts[1]
    order_id = int(parts[2])
    status_map = {"accept": "accepted", "delivery": "delivery", "done": "done", "cancel": "cancelled"}
    status_labels = {"accepted": "Принят", "delivery": "В доставке", "done": "Выполнен", "cancelled": "Отменён"}
    new_status = status_map.get(action, "new")
    await update_order_status(order_id, new_status)
    label = status_labels.get(new_status, new_status)
    await query.edit_message_text(query.message.text + f"\n\nСтатус: {label}")

    if new_status == "cancelled":
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT telegram_id FROM orders WHERE id = ?", (order_id,)) as cursor:
                    row = await cursor.fetchone()
            if row:
                await context.bot.send_message(
                    chat_id=row["telegram_id"],
                    text=f"Ваш заказ #{order_id} отменён администратором. Свяжитесь с нами для уточнения."
                )
        except Exception:
            pass


async def booking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id, context):
        return
    parts = query.data.split("_")
    action = parts[1]
    booking_id = int(parts[2])
    if action == "confirm":
        await update_booking_status(booking_id, "confirmed")
        await query.edit_message_text(query.message.text + "\n\nПодтверждено!")
    elif action == "reject":
        await update_booking_status(booking_id, "rejected")
        await query.edit_message_text(query.message.text + "\n\nОтклонено.")


async def task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id, context):
        return
    task_id = int(query.data.split("_")[2])
    await close_task(task_id)
    await query.edit_message_text(query.message.text + "\n\nВыполнено!")


async def get_photo_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await update.message.reply_text(f"file_id для menu_data.py:\n\n{file_id}")
    else:
        await update.message.reply_text("Отправь фото боту — получишь file_id")
