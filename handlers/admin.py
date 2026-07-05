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

TASK_TITLE, TASK_DESC, TASK_PRIORITY = range(20, 23)


def is_admin(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    admin_ids = context.bot_data.get("admin_ids", [])
    return user_id in admin_ids


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        await update.message.reply_text("Нет доступа.")
        return
    await update.message.reply_text(
        "Панель администратора Strawberry Diora\n\nВыберите раздел:",
        reply_markup=admin_menu_keyboard()
    )


async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return
    orders = await get_all_orders(status="new")
    if not orders:
        await update.message.reply_text("Новых заказов нет!")
        return
    await update.message.reply_text(f"Новые заказы ({len(orders)}):")
    for order in orders[:10]:
        await update.message.reply_text(
            f"Заказ #{order['id']}\n"
            f"{order['description']}\n"
            f"Адрес: {order['address']}\n"
            f"Время: {order['created_at'][:16]}",
            reply_markup=order_status_keyboard(order["id"])
        )


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
            f"{task['description']}\n"
            f"Время: {task['created_at'][:16]}",
            reply_markup=task_done_keyboard(task["id"])
        )


async def create_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return ConversationHandler.END
    await update.message.reply_text("Введите название задачи:")
    return TASK_TITLE


async def task_get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_title"] = update.message.text
    await update.message.reply_text("Введите описание задачи:")
    return TASK_DESC


async def task_get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_desc"] = update.message.text
    await update.message.reply_text("Приоритет: высокий, обычный или низкий?")
    return TASK_PRIORITY


async def task_get_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    priority_map = {
        "высокий": "high", "обычный": "normal", "низкий": "low"
    }
    priority = priority_map.get(update.message.text.lower(), "normal")
    task_id = await create_task(
        title=context.user_data["task_title"],
        description=context.user_data["task_desc"],
        created_by=update.effective_user.id,
        priority=priority
    )
    await update.message.reply_text(
        f"Задача #{task_id} создана!",
        reply_markup=admin_menu_keyboard()
    )
    return ConversationHandler.END


async def order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id, context):
        await query.answer("Нет доступа", show_alert=True)
        return
    parts = query.data.split("_")
    action = parts[1]
    order_id = int(parts[2])
    status_map = {
        "accept": "accepted",
        "delivery": "delivery",
        "done": "done",
        "cancel": "cancelled"
    }
    status_labels = {
        "accepted": "Принят",
        "delivery": "В доставке",
        "done": "Выполнен",
        "cancelled": "Отменён"
    }
    new_status = status_map.get(action, "new")
    await update_order_status(order_id, new_status)
    label = status_labels.get(new_status, new_status)
    await query.edit_message_text(
        query.message.text + f"\n\nСтатус: {label}"
    )

    # Уведомляем клиента если отменён
    if new_status == "cancelled":
        try:
            import aiosqlite
            async with aiosqlite.connect("strawberry_diora.db") as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT telegram_id FROM orders WHERE id = ?", (order_id,)
                ) as cursor:
                    row = await cursor.fetchone()
            if row:
                await context.bot.send_message(
                    chat_id=row["telegram_id"],
                    text=f"Ваш заказ #{order_id} был отменён администратором. Свяжитесь с нами для уточнения."
                )
        except Exception:
            pass


async def booking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id, context):
        await query.answer("Нет доступа", show_alert=True)
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
        await query.answer("Нет доступа", show_alert=True)
        return
    task_id = int(query.data.split("_")[2])
    await close_task(task_id)
    await query.edit_message_text(query.message.text + "\n\nВыполнено!")


async def get_photo_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await update.message.reply_text(
            f"file_id для menu_data.py:\n\n{file_id}"
        )
    else:
        await update.message.reply_text(
            "Отправь фото с подписью /addphoto"
        )
