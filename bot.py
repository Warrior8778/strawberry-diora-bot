import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters
)

from database.db import init_db
from handlers.client import (
    start, faq_handler, contacts_handler, my_orders_handler,
    ai_chat_handler, reset_chat, cancel_handler,
    order_start, order_get_description, order_get_address,
    booking_start, booking_get_name, booking_get_phone,
    booking_get_date, booking_get_time, booking_get_persons, booking_get_comment,
    ORDER_DESCRIPTION, ORDER_ADDRESS,
    BOOKING_NAME, BOOKING_PHONE, BOOKING_DATE, BOOKING_TIME, BOOKING_PERSONS, BOOKING_COMMENT
)
from handlers.admin import (
    admin_panel, admin_orders, admin_bookings, admin_tasks,
    create_task_start, task_get_title, task_get_desc, task_get_priority,
    order_callback, booking_callback, task_callback,
    TASK_TITLE, TASK_DESC, TASK_PRIORITY
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS_RAW.split(",") if x.strip()]


async def post_init(application: Application):
    """Инициализация после запуска"""
    application.bot_data["admin_ids"] = ADMIN_IDS
    await init_db()
    print(f"🍓 Strawberry_Diora Bot запущен!")
    print(f"👑 Администраторы: {ADMIN_IDS}")


def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()

    # ── Обработчик заказа ──────────────────────────────────
    order_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📦 Заказать$"), order_start)],
        states={
            ORDER_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_get_description)],
            ORDER_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_get_address)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_handler, pattern="^cancel$"),
            CommandHandler("cancel", cancel_handler),
        ]
    )

    # ── Обработчик бронирования ────────────────────────────
    booking_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📅 Бронирование$"), booking_start)],
        states={
            BOOKING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, booking_get_name)],
            BOOKING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, booking_get_phone)],
            BOOKING_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, booking_get_date)],
            BOOKING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, booking_get_time)],
            BOOKING_PERSONS: [CallbackQueryHandler(booking_get_persons, pattern="^persons_")],
            BOOKING_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, booking_get_comment)],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_handler, pattern="^cancel$"),
            CommandHandler("cancel", cancel_handler),
        ]
    )

    # ── Создание задачи ────────────────────────────────────
    task_conv = ConversationHandler(
        entry_points=[CommandHandler("newtask", create_task_start)],
        states={
            TASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_get_title)],
            TASK_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_get_desc)],
            TASK_PRIORITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_get_priority)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)]
    )

    # ── Регистрация обработчиков ───────────────────────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("reset", reset_chat))

    app.add_handler(order_conv)
    app.add_handler(booking_conv)
    app.add_handler(task_conv)

    # Кнопки меню клиента
    app.add_handler(MessageHandler(filters.Regex("^❓ FAQ$"), faq_handler))
    app.add_handler(MessageHandler(filters.Regex("^📞 Контакты$"), contacts_handler))
    app.add_handler(MessageHandler(filters.Regex("^🔍 Мои заказы$"), my_orders_handler))

    # Кнопки меню администратора
    app.add_handler(MessageHandler(filters.Regex("^📋 Заказы$"), admin_orders))
    app.add_handler(MessageHandler(filters.Regex("^📅 Брони$"), admin_bookings))
    app.add_handler(MessageHandler(filters.Regex("^✅ Задачи$"), admin_tasks))

    # Callback кнопки
    app.add_handler(CallbackQueryHandler(order_callback, pattern="^order_"))
    app.add_handler(CallbackQueryHandler(booking_callback, pattern="^booking_"))
    app.add_handler(CallbackQueryHandler(task_callback, pattern="^task_done_"))

    # AI чат (все остальные сообщения)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, ai_chat_handler
    ))

    print("🚀 Запуск бота...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
