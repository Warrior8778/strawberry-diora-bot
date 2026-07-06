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
        await update.message.reply_text("Access denied.")
        return
    await update.message.reply_text(
        "Admin Panel — Strawberry Diora 🍓\n\nChoose a section:",
        reply_markup=admin_menu_keyboard()
    )


async def admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 New", callback_data="orders_new"),
         InlineKeyboardButton("✅ Accepted", callback_data="orders_accepted")],
        [InlineKeyboardButton("🚀 Delivering", callback_data="orders_delivery"),
         InlineKeyboardButton("📋 History", callback_data="orders_history")],
    ])
    await update.message.reply_text("Choose orders section:", reply_markup=keyboard)


async def orders_section_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id, context):
        return

    section = query.data.split("_")[1]
    status_map = {
        "new": ("new", "🆕 New Orders"),
        "accepted": ("accepted", "✅ Accepted Orders"),
        "delivery": ("delivery", "🚀 Delivering"),
        "history": (None, "📋 Order History"),
    }
    status, title = status_map.get(section, (None, "Orders"))

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
        await query.edit_message_text(f"{title}\n\nNo orders found.")
        return

    await query.edit_message_text(f"{title} ({len(orders)}):")
    status_labels = {
        "new": "New", "accepted": "Accepted",
        "delivery": "Delivering", "done": "Done", "cancelled": "Cancelled"
    }

    for order in orders:
        status_label = status_labels.get(order["status"], order["status"])
        text = (
            f"Order #{order['id']} — {status_label}\n"
            f"{order['description']}\n"
            f"Address: {order['address']}\n"
            f"Time: {order['created_at'][:16]}"
        )
        if order["status"] in ("new", "accepted", "delivery"):
            await query.message.reply_text(text, reply_markup=order_status_keyboard(order["id"]))
        else:
            await query.message.reply_text(text)


async def admin_bookings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return
    bookings = await get_pending_bookings()
    if not bookings:
        await update.message.reply_text("No pending bookings!")
        return
    await update.message.reply_text(f"Pending bookings ({len(bookings)}):")
    for b in bookings:
        await update.message.reply_text(
            f"Booking #{b['id']}\n"
            f"Name: {b['name']}\n"
            f"Phone: {b['phone']}\n"
            f"Date: {b['date']} at {b['time']}\n"
            f"Guests: {b['persons']}\n"
            f"Comment: {b['comment'] or 'none'}",
            reply_markup=booking_action_keyboard(b["id"])
        )


async def admin_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return
    tasks = await get_open_tasks()
    if not tasks:
        await update.message.reply_text("No open tasks!")
        return
    await update.message.reply_text(f"Open tasks ({len(tasks)}):")
    for task in tasks:
        await update.message.reply_text(
            f"Task #{task['id']}\n"
            f"{task['title']}\n"
            f"{task['description']}",
            reply_markup=task_done_keyboard(task["id"])
        )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Today", callback_data="stats_day"),
         InlineKeyboardButton("This week", callback_data="stats_week")],
        [InlineKeyboardButton("This month", callback_data="stats_month"),
         InlineKeyboardButton("All time", callback_data="stats_all")],
    ])
    await update.message.reply_text("Choose period:", reply_markup=keyboard)


