from telegram import Update
from telegram.ext import ContextTypes
from menu_data import get_categories, get_items_by_category, get_item_by_id
from utils.keyboards import (
    categories_keyboard, items_keyboard, item_detail_keyboard,
    cart_keyboard, confirm_order_keyboard, main_menu_keyboard
)
from database.db import create_order, get_or_create_client


# ─── КАТАЛОГ ───────────────────────────────────────────────

async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать категории"""
    await update.message.reply_text(
        "🛍 *Наше меню* — выбери категорию:",
        parse_mode="MarkdownV2",
        reply_markup=categories_keyboard()
    )


async def catalog_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Выбор категории
    if data.startswith("cat_"):
        cat_index = int(data.split("_")[1])
        categories = get_categories()
        category = categories[cat_index]
        items = get_items_by_category(category)

        text = f"*{category}*\n\nВыбери блюдо:"
        await query.edit_message_text(
            text,
            parse_mode="MarkdownV2",
            reply_markup=items_keyboard(cat_index)
        )

    # Назад к категориям
    elif data == "back_to_cats":
        await query.edit_message_text(
            "🛍 *Наше меню* — выбери категорию:",
            parse_mode="MarkdownV2",
            reply_markup=categories_keyboard()
        )

    # Карточка блюда
    elif data.startswith("item_"):
        item_id = data[5:]
        item, category = get_item_by_id(item_id)
        if not item:
            await query.answer("Блюдо не найдено", show_alert=True)
            return

        categories = get_categories()
        cat_index = categories.index(category)

        text = (
            f"*{item['name']}*\n"
            f"_{item['desc']}_\n\n"
            f"💰 *{item['price']}₽*"
        )

        if item.get("photo"):
            try:
                await query.message.reply_photo(
                    photo=item["photo"],
                    caption=text,
                    parse_mode="MarkdownV2",
                    reply_markup=item_detail_keyboard(item_id, cat_index)
                )
                await query.message.delete()
            except Exception:
                await query.edit_message_text(
                    text,
                    parse_mode="MarkdownV2",
                    reply_markup=item_detail_keyboard(item_id, cat_index)
                )
        else:
            await query.edit_message_text(
                text,
                parse_mode="MarkdownV2",
                reply_markup=item_detail_keyboard(item_id, cat_index)
            )

    # Добавить в корзину
    elif data.startswith("add_"):
        item_id = data[4:]
        item, _ = get_item_by_id(item_id)
        if not item:
            return

        cart = context.user_data.setdefault("cart", {})
        if item_id in cart:
            cart[item_id]["qty"] += 1
        else:
            cart[item_id] = {
                "name": item["name"],
                "price": item["price"],
                "qty": 1
            }

        total = sum(v["price"] * v["qty"] for v in cart.values())
        items_count = sum(v["qty"] for v in cart.values())

        await query.answer(
            f"✅ {item['name']} добавлен! Корзина: {items_count} поз. / {total}₽",
            show_alert=False
        )


# ─── КОРЗИНА ───────────────────────────────────────────────

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать корзину (из кнопки меню)"""
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
            "🗑 Корзина очищена.\n\nВыбери категорию:",
            reply_markup=categories_keyboard()
        )

    elif data == "checkout":
        cart = context.user_data.get("cart", {})
        if not cart:
            await query.answer("Корзина пуста!", show_alert=True)
            return

        total = sum(v["price"] * v["qty"] for v in cart.values())
        lines = "\n".join(
            f"• {v['name']} × {v['qty']} = {v['price'] * v['qty']}₽"
            for v in cart.values()
        )

        await query.edit_message_text(
            f"📋 *Подтверди заказ:*\n\n{lines}\n\n"
            f"💰 *Итого: {total}₽*\n\n"
            f"Подтверждаешь?",
            parse_mode="MarkdownV2",
            reply_markup=confirm_order_keyboard()
        )

    elif data == "confirm_order":
        await _finalize_order(query, context)


def _build_cart_message(cart: dict):
    if not cart:
        return (
            "🛒 *Корзина пуста*\n\nДобавь блюда из меню!",
            categories_keyboard()
        )

    total = sum(v["price"] * v["qty"] for v in cart.values())
    lines = "\n".join(
        f"• {v['name']} × {v['qty']} = {v['price'] * v['qty']}₽"
        for v in cart.values()
    )

    text = f"🛒 *Твоя корзина:*\n\n{lines}\n\n💰 *Итого: {total}₽*"
    return text, cart_keyboard()


async def _finalize_order(query, context: ContextTypes.DEFAULT_TYPE):
    """Создать заказ и уведомить админа"""
    user = query.from_user
    cart = context.user_data.get("cart", {})
    total = sum(v["price"] * v["qty"] for v in cart.values())

    lines = "\n".join(
        f"• {v['name']} × {v['qty']} = {v['price'] * v['qty']}₽"
        for v in cart.values()
    )
    description = lines + f"\n\nИтого: {total}₽"

    # Просим адрес
    context.user_data["pending_order_desc"] = description
    context.user_data["pending_order_total"] = total

    await query.edit_message_text(
        "📍 *Введи адрес доставки:*\n\n_Например: ул. Ленина, д.5, кв.12_",
        parse_mode="MarkdownV2"
    )
    context.user_data["awaiting_address"] = True


async def handle_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить адрес и создать заказ"""
    if not context.user_data.get("awaiting_address"):
        return False

    user = update.effective_user
    address = update.message.text
    description = context.user_data.get("pending_order_desc", "")
    total = context.user_data.get("pending_order_total", 0)

    order_id = await create_order(user.id, description, address)

    await update.message.reply_text(
        f"✅ *Заказ #{order_id} оформлен!*\n\n"
        f"{description}\n\n"
        f"📍 Доставка: {address}\n\n"
        f"Ожидайте звонка для подтверждения 🚀",
        parse_mode="MarkdownV2",
        reply_markup=main_menu_keyboard()
    )

    # Уведомляем администраторов
    admin_ids = context.bot_data.get("admin_ids", [])
    from utils.keyboards import order_status_keyboard
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"🆕 *Новый заказ #{order_id}*\n\n"
                    f"👤 {user.full_name} (@{user.username or '-'})\n"
                    f"📞 [написать клиенту](tg://user?id={user.id})\n\n"
                    f"{description}\n\n"
                    f"📍 {address}"
                ),
                parse_mode="MarkdownV2",
                reply_markup=order_status_keyboard(order_id)
            )
        except Exception:
            pass

    # Очищаем корзину
    context.user_data["cart"] = {}
    context.user_data["awaiting_address"] = False

    return True
