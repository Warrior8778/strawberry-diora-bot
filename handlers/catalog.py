from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from menu_data import SETS, get_set_by_id, get_topping_by_id, TOPPINGS, EXTRAS
from utils.keyboards import (
    sets_keyboard, toppings_keyboard, cart_keyboard,
    confirm_order_keyboard, main_menu_keyboard,
    date_keyboard, time_keyboard
)
from utils.delivery import get_distance_km, calculate_delivery_cost
from database.db import create_order


async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    has_photos = any(s.get("photo") for s in SETS)
    if has_photos:
        for s in SETS:
            text = f"🍓 {s['name']}\n{s['desc']}\n\n💰 {s['price']} Rp"
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
            "🍓 Выбери свой сет клубники в шоколаде:",
            reply_markup=sets_keyboard()
        )


def _set_select_keyboard(set_id: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Выбрать", callback_data=f"set_{set_id}")]
    ])


async def catalog_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("set_"):
        set_id = data[4:]
        s = get_set_by_id(set_id)
        if not s:
            return
        context.user_data[f"toppings_{set_id}"] = []
        text = f"🍓 {s['name']}\n{s['desc']}\n\n💰 {s['price']} Rp\n\nВыбери посыпки и добавки:"
        selected = context.user_data.get(f"toppings_{set_id}", [])
        try:
            await query.edit_message_text(text, reply_markup=toppings_keyboard(set_id, selected))
        except Exception:
            await query.message.reply_text(text, reply_markup=toppings_keyboard(set_id, selected))

    elif data == "back_to_sets":
        try:
            await query.edit_message_text("🍓 Выбери свой сет:", reply_markup=sets_keyboard())
        except Exception:
            await query.message.reply_text("🍓 Выбери свой сет:", reply_markup=sets_keyboard())

    elif data.startswith("toggle_"):
        rest = data[7:]
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
        text = f"🍓 {s['name']}\n{s['desc']}\n\n💰 {s['price']} Rp\n\nВыбери посыпки и добавки:"
        try:
            await query.edit_message_reply_markup(reply_markup=toppings_keyboard(set_id, selected))
        except Exception:
            await query.edit_message_text(text, reply_markup=toppings_keyboard(set_id, selected))

    elif data.startswith("addset_"):
        set_id = data[7:]
        s = get_set_by_id(set_id)
        if not s:
            return
        selected = context.user_data.get(f"toppings_{set_id}", [])
        extra_price = sum(
            get_topping_by_id(t_id)["price"]
            for t_id in selected
            if get_topping_by_id(t_id) and get_topping_by_id(t_id)["price"] > 0
        )
        total_price = s["price"] + extra_price
        topping_names = [get_topping_by_id(t)["name"] for t in selected if get_topping_by_id(t)]
        topping_str = ", ".join(topping_names) if topping_names else "без посыпок"
        cart = context.user_data.setdefault("cart", {})
        cart_key = f"{set_id}_{'-'.join(sorted(selected))}"
        if cart_key in cart:
            cart[cart_key]["qty"] += 1
        else:
            cart[cart_key] = {"name": s["name"], "desc": topping_str, "price": total_price, "qty": 1}
        count = sum(v["qty"] for v in cart.values())
        total = sum(v["price"] * v["qty"] for v in cart.values())
        await query.answer(f"✅ {s['name']} добавлен!\nПерейди в 🛒 Корзину для оформления заказа", show_alert=True)


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
            await query.edit_message_text("🗑 Корзина очищена.", reply_markup=sets_keyboard())
        except Exception:
            await query.message.reply_text("🗑 Корзина очищена.", reply_markup=sets_keyboard())

    elif data == "checkout":
        cart = context.user_data.get("cart", {})
        if not cart:
            await query.answer("Корзина пуста!", show_alert=True)
            return
        await _start_checkout(query, context)


