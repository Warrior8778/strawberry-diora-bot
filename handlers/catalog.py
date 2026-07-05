from telegram import Update
from telegram.ext import ContextTypes
from menu_data import get_categories, get_items_by_category, get_item_by_id
from utils.keyboards import (
    categories_keyboard, items_keyboard, item_detail_keyboard,
    cart_keyboard, confirm_order_keyboard, main_menu_keyboard
)
from database.db import create_order


async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛍 Наше меню — выбери категорию:",
        reply_markup=categories_keyboard()
    )


async def catalog_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("cat_"):
        cat_index = int(data.split("_")[1])
        categories = get_categories()
        category = categories[cat_index]
        await query.edit_message_text(
            f"{category}\n\nВыбери блюдо:",
            reply_markup=items_keyboard(cat_index)
        )

    elif data == "back_to_cats":
        await query.edit_message_text(
            "🛍 Наше меню — выбери категорию:",
            reply_markup=categories_keyboard()
        )

    elif data.startswith("item_"):
        item_id = data[5:]
        item, category = get_item_by_id(item_id)
        if not item:
            await query.answer("Блюдо не найдено", show_alert=True)
            return
        categories = get_categories()
        cat_index = categories.index(category)
        text = f"{item['name']}\n{item['desc']}\n\n💰 {item['price']}₽"
        await query.edit_message_text(
            text,
            reply_markup=item_detail_keyboard(item_id, cat_index)
        )

    elif data.startswith("add_"):
        item_id = data[4:]
        item, _ = get_item_by_id(item_id)
        if not item:
            return
        cart = context.user_data.setdefault("cart", {})
        if item_id in cart:
            cart[item_id]["qty"] += 1
        else:
            cart[item_id] = {"name": item["name"], "price": item["price"], "qty": 1}
        total = sum(v["price"] * v["qty"] for v in cart.values())
        count = sum(v["qty"] for v in cart.values())
        await query.answer(f"✅ Добавлено! В корзине: {count} поз. / {total}₽", show_alert=False)


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = context.user_data.get("cart", {})
    text, keyboard = _build_cart_message(cart)
    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard)
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=keyboard)


async def cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "show_cart":
        cart = context.user_data.get("cart", {})
        text, keyboard = _build_cart_message(cart)
        await query.edit_message_text(text, reply_markup=keyboard)

    elif data == "clear_cart":
        context.user_data["cart"] = {}
        await query.edit_message_text(
            "🗑 Корзина очищена. Выбери категорию:",
            reply_markup=categories_keyboard()
        )

    elif data == "checkout":
        cart = context.user_data.get("cart", {})
        if not cart:
            await query.answer("Корзина пуста!", show_alert=True)
            return
        total = sum(v["price"] * v["qty"] for v in cart.values())
        lines = "\n".join(
            f"- {v['name']} x{v['qty']} = {v['price'] * v['qty']}р"
            for v in cart.values()
        )
        await query.edit_message_text(
            f"Подтверди заказ:\n\n{lines}\n\nИтого: {total}р\n\nПодтверждаешь?",
            reply_markup=confirm_order_keyboard()
        )

    elif data == "confirm_order":
        await _finalize_order(query, context)


def _build_cart_message(cart: dict):
    if not cart:
        return "🛒 Корзина пуста\n\nДобавь блюда из меню!", categories_keyboard()
    total = sum(v["price"] * v["qty"] for v in cart.values())
    lines = "\n".join(
        f"- {v['name']} x{v['qty']} = {v['price'] * v['qty']}р"
        for v in cart.values()
    )
    return f"🛒 Твоя корзина:\n\n{lines}\n\nИтого: {total}р", cart_keyboard()


async def _finalize_order(query, context: ContextTypes.DEFAULT_TYPE):
    cart = context.user_data.get("cart", {})
    total = sum(v["price"] * v["qty"] for v in cart.values())
    lines = "\n".join(
        f"- {v['name']} x{v['qty']} = {v['price'] * v['qty']}р"
        for v in cart.values()
    )
    description = lines + f"\n\nИтого: {total}р"
    context.user_data["pending_order_desc"] = description
    context.user_data["pending_order_total"] = total
    await query.edit_message_text(
        "Введи адрес доставки:\n\nНапример: ул. Ленина, д.5, кв.12"
    )
    context.user_data["awaiting_address"] = True


async def handle_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_address"):
        return False
    user = update.effective_user
    address = update.message.text
    description = context.user_data.get("pending_order_desc", "")
    total = context.user_data.get("pending_order_total", 0)
    order_id = await create_order(user.id, description, address)
    await update.message.reply_text(
        f"Заказ #{order_id} оформлен!\n\n{description}\n\nДоставка: {address}\n\nОжидайте звонка!",
        reply_markup=main_menu_keyboard()
    )
    admin_ids = context.bot_data.get("admin_ids", [])
    from utils.keyboards import order_status_keyboard
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"Новый заказ #{order_id}\n\n"
                    f"Клиент: {user.full_name} (@{user.username or '-'})\n\n"
                    f"{description}\n\n"
                    f"Адрес: {address}"
                ),
                reply_markup=order_status_keyboard(order_id)
            )
        except Exception:
            pass
    context.user_data["cart"] = {}
    context.user_data["awaiting_address"] = False
    return True
