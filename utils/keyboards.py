from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from menu_data import get_categories, get_items_by_category


def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("🛍 Каталог"), KeyboardButton("🛒 Корзина")],
        [KeyboardButton("📅 Бронирование"), KeyboardButton("🔍 Мои заказы")],
        [KeyboardButton("❓ FAQ"), KeyboardButton("📞 Контакты")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def admin_menu_keyboard():
    keyboard = [
        [KeyboardButton("📋 Заказы"), KeyboardButton("📅 Брони")],
        [KeyboardButton("✅ Задачи"), KeyboardButton("📊 Статистика")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def categories_keyboard():
    """Клавиатура категорий меню"""
    categories = get_categories()
    keyboard = []
    row = []
    for i, cat in enumerate(categories):
        row.append(InlineKeyboardButton(cat, callback_data=f"cat_{i}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🛒 Корзина", callback_data="show_cart")])
    return InlineKeyboardMarkup(keyboard)


def items_keyboard(category_index: int):
    """Клавиатура блюд в категории"""
    categories = get_categories()
    category = categories[category_index]
    items = get_items_by_category(category)
    keyboard = []
    for item in items:
        keyboard.append([
            InlineKeyboardButton(
                f"{item['name']} — {item['price']}₽",
                callback_data=f"item_{item['id']}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_cats"),
        InlineKeyboardButton("🛒 Корзина", callback_data="show_cart"),
    ])
    return InlineKeyboardMarkup(keyboard)


def item_detail_keyboard(item_id: str, category_index: int):
    """Кнопки на карточке блюда"""
    keyboard = [
        [InlineKeyboardButton("➕ Добавить в корзину", callback_data=f"add_{item_id}")],
        [
            InlineKeyboardButton("◀️ Назад", callback_data=f"cat_{category_index}"),
            InlineKeyboardButton("🛒 Корзина", callback_data="show_cart"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def cart_keyboard():
    """Кнопки корзины"""
    keyboard = [
        [InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout")],
        [
            InlineKeyboardButton("🗑 Очистить", callback_data="clear_cart"),
            InlineKeyboardButton("🛍 В меню", callback_data="back_to_cats"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def confirm_order_keyboard():
    """Подтверждение заказа клиентом"""
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