async def date_time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("date_"):
        date_val = data[5:]
        if date_val == "custom":
            context.user_data["checkout_step"] = "date_custom"
            await query.edit_message_text("📆 Введи дату доставки:\nНапример: 25.07.2024")
        else:
            context.user_data["delivery_date"] = date_val
            context.user_data["checkout_step"] = "time"
            await query.edit_message_text(
                f"📆 Дата: {date_val}\n\n🕐 Выбери время доставки:",
                reply_markup=time_keyboard()
            )

    elif data.startswith("time_"):
        time_val = data[5:]
        context.user_data["delivery_time"] = time_val
        await query.edit_message_text(f"🕐 Время: {time_val} — отлично!")
        await _finalize_order_from_callback(query, context)


def _build_cart_message(cart: dict):
    if not cart:
        return "🛒 Корзина пуста\n\nВыбери сет!", sets_keyboard()
    total = sum(v["price"] * v["qty"] for v in cart.values())
    lines = "\n".join(
        f"- {v['name']} ({v['desc']}) x{v['qty']} = {v['price'] * v['qty']} Rp"
        for v in cart.values()
    )
    return f"🛒 Твоя корзина:\n\n{lines}\n\nИтого: {total} Rp", cart_keyboard()


async def _start_checkout(query, context: ContextTypes.DEFAULT_TYPE):
    cart = context.user_data.get("cart", {})
    total = sum(v["price"] * v["qty"] for v in cart.values())
    lines = "\n".join(
        f"- {v['name']} ({v['desc']}) x{v['qty']} = {v['price'] * v['qty']} Rp"
        for v in cart.values()
    )
    context.user_data["pending_order_desc"] = lines
    context.user_data["pending_order_total"] = total
    context.user_data["awaiting_address"] = True
    context.user_data["checkout_step"] = "location"

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    maps_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗺 Открыть Google Maps", url="https://maps.google.com")]
    ])
    text = (
        "📍 Пришлите адрес доставки, чтобы наш администратор мог рассчитать финальную стоимость вместе с доставкой.\n\n"
        "Вы можете:\n"
        "• Открыть Google Maps, выбрать точку и отправить ссылку\n"
        "• Или написать адрес текстом"
    )
    try:
        await query.edit_message_text(text, reply_markup=maps_keyboard)
    except Exception:
        await query.message.reply_text(text, reply_markup=maps_keyboard)


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка геолокации от клиента"""
    if not context.user_data.get("awaiting_address"):
        return False
    if context.user_data.get("checkout_step") != "location":
        return False

    location = update.message.location
    if not location:
        return False



    distance = await get_distance_km(location.latitude, location.longitude)

    if distance:
        delivery_cost = calculate_delivery_cost(distance)
        context.user_data["delivery_address"] = f"📍 Геолокация ({location.latitude:.4f}, {location.longitude:.4f})"
        context.user_data["delivery_lat"] = location.latitude
        context.user_data["delivery_lng"] = location.longitude
        context.user_data["delivery_distance"] = distance
        context.user_data["delivery_cost"] = delivery_cost


    else:
        context.user_data["delivery_address"] = f"Геолокация ({location.latitude:.4f}, {location.longitude:.4f})"
        context.user_data["delivery_cost"] = 12000
        await update.message.reply_text("Не удалось рассчитать расстояние, стоимость доставки уточним при подтверждении.")

    context.user_data["checkout_step"] = "date"
    await update.message.reply_text(
        "📆 Выбери дату доставки:",
        reply_markup=date_keyboard()
    )
    return True


async def handle_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_address"):
        return False

    step = context.user_data.get("checkout_step")

    if step == "location":
        # Сначала проверяем не ссылка ли это Google Maps
        if await handle_maps_url(update, context):
            return True
        # Клиент написал адрес текстом
        context.user_data["delivery_address"] = update.message.text
        context.user_data["delivery_cost"] = None
        context.user_data["checkout_step"] = "date"
        await update.message.reply_text(
            "📆 Выбери дату доставки:",
            reply_markup=date_keyboard()
        )
        return True

    elif step == "date_custom":
        context.user_data["delivery_date"] = update.message.text
        context.user_data["checkout_step"] = "time"
        await update.message.reply_text(
            f"📆 Дата: {update.message.text}\n\n🕐 Выбери время доставки:",
            reply_markup=time_keyboard()
        )
        return True

    return False


async def _finalize_order_from_callback(query, context: ContextTypes.DEFAULT_TYPE):
    user = query.from_user
    order_lines = context.user_data.get("pending_order_desc", "")
    order_total = context.user_data.get("pending_order_total", 0)
    address = context.user_data.get("delivery_address", "")
    date = context.user_data.get("delivery_date", "")
    time = context.user_data.get("delivery_time", "")

    full_description = (
        f"{order_lines}\n\n"
        f"💰 Итого: {order_total:,} Rp\n"
        f"🚗 Доставка: уточним при звонке"
    )

    order_id = await create_order(user.id, full_description, address)

    await query.message.reply_text(
        f"✅ Заказ #{order_id} оформлен!\n\n"
        f"{order_lines}\n\n"
        f"💰 Итого: {order_total:,} Rp\n"
        f"🚗 Доставка: уточним при звонке\n\n"
        f"📍 Адрес: {address}\n"
        f"📆 Дата: {date}\n"
        f"🕐 Время: {time}\n\n"
        f"Ожидайте звонка для подтверждения! 🍓",
        reply_markup=main_menu_keyboard()
    )

    admin_ids = context.bot_data.get("admin_ids", [])
    from utils.keyboards import order_status_keyboard

    for admin_id in admin_ids:
        try:
            msg = (
                f"New Order #{order_id}\n\n"
                f"Client: {user.full_name} (@{user.username or '-'})\n\n"
                f"{order_lines}\n\n"
                f"Order Total: {order_total:,} Rp (delivery TBD)\n\n"
                f"Address: {address}\n"
                f"Date: {date}\n"
                f"Time: {time}"
            )
            await context.bot.send_message(
                chat_id=admin_id,
                text=msg,
                reply_markup=order_status_keyboard(order_id)
            )
        except Exception:
            pass

    context.user_data["cart"] = {}
    context.user_data["awaiting_address"] = False
    context.user_data["checkout_step"] = None
    context.user_data["delivery_cost"] = None
    context.user_data["delivery_distance"] = None
    context.user_data["delivery_lat"] = None
    context.user_data["delivery_lng"] = None


async def handle_maps_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ссылки Google Maps вместо геолокации"""
    if not context.user_data.get("awaiting_address"):
        return False
    if context.user_data.get("checkout_step") != "location":
        return False

    text = update.message.text
    from utils.delivery import is_google_maps_url, resolve_google_maps_url, get_distance_km, calculate_delivery_cost

    if not is_google_maps_url(text):
        return False



    lat, lng = await resolve_google_maps_url(text)

    if lat and lng:
        distance = await get_distance_km(lat, lng)
        if distance:
            delivery_cost = calculate_delivery_cost(distance)
            context.user_data["delivery_address"] = f"📍 {text}"
            context.user_data["delivery_lat"] = lat
            context.user_data["delivery_lng"] = lng
            context.user_data["delivery_distance"] = distance
            context.user_data["delivery_cost"] = delivery_cost


        else:
            context.user_data["delivery_address"] = text
            context.user_data["delivery_cost"] = None
            await update.message.reply_text("Не удалось рассчитать расстояние, уточним при подтверждении.")
    else:
        context.user_data["delivery_address"] = text
        context.user_data["delivery_cost"] = None
        await update.message.reply_text("Не удалось определить координаты, уточним при подтверждении.")

    context.user_data["checkout_step"] = "date"
    await update.message.reply_text(
        "📆 Выбери дату доставки:",
        reply_markup=date_keyboard()
    )
    return True
