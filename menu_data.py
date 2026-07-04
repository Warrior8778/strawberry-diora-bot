# ─────────────────────────────────────────────
#  МЕНЮ Strawberry_Diora 🍓
#  Редактируй этот файл чтобы обновить меню
# ─────────────────────────────────────────────
#
#  photo: ссылка на фото ИЛИ file_id из Telegram
#  Оставь photo=None если фото нет
# ─────────────────────────────────────────────

MENU = {
    "🍕 Пицца": [
        {
            "id": "pizza_1",
            "name": "Маргарита",
            "desc": "Томатный соус, моцарелла, базилик",
            "price": 650,
            "photo": None,
        },
        {
            "id": "pizza_2",
            "name": "Пепперони",
            "desc": "Томатный соус, моцарелла, пепперони",
            "price": 750,
            "photo": None,
        },
        {
            "id": "pizza_3",
            "name": "4 сыра",
            "desc": "Моцарелла, чеддер, пармезан, дор-блю",
            "price": 800,
            "photo": None,
        },
    ],
    "🍔 Бургеры": [
        {
            "id": "burger_1",
            "name": "Классик",
            "desc": "Говяжья котлета, салат, томат, соус",
            "price": 450,
            "photo": None,
        },
        {
            "id": "burger_2",
            "name": "Чизбургер",
            "desc": "Говяжья котлета, чеддер, лук, соус",
            "price": 500,
            "photo": None,
        },
        {
            "id": "burger_3",
            "name": "Двойной",
            "desc": "Две котлеты, двойной сыр, бекон",
            "price": 650,
            "photo": None,
        },
    ],
    "🥗 Салаты": [
        {
            "id": "salad_1",
            "name": "Цезарь",
            "desc": "Курица, романо, пармезан, сухарики",
            "price": 380,
            "photo": None,
        },
        {
            "id": "salad_2",
            "name": "Греческий",
            "desc": "Овощи, оливки, фета, оливковое масло",
            "price": 350,
            "photo": None,
        },
    ],
    "🥤 Напитки": [
        {
            "id": "drink_1",
            "name": "Кола 0.5л",
            "desc": "Coca-Cola",
            "price": 120,
            "photo": None,
        },
        {
            "id": "drink_2",
            "name": "Сок апельсин",
            "desc": "Свежевыжатый 300мл",
            "price": 200,
            "photo": None,
        },
        {
            "id": "drink_3",
            "name": "Вода 0.5л",
            "desc": "Негазированная",
            "price": 80,
            "photo": None,
        },
    ],
    "🍰 Десерты": [
        {
            "id": "dessert_1",
            "name": "Чизкейк",
            "desc": "Нью-Йорк с ягодным соусом",
            "price": 320,
            "photo": None,
        },
        {
            "id": "dessert_2",
            "name": "Тирамису",
            "desc": "Классический итальянский",
            "price": 290,
            "photo": None,
        },
    ],
}


def get_item_by_id(item_id: str):
    """Найти блюдо по ID"""
    for category, items in MENU.items():
        for item in items:
            if item["id"] == item_id:
                return item, category
    return None, None


def get_categories():
    return list(MENU.keys())


def get_items_by_category(category: str):
    return MENU.get(category, [])
