from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard():
    """Главное меню для клиентов"""
    keyboard = [
        [KeyboardButton("📦 Заказать"), KeyboardButton("📅 Бронирование")],
        [KeyboardButton("🔍 Мои заказы"), KeyboardButton("❓ FAQ")],
        [KeyboardButton("📞 Контакты"), KeyboardButton("💬 Написать нам")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def admin_menu_keyboard():
    """Меню для администраторов"""
    keyboard = [
        [KeyboardButton("📋 Заказы"), KeyboardButton("📅 Брони")],
        [KeyboardButton("✅ Задачи"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("👥 Клиенты"), KeyboardButton("⚙️ Настройки")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def order_status_keyboard(order_id: int):
    """Кнопки изменения статуса заказа"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Принять", callback_data=f"order_accept_{order_id}"),
            InlineKeyboardButton("🚀 В доставке", callback_data=f"order_delivery_{order_id}"),
        ],
        [
            InlineKeyboardButton("✔️ Выполнен", callback_data=f"order_done_{order_id}"),
            InlineKeyboardButton("❌ Отменить", callback_data=f"order_cancel_{order_id}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def booking_action_keyboard(booking_id: int):
    """Кнопки подтверждения бронирования"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"booking_confirm_{booking_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"booking_reject_{booking_id}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def task_done_keyboard(task_id: int):
    """Кнопка выполнения задачи"""
    keyboard = [
        [InlineKeyboardButton("✅ Выполнено", callback_data=f"task_done_{task_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def cancel_keyboard():
    """Кнопка отмены действия"""
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
    return InlineKeyboardMarkup(keyboard)


def persons_keyboard():
    """Выбор количества человек для брони"""
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data="persons_1"),
            InlineKeyboardButton("2", callback_data="persons_2"),
            InlineKeyboardButton("3", callback_data="persons_3"),
            InlineKeyboardButton("4", callback_data="persons_4"),
        ],
        [
            InlineKeyboardButton("5", callback_data="persons_5"),
            InlineKeyboardButton("6", callback_data="persons_6"),
            InlineKeyboardButton("7+", callback_data="persons_7"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
