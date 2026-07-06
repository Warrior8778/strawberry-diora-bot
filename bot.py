import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters
)

from database.db import init_db
from handlers.client import (
    start, faq_handler, contacts_handler, my_orders_handler,
    support_handler, ai_chat_handler, reset_chat, cancel_handler,
    client_cancel_callback,
    booking_start, booking_get_name, booking_get_phone,
    booking_get_date, booking_get_time, booking_get_persons, booking_get_comment,
    BOOKING_NAME, BOOKING_PHONE, BOOKING_DATE, BOOKING_TIME, BOOKING_PERSONS, BOOKING_COMMENT
)
from handlers.catalog import show_catalog, show_cart, catalog_callback, cart_callback, date_time_callback
from handlers.admin import (
    admin_panel, admin_orders, admin_bookings, admin_tasks, admin_stats,
    orders_section_callback, stats_callback,
    create_task_start, task_get_title, task_get_desc, task_get_priority,
    order_callback, booking_callback, task_callback, get_photo_id,
    TASK_TITLE, TASK_DESC, TASK_PRIORITY
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]


async def post_init(application: Application):
    application.bot_data["admin_ids"] = ADMIN_IDS
    await init_db()
    print(f"🍓 Strawberry_Diora Bot started! Admins: {ADMIN_IDS}")


def main():
    app = Application.builder().token(TOKEN).post_init(post_init).build()

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

    task_conv = ConversationHandler(
        entry_points=[CommandHandler("newtask", create_task_start)],
        states={
            TASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_get_title)],
            TASK_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_get_desc)],
            TASK_PRIORITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_get_priority)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("reset", reset_chat))
    app.add_handler(CommandHandler("addphoto", get_photo_id))

    app.add_handler(booking_conv)
    app.add_handler(task_conv)

    # Кнопки клиента (Russian)
    app.add_handler(MessageHandler(filters.Regex("^🛍 Каталог$"), show_catalog))
    app.add_handler(MessageHandler(filters.Regex("^🛒 Корзина$"), show_cart))
    app.add_handler(MessageHandler(filters.Regex("^❓ FAQ$"), faq_handler))
    app.add_handler(MessageHandler(filters.Regex("^📞 Контакты$"), contacts_handler))
    app.add_handler(MessageHandler(filters.Regex("^🔍 Мои заказы$"), my_orders_handler))
    app.add_handler(MessageHandler(filters.Regex("^💬 Поддержка$"), support_handler))

    # Кнопки админа (English)
    app.add_handler(MessageHandler(filters.Regex("^📋 Orders$"), admin_orders))
    app.add_handler(MessageHandler(filters.Regex("^📅 Bookings$"), admin_bookings))
    app.add_handler(MessageHandler(filters.Regex("^✅ Tasks$"), admin_tasks))
    app.add_handler(MessageHandler(filters.Regex("^📊 Statistics$"), admin_stats))

    # Фото от админа
    app.add_handler(MessageHandler(filters.PHOTO, get_photo_id))

    # Callbacks каталога
    app.add_handler(CallbackQueryHandler(catalog_callback, pattern="^set_"))
    app.add_handler(CallbackQueryHandler(catalog_callback, pattern="^back_to_sets$"))
    app.add_handler(CallbackQueryHandler(catalog_callback, pattern="^toggle_"))
    app.add_handler(CallbackQueryHandler(catalog_callback, pattern="^addset_"))

    # Callbacks корзины
    app.add_handler(CallbackQueryHandler(cart_callback, pattern="^show_cart$"))
    app.add_handler(CallbackQueryHandler(cart_callback, pattern="^clear_cart$"))
    app.add_handler(CallbackQueryHandler(cart_callback, pattern="^checkout$"))
    app.add_handler(CallbackQueryHandler(cart_callback, pattern="^confirm_order$"))

    # Callbacks даты и времени
    app.add_handler(CallbackQueryHandler(date_time_callback, pattern="^date_"))
    app.add_handler(CallbackQueryHandler(date_time_callback, pattern="^time_"))

    # Отмена заказа клиентом
    app.add_handler(CallbackQueryHandler(client_cancel_callback, pattern="^client_cancel_"))

    # Разделы заказов и статистика
    app.add_handler(CallbackQueryHandler(orders_section_callback, pattern="^orders_"))
    app.add_handler(CallbackQueryHandler(stats_callback, pattern="^stats_"))

    # Callbacks админа
    app.add_handler(CallbackQueryHandler(order_callback, pattern="^order_"))
    app.add_handler(CallbackQueryHandler(booking_callback, pattern="^booking_"))
    app.add_handler(CallbackQueryHandler(task_callback, pattern="^task_done_"))

    # AI чат
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_handler))

    print("🚀 Starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
