from telegram import Update
from telegram.ext import ContextTypes
from menu_data import SETS, get_set_by_id, get_topping_by_id, TOPPINGS, EXTRAS
from utils.keyboards import (
    sets_keyboard, toppings_keyboard,
    cart_keyboard, confirm_order_keyboard, main_menu_keyboard
)
from database.db import create_order


async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все сеты"""
    # Если есть фото у первого сета — показываем с фото, иначе текстом
    has_photos = any(s.get("photo") for s in SETS)

    if has_photos:
        for s in SETS:
            text = f"🍓 {s['name']}\n{s['desc']}\n\n💰 {s['price']}₽"
            if s.get("photo"):
                await update.message.reply_photo(
                    photo=s["photo"],
                    caption=text,
                    reply_markup=_set_select_keyboard(s["id"])
                )
            else:
                await update.message.reply_text(text, reply_markup=_set_select_keyboard(s["id"]))
    else:
        await update.message.reply_text(
            "🍓 Выбери сет клубники в шоколаде:",
            reply_markup=sets_keyboard()
        )


def _set_select_keyboard(set_id: str):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Выбрать", callback_data=f"set_{set_id}")]
    ])


async def catalog_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Выбор сета
    if data.startswith("set_"):
        set_id = data[4:]
        s = get_set_by_id(set_id)
        if not s:
            return

        # Сбрасываем выбор посыпок для этого сета
        context.user_data[f"toppings_{set_id}"] = []

        text = (
            f"🍓 {s['name']}\n"
            f"{s['desc']}\n\n"
            f"💰 {s['price']}₽\n\n"
            f"Выбери посыпки и добавки:"
        )
        selected = context.user_data.get(f"toppings_{set_id}", [])

        try:
            await query.edit_message_text(text, reply_markup=toppings_keyboard(set_id, selected))
        except Exception:
            await query.message.reply_text(text, reply_markup=toppings_keyboard(set_id, selected))

    # Назад к сетам
    elif data == "back_to_sets":
        try:
            await query.edit_message_text(
                "🍓 Выбери сет клубники в шоколаде:",
                reply_markup=sets_keyboard()
            )
        except Exception:
            await query.message.reply_text(
                "🍓 Выбери сет клубники в шоколаде:",
                reply_markup=sets_keyboard()
            )

    # Переключить посыпку
    elif data.startswith("toggle_"):
        parts = data.split("_", 2)
        # toggle_{set_id}_{topping_id} — но set_id тоже содержит _
        # формат: toggle_set_xs_topping_арахис
        # разберём по-другому: toggle_{set_id}_{topping_id}
        rest = data[7:]  # убираем "toggle_"
        # находим set_id и topping_id
        set_id = None
        topping_id = None
        for s in SETS:
            if rest.startswith(s["id"] + "_"):
                set_id = s["id"]
                topping_id = rest[len(s["id"]) + 1:]
                break

        if not set_id:
            return

        selected = context.user_data.get(f"toppings_{set_id}", [])
        if topping_id in selected:
            selected.remove(topping_id)
        else:
            selected.append(topping_id)
        context.user_data[f"toppings_{set_id}"] = selected

        s = get_set_by_id(set_id)
        text = (
            f"🍓 {s['name']}\n"
            f"{s['desc']}\n\n"
            f"💰 {s['price']}₽\n\n"
            f"Выбери посыпки и добавки:"
        )
        try:
            await query.edit_message_reply_markup(reply_markup=toppings_keyboard(set_id, selected))
        except Exception:
            await query.edit_message_text(text, reply_markup=toppings_keyboard(set_id, selected))

    # Добавить сет в корзину
    elif data.startswith("addset_"):
        set_id = data[7:]
        s = get_set_by_id(set_id)
        if not s:
            return

        selected = context.user_data.get(f"toppings_{set_id}", [])

        # Считаем цену с добавками
        extra_price = sum(
            get_topping_by_id(t_id)["price"]
            for t_id in selected
            if get_topping_by_id(t_id) and get_topping_by_id(t_id)["price"] > 0
        )
        total_price = s["price"] + extra_price

        # Формируем описание
        topping_names = [get_topping_by_id(t)["name"] for t in selected if get_topping_by_id(t)]
        topping_str = ", ".join(topping_names) if topping_names else "без посыпок"

        cart = context.user_data.setdefault("cart", {})
        cart_key = f"{set_id}_{'-'.join(sorted(selected))}"
        if cart_key in cart:
            cart[cart_key]["qty"] += 1
        else:
            cart[cart_key] = {
                "name": s["name"],
                "desc": topping_str,
                "price": total_price,
                "qty": 1
            }

        count = sum(v["qty"] for v in cart.values())
        total = sum(v["price"] * v["qty"] for v in cart.values())
        await query.answer(f"✅ {s['name']} добавлен! Корзина: {count} поз. / {total}₽", show_alert=False)


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = context.user_data.get("cart", {})
    text, keyboard = _build_cart_message(cart)
    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard)
    else:
        query = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(text, reply_markup=keyboard)
        except Exception:
            await query.message.reply_text(text, reply_markup=keyboard)


async def cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "show_cart":
        cart = context.user_data.get("cart", {})
        text, keyboard = _build_cart_message(cart)
        try:
            await query.edit_message_text(text, reply_markup=keyboard)
        except Exception:
            await query.message.reply_text(text, reply_markup=keyboard)

    elif data == "clear_cart":
        context.user_data["cart"] = {}
        try:
            await query.edit_message_text(
                "🗑 Корзина очищена.",
                reply_markup=sets_keyboard()
            )
        except Exception:
            await query.message.reply_text("🗑 Корзина очищена.", reply_markup=sets_keyboard())

    elif data == "checkout":
        cart = context.user_data.get("cart", {})
        if not cart:
            await query.answer("Корзина пуста!", show_alert=True)
            return
        total = sum(v["price"] * v["qty"] for v in cart.values())
        lines = "\n".join(
            f"- {v['name']} ({v['desc']}) x{v['qty']} = {v['price'] * v['qty']}р"
            for v in cart.values()
        )
        try:
            await query.edit_message_text(
                f"Подтверди заказ:\n\n{lines}\n\nИтого: {total}р\n\nПодтверждаешь?",
                reply_markup=confirm_order_keyboard()
            )
        except Exception:
            await query.message.reply_text(
                f"Подтверди заказ:\n\n{lines}\n\nИтого: {total}р\n\nПодтверждаешь?",
                reply_markup=confirm_order_keyboard()
            )

    elif data == "confirm_order":
        await _finalize_order(query, context)


def _build_cart_message(cart: dict):
    if not cart:
        return "🛒 Корзина пуста\n\nВыбери сет!", sets_keyboard()
    total = sum(v["price"] * v["qty"] for v in cart.values())
    lines = "\n".join(
        f"- {v['name']} ({v['desc']}) x{v['qty']} = {v['price'] * v['qty']}р"
        for v in cart.values()
    )
    return f"🛒 Твоя корзина:\n\n{lines}\n\nИтого: {total}р", cart_keyboard()


async def _finalize_order(query, context: ContextTypes.DEFAULT_TYPE):
    cart = context.user_data.get("cart", {})
    total = sum(v["price"] * v["qty"] for v in cart.values())
    lines = "\n".join(
        f"- {v['name']} ({v['desc']}) x{v['qty']} = {v['price'] * v['qty']}р"
        for v in cart.values()
    )
    description = lines + f"\n\nИтого: {total}р"
    context.user_data["pending_order_desc"] = description
    context.user_data["pending_order_total"] = total
    try:
        await query.edit_message_text(
            "Введи адрес доставки:\n\nНапример: ул. Ленина, д.5, кв.12"
        )
    except Exception:
        await query.message.reply_text(
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
        f"Заказ #{order_id} оформлен!\n\n{description}\n\nДоставка: {address}\n\nОжидайте звонка! 🍓",
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
