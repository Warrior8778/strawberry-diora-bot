from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from menu_data import SETS, TOPPINGS, EXTRAS


def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("🛍 Каталог"), KeyboardButton("🛒 Корзина")],
        [KeyboardButton("📅 Бронирование"), KeyboardButton("🔍 Мои заказы")],
        [KeyboardButton("💬 Поддержка"), KeyboardButton("❓ FAQ")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def admin_menu_keyboard():
    keyboard = [
        [KeyboardButton("📋 Заказы"), KeyboardButton("📅 Брони")],
        [KeyboardButton("✅ Задачи"), KeyboardButton("📊 Статистика")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def sets_keyboard():
    """Галерея сетов"""
    keyboard = []
    for s in SETS:
        keyboard.append([
            InlineKeyboardButton(
                f"{s['name']} — {s['price']}₽",
                callback_data=f"set_{s['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🛒 Корзина", callback_data="show_cart")])
    return InlineKeyboardMarkup(keyboard)


def toppings_keyboard(set_id: str, selected: list):
    """Выбор посыпок и добавок (мультивыбор)"""
    keyboard = []

    # Бесплатные посыпки
    for t in TOPPINGS:
        check = "✅" if t["id"] in selected else "◻️"
        keyboard.append([
            InlineKeyboardButton(
                f"{check} {t['name']} (бесплатно)",
                callback_data=f"toggle_{set_id}_{t['id']}"
            )
        ])

    # Платные добавки
    for e in EXTRAS:
        check = "✅" if e["id"] in selected else "◻️"
        keyboard.append([
            InlineKeyboardButton(
                f"{check} {e['name']} +{e['price']}₽",
                callback_data=f"toggle_{set_id}_{e['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("➕ Добавить в корзину", callback_data=f"addset_{set_id}"),
    ])
    keyboard.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_sets"),
        InlineKeyboardButton("🛒 Корзина", callback_data="show_cart"),
    ])
    return InlineKeyboardMarkup(keyboard)


def cart_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout")],
        [
            InlineKeyboardButton("🗑 Очистить", callback_data="clear_cart"),
            InlineKeyboardButton("🛍 В меню", callback_data="back_to_sets"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def confirm_order_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_order"),
            InlineKeyboardButton("❌ Отмена", callback_data="show_cart"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def order_status_keyboard(order_id: int):
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
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"booking_confirm_{booking_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"booking_reject_{booking_id}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def task_done_keyboard(task_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Выполнено", callback_data=f"task_done_{task_id}")]
    ])


def cancel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ])


def persons_keyboard():
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