async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id, context):
        return

    period = query.data.split("_")[1]
    now = datetime.now()

    if period == "day":
        since = now.replace(hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
        label = "today"
    elif period == "week":
        since = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        label = "this week"
    elif period == "month":
        since = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        label = "this month"
    else:
        since = "2000-01-01 00:00:00"
        label = "all time"

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE status='done' AND created_at >= ?", (since,)
        ) as cursor:
            done_orders = [dict(r) for r in await cursor.fetchall()]
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM orders WHERE created_at >= ?", (since,)
        ) as cursor:
            total_orders = (await cursor.fetchone())["cnt"]
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM orders WHERE status='cancelled' AND created_at >= ?", (since,)
        ) as cursor:
            cancelled = (await cursor.fetchone())["cnt"]
        async with db.execute(
            "SELECT COUNT(DISTINCT telegram_id) as cnt FROM orders WHERE created_at >= ?", (since,)
        ) as cursor:
            clients = (await cursor.fetchone())["cnt"]

    revenue = 0
    set_counts = {}
    for order in done_orders:
        desc = order.get("description", "")
        for line in desc.split("\n"):
            if "Total:" in line:
                try:
                    revenue += int(line.replace("Total:", "").replace("Rp", "").strip())
                except Exception:
                    pass
            if line.startswith("- "):
                name = line.split(" (")[0].replace("- ", "").strip()
                if name:
                    set_counts[name] = set_counts.get(name, 0) + 1

    avg_check = round(revenue / len(done_orders)) if done_orders else 0
    popular = ""
    if set_counts:
        sorted_sets = sorted(set_counts.items(), key=lambda x: x[1], reverse=True)
        popular = "\n".join(f"  {name}: {cnt} pcs" for name, cnt in sorted_sets[:3])

    text = (
        f"Statistics — {label}:\n\n"
        f"Total orders: {total_orders}\n"
        f"Completed: {len(done_orders)}\n"
        f"Cancelled: {cancelled}\n"
        f"Clients: {clients}\n\n"
        f"Revenue: {revenue} Rp\n"
        f"Avg order: {avg_check} Rp\n"
    )
    if popular:
        text += f"\nTop sets:\n{popular}"

    await query.edit_message_text(text)


async def create_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return ConversationHandler.END
    await update.message.reply_text("Enter task title:")
    return TASK_TITLE


async def task_get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_title"] = update.message.text
    await update.message.reply_text("Enter task description:")
    return TASK_DESC


async def task_get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["task_desc"] = update.message.text
    await update.message.reply_text("Priority: high, normal or low?")
    return TASK_PRIORITY


async def task_get_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    priority_map = {"high": "high", "normal": "normal", "low": "low"}
    priority = priority_map.get(update.message.text.lower(), "normal")
    task_id = await create_task(
        title=context.user_data["task_title"],
        description=context.user_data["task_desc"],
        created_by=update.effective_user.id,
        priority=priority
    )
    await update.message.reply_text(f"Task #{task_id} created!", reply_markup=admin_menu_keyboard())
    return ConversationHandler.END


async def order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id, context):
        return
    parts = query.data.split("_")
    action = parts[1]
    order_id = int(parts[2])
    status_map = {"accept": "accepted", "delivery": "delivery", "done": "done", "cancel": "cancelled"}
    status_labels = {"accepted": "Accepted", "delivery": "Delivering", "done": "Done", "cancelled": "Cancelled"}
    new_status = status_map.get(action, "new")
    await update_order_status(order_id, new_status)
    label = status_labels.get(new_status, new_status)
    await query.edit_message_text(query.message.text + f"\n\nStatus updated: {label}")

    if new_status == "cancelled":
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT telegram_id FROM orders WHERE id = ?", (order_id,)) as cursor:
                    row = await cursor.fetchone()
            if row:
                await context.bot.send_message(
                    chat_id=row["telegram_id"],
                    text=f"Your order #{order_id} was cancelled by admin. Please contact us for details."
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
        await query.edit_message_text(query.message.text + "\n\nConfirmed!")
    elif action == "reject":
        await update_booking_status(booking_id, "rejected")
        await query.edit_message_text(query.message.text + "\n\nRejected.")


async def task_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id, context):
        return
    task_id = int(query.data.split("_")[2])
    await close_task(task_id)
    await query.edit_message_text(query.message.text + "\n\nDone!")


async def get_photo_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id, context):
        return
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await update.message.reply_text(f"file_id for menu_data.py:\n\n{file_id}")
    else:
        await update.message.reply_text("Send a photo to get its file_id")
