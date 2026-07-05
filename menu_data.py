# ─────────────────────────────────────────────
#  МЕНЮ Strawberry_Diora 🍓
#  Редактируй этот файл чтобы обновить меню
# ─────────────────────────────────────────────
#  photo: file_id из Telegram (получи через /addphoto)
#  Оставь photo=None если фото нет
# ─────────────────────────────────────────────

SETS = [
    {
        "id": "set_xs",
        "name": "Diora XS",
        "desc": "4 клубники в шоколаде",
        "price": 140,
        "photo": None,
    },
    {
        "id": "set_s",
        "name": "Diora S",
        "desc": "12-15 клубник в шоколаде",
        "price": 420,
        "photo": None,
    },
    {
        "id": "set_m",
        "name": "Diora M",
        "desc": "20-23 клубники в шоколаде",
        "price": 650,
        "photo": None,
    },
]

# Бесплатные посыпки
TOPPINGS = [
    {"id": "topping_arахис", "name": "Арахис", "price": 0},
    {"id": "topping_кокос", "name": "Кокос", "price": 0},
    {"id": "topping_орео", "name": "Орео", "price": 0},
]

# Платные добавки
EXTRAS = [
    {"id": "extra_ягоды", "name": "Свежие ягоды (голубика, клубника)", "price": 90},
]


def get_set_by_id(set_id: str):
    for s in SETS:
        if s["id"] == set_id:
            return s
    return None


def get_topping_by_id(t_id: str):
    for t in TOPPINGS:
        if t["id"] == t_id:
            return t
    for e in EXTRAS:
        if e["id"] == t_id:
            return e
    return None
