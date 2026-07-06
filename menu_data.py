SETS = [
    {
        "id": "set_xs",
        "name": "Diora XS",
        "desc": "4 chocolate-covered strawberries",
        "price": 140000,
        "photo": "AgACAgIAAxkBAANyakpXr3QyVTtwTCYxDoczTiUYzB8AAjQZaxvS_FFKjOiugMc9P7ABAAMCAAN5AAM8BA",
    },
    {
        "id": "set_s",
        "name": "Diora S",
        "desc": "12-15 chocolate-covered strawberries",
        "price": 420000,
        "photo": "AgACAgIAAxkBAANuakpXZqe1d0CeipnQYlicJP1py8oAAjIZaxvS_FFKfa3PTvP8hEoBAAMCAAN5AAM8BA",
    },
    {
        "id": "set_m",
        "name": "Diora M",
        "desc": "20-23 chocolate-covered strawberries",
        "price": 650000,
        "photo": "AgACAgIAAxkBAANwakpXmIfMEK2sgUo6de_1AUbtn3oAAjMZaxvS_FFKPXccg708R7sBAAMCAAN5AAM8BA",
    },
]

TOPPINGS = [
    {"id": "topping_peanut", "name": "Peanut", "price": 0},
    {"id": "topping_coconut", "name": "Coconut", "price": 0},
    {"id": "topping_oreo", "name": "Oreo", "price": 0},
]

EXTRAS = [
    {"id": "extra_berries", "name": "Fresh berries (blueberry, strawberry)", "price": 90},
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
