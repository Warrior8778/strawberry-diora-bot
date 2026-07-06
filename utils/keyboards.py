from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from menu_data import SETS, TOPPINGS, EXTRAS
from datetime import datetime, timedelta


def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("🛍 Каталог"), KeyboardButton("🛒 Корзина")],
        [KeyboardButton("📅 Бронирование"), KeyboardButton("🔍 Мои заказы")],
        [KeyboardButton("💬 Поддержка"), KeyboardButton("❓ FAQ")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def admin_menu_keyboard():
    keyboard = [
        [KeyboardButton("📋 Orders"), KeyboardButton("📅 Bookings")],
        [KeyboardButton("✅ Tasks"), KeyboardButton("📊 Statistics")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def sets_keyboard():
    keyboard = []
    for s in SETS:
        keyboard.append([
            InlineKeyboardButton(
                f"{s['name']} — {s['price']} Rp",
                callback_data=f"set_{s['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🛒 Корзина", callback_data="show_cart")])
    return InlineKeyboardMarkup(keyboard)


def toppings_keyboard(set_id: str, selected: list):
    keyboard = []
    for t in TOPPINGS:
        check = "✅" if t["id"] in selected else "◻️"
        keyboard.append([
            InlineKeyboardButton(
                f"{check} {t['name']} (бесплатно)",
                callback_data=f"toggle_{set_id}_{t['id']}"
            )
        ])
    for e in EXTRAS:
        check = "✅" if e["id"] in selected else "◻️"
        keyboard.append([
            InlineKeyboardButton(
                f"{check} {e['name']} +{e['price']} Rp",
                callback_data=f"toggle_{set_id}_{e['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("➕ Добавить в корзину", callback_data=f"addset_{set_id}")])
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


def date_keyboard():
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    keyboard = [
        [
            InlineKeyboardButton(f"Сегодня ({today.strftime('%d.%m')})", callback_data=f"date_{today.strftime('%d.%m.%Y')}"),
            InlineKeyboardButton(f"Завтра ({tomorrow.strftime('%d.%m')})", callback_data=f"date_{tomorrow.strftime('%d.%m.%Y')}"),
        ],
        [
            InlineKeyboardButton(day_after.strftime('%d.%m.%Y'), callback_data=f"date_{day_after.strftime('%d.%m.%Y')}"),
            InlineKeyboardButton("Другая дата", callback_data="date_custom"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def time_keyboard():
    slots = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00",
             "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"]
    keyboard = []
    row = []
    for i, slot in enumerate(slots):
        row.append(InlineKeyboardButton(slot, callback_data=f"time_{slot}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def order_status_keyboard(order_id: int):
    keyboard = [
        [
            InlineKeyboardButton("✅ Accept", callback_data=f"order_accept_{order_id}"),
            InlineKeyboardButton("🚀 Delivering", callback_data=f"order_delivery_{order_id}"),
        ],
        [
            InlineKeyboardButton("✔️ Done", callback_data=f"order_done_{order_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"order_cancel_{order_id}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def booking_action_keyboard(booking_id: int):
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"booking_confirm_{booking_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"booking_reject_{booking_id}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def task_done_keyboard(task_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Done", callback_data=f"task_done_{task_id}")]
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
