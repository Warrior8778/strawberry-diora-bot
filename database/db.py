import aiosqlite
import os
from datetime import datetime

DB_PATH = "strawberry_diora.db"


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Клиенты
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                name TEXT,
                phone TEXT,
                username TEXT,
                registered_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Заказы
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER,
                telegram_id INTEGER,
                description TEXT,
                address TEXT,
                status TEXT DEFAULT 'new',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)

        # Бронирования
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                name TEXT,
                phone TEXT,
                date TEXT,
                time TEXT,
                persons INTEGER DEFAULT 1,
                comment TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Внутренние задачи
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                assigned_to INTEGER,
                created_by INTEGER,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'normal',
                created_at TEXT DEFAULT (datetime('now')),
                due_date TEXT
            )
        """)

        # История диалогов AI
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                role TEXT,
                message TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        await db.commit()
    print("✅ База данных инициализирована")


# ─── КЛИЕНТЫ ───────────────────────────────────────────────

async def get_or_create_client(telegram_id: int, name: str, username: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM clients WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            client = await cursor.fetchone()

        if not client:
            await db.execute(
                "INSERT INTO clients (telegram_id, name, username) VALUES (?, ?, ?)",
                (telegram_id, name, username)
            )
            await db.commit()
            async with db.execute(
                "SELECT * FROM clients WHERE telegram_id = ?", (telegram_id,)
            ) as cursor:
                client = await cursor.fetchone()

        return dict(client)


async def update_client_phone(telegram_id: int, phone: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE clients SET phone = ? WHERE telegram_id = ?",
            (phone, telegram_id)
        )
        await db.commit()


# ─── ЗАКАЗЫ ────────────────────────────────────────────────

async def create_order(telegram_id: int, description: str, address: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id FROM clients WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            client = await cursor.fetchone()

        client_id = client["id"] if client else None
        cursor = await db.execute(
            """INSERT INTO orders (client_id, telegram_id, description, address)
               VALUES (?, ?, ?, ?)""",
            (client_id, telegram_id, description, address)
        )
        await db.commit()
        return cursor.lastrowid


async def get_orders_by_user(telegram_id: int, limit: int = 5):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT * FROM orders WHERE telegram_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (telegram_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_all_orders(status: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status:
            async with db.execute(
                "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC",
                (status,)
            ) as cursor:
                rows = await cursor.fetchall()
        else:
            async with db.execute(
                "SELECT * FROM orders ORDER BY created_at DESC LIMIT 50"
            ) as cursor:
                rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE orders SET status = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (status, order_id)
        )
        await db.commit()


# ─── БРОНИРОВАНИЯ ──────────────────────────────────────────

async def create_booking(telegram_id: int, name: str, phone: str,
                          date: str, time: str, persons: int, comment: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO bookings (telegram_id, name, phone, date, time, persons, comment)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (telegram_id, name, phone, date, time, persons, comment)
        )
        await db.commit()
        return cursor.lastrowid


async def get_bookings_by_date(date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM bookings WHERE date = ? ORDER BY time",
            (date,)
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_pending_bookings():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM bookings WHERE status = 'pending' ORDER BY date, time"
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def update_booking_status(booking_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE bookings SET status = ? WHERE id = ?",
            (status, booking_id)
        )
        await db.commit()


# ─── ЗАДАЧИ ────────────────────────────────────────────────

async def create_task(title: str, description: str, created_by: int,
                       priority: str = "normal", due_date: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO tasks (title, description, created_by, priority, due_date)
               VALUES (?, ?, ?, ?, ?)""",
            (title, description, created_by, priority, due_date)
        )
        await db.commit()
        return cursor.lastrowid


async def get_open_tasks():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tasks WHERE status = 'open' ORDER BY priority DESC, created_at"
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def close_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET status = 'done' WHERE id = ?", (task_id,)
        )
        await db.commit()


# ─── ИСТОРИЯ ДИАЛОГОВ ──────────────────────────────────────

async def save_message(telegram_id: int, role: str, message: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO chat_history (telegram_id, role, message) VALUES (?, ?, ?)",
            (telegram_id, role, message)
        )
        await db.commit()


async def get_chat_history(telegram_id: int, limit: int = 10):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT role, message FROM chat_history
               WHERE telegram_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (telegram_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
        return [dict(r) for r in reversed(rows)]


async def clear_chat_history(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM chat_history WHERE telegram_id = ?", (telegram_id,)
        )
        await db.commit()
