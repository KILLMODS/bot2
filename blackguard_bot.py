#!/usr/bin/env python3
"""
BlackGuard — Telegram Business bot
-----------------------------------
pip install python-telegram-bot==21.*
python blackguard_bot.py
"""

import asyncio
import logging
import os
import html
import random
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    ContextTypes,
    TypeHandler,
    CallbackQueryHandler,
    CommandHandler,
)
from telegram.error import TelegramError, BadRequest

# ---------------------------------------------------------------------------
# Конфиг
# ---------------------------------------------------------------------------

BOT_TOKEN = os.getenv("BOT_TOKEN", "9112401681:AAEhit89PgxE8EFE0ctQ064Z-2FisaQFWCY").strip()
BOT_USERNAME = "@BIackGuardRobot"
BOT_NAME = "BlackGuard"

DB_PATH = Path(__file__).parent / "blackguard.db"

AUTOREPLY_TEXT = (
    "Здравствуйте! Сейчас я не на связи, отвечу вам при первой "
    "возможности. Это автоматическое сообщение."
)

# --- команды ---
CMD_AWAY = ".away"
CMD_ONLINE = ".online"
CMD_MUTE = ".mute"
CMD_UNMUTE = ".unmute"
CMD_STATUS = ".status"
CMD_HELP = ".help"
CMD_MUTELIST = ".mutelist"
CMD_SETREPLY = ".setreply"
CMD_AFK = ".afk"
CMD_BACK = ".back"
CMD_REMIND = ".remind"
CMD_NOTE_ADD = ".note"
CMD_NOTE_LIST = ".notes"
CMD_NOTE_DEL = ".delnote"
CMD_BANWORD_ADD = ".banword"
CMD_BANWORD_LIST = ".banwords"
CMD_BANWORD_DEL = ".unbanword"
CMD_QUIET_START = ".quiet"
CMD_QUIET_STOP = ".loud"
CMD_STATS = ".stats"
CMD_PING = ".ping"
CMD_UPTIME = ".uptime"
CMD_ID = ".id"

# Команда признания / предложения встречаться
CMD_ASKOUT = ".askout"
CMD_PROPOSAL = ".proposal"
CMD_LOVEASK = ".loveask"

# Игры
CMD_GAME_DICE = ".dice"
CMD_GAME_BASKET = ".basket"
CMD_GAME_DARTS = ".darts"
CMD_GAME_BOWLING = ".bowling"
CMD_GAME_FOOTBALL = ".football"

# Весёлые
CMD_LOVE = ".love"
CMD_COMPLIMENT = ".compliment"
CMD_QUOTE = ".quote"
CMD_FACT = ".fact"
CMD_TIP = ".tip"
CMD_ROAST = ".roast"

# Эффекты (текст + эффект)
CMD_FX_FIRE = ".fire"
CMD_FX_CONFETTI = ".confetti"
CMD_FX_HEART = ".heart"
CMD_FX_POO = ".poo"
CMD_FX_BOOM = ".boom"
CMD_FX_SPARKLES = ".sparkles"
CMD_FX_BALLOON = ".balloon"
CMD_FX_PARTY = ".party"
CMD_FX_THUMBSUP = ".thumbsup"
CMD_FX_FIREWORKS = ".fireworks"
CMD_FX_LIGHTNING = ".lightning"
CMD_FX_HUNDRED = ".hundred"

# Анимации
CMD_TYPE = ".type"
CMD_LOADING = ".loading"
CMD_GLITCH = ".glitch"

GAME_EMOJI = {
    "dice": "🎲", "basket": "🏀", "darts": "🎯",
    "bowling": "🎳", "football": "⚽",
}

# Эффекты Telegram
FX = {
    "fire":      "5104841245755180586",
    "confetti":  "5046509860389126442",
    "thumbsup":  "5107584321108051014",
    "poo":       "5046589136895476101",
    "heart":     "5159385139981059251",
    "party":     "5104858069142078462",
    "fireworks": "5044134455711629726",
    "sparkles":  "5105016972528124222",
    "balloon":   "5044551451480063882",
    "lightning": "5048608250411827902",
    "boom":      "5051735441012713274",
    "hundred":   "5051224801007413241",
}

LOVE_PHRASES = [
    "Ты — лучшее, что случилось со мной в этом чате. И вообще. 💙",
    "Просто напоминаю: ты невероятная.",
    "Если бы за тебя начислялись баллы, я бы уже был миллиардером.",
    "Скучаю. Да-да, прямо сейчас.",
    "Ты моя любимая причина отвлекаться от дел.",
    "Там, где ты — там и дом.",
    "Сегодня тоже хочу сказать, что ты самая лучшая.",
    "Если это читаешь не ты — всё равно, ты классная.",
]

COMPLIMENTS = [
    "У тебя отличный вкус — ты же общаешься со мной 😎",
    "Ты явно из тех людей, кто читает документацию до конца.",
    "Твоя энергетика делает этот чат лучше.",
    "С тобой приятно иметь дело.",
]

QUOTES = [
    "«Простота — залог надёжности.» — Эдсгер Дейкстра",
    "«Сначала решите проблему, потом пишите код.» — Джон Джонсон",
    "«Лучший код — тот, который не нужно писать.» — неизвестный мудрец",
]

FACTS = [
    "Telegram был запущен в 2013 году братьями Дуровыми.",
    "В среднем человек проверяет телефон 96 раз в день.",
    "Осьминоги имеют три сердца и голубую кровь.",
]

TIPS = [
    "Совет: закрепи важные чаты, чтобы не терять их.",
    "Совет: используй `.mute` для спамеров — и тишина.",
    "Совет: `.setreply` позволяет менять автоответ под собеседника.",
    "Совет: `.stats` покажет, сколько сообщений ты на самом деле получаешь.",
]

ROASTS = [
    "Ты не плохой человек, ты просто… оригинальный.",
    "Твой код работает — и это уже повод для гордости.",
    "Ты как Wi-Fi в поезде: вроде есть, но лучше не полагаться.",
]

COOLDOWN_STEPS = [600, 1200, 1800, 3600, 7200]
TYPING_STEPS = [500, 1000, 1500, 2000, 2500, 3000]

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("blackguard")

# ---------------------------------------------------------------------------
# БД
# ---------------------------------------------------------------------------

def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_init() -> None:
    conn = db_connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS connections (
            business_connection_id TEXT PRIMARY KEY,
            owner_user_id INTEGER NOT NULL,
            is_away INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS muted (
            business_connection_id TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            PRIMARY KEY (business_connection_id, chat_id)
        );
        CREATE TABLE IF NOT EXISTS seen_messages (
            business_connection_id TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            from_user_id INTEGER,
            from_name TEXT,
            text TEXT,
            created_at INTEGER NOT NULL,
            PRIMARY KEY (business_connection_id, chat_id, message_id)
        );
        CREATE TABLE IF NOT EXISTS autoreply_sent (
            business_connection_id TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            last_sent_at INTEGER NOT NULL,
            PRIMARY KEY (business_connection_id, chat_id)
        );
        CREATE TABLE IF NOT EXISTS custom_reply (
            business_connection_id TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            PRIMARY KEY (business_connection_id, chat_id)
        );
        CREATE TABLE IF NOT EXISTS settings (
            business_connection_id TEXT PRIMARY KEY,
            cooldown_sec INTEGER NOT NULL DEFAULT 3600,
            typing_delay_ms INTEGER NOT NULL DEFAULT 1500,
            quiet_from INTEGER NOT NULL DEFAULT 23,
            quiet_to   INTEGER NOT NULL DEFAULT 8,
            quiet_enabled INTEGER NOT NULL DEFAULT 0,
            autoreply_enabled INTEGER NOT NULL DEFAULT 1,
            forward_deleted INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS afk (
            business_connection_id TEXT NOT NULL,
            since_ts INTEGER NOT NULL,
            reason TEXT,
            PRIMARY KEY (business_connection_id)
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_connection_id TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS banwords (
            business_connection_id TEXT NOT NULL,
            word TEXT NOT NULL,
            PRIMARY KEY (business_connection_id, word)
        );
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            due_ts INTEGER NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS stats (
            business_connection_id TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            msgs_in INTEGER NOT NULL DEFAULT 0,
            msgs_deleted INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (business_connection_id, chat_id)
        );
    """)
    conn.commit(); conn.close()


def upsert_connection(bc_id: str, owner_id: int) -> None:
    conn = db_connect()
    conn.execute(
        """INSERT INTO connections (business_connection_id, owner_user_id, is_away, created_at)
           VALUES (?, ?, COALESCE((SELECT is_away FROM connections WHERE business_connection_id = ?), 0), ?)
           ON CONFLICT(business_connection_id) DO UPDATE SET owner_user_id = excluded.owner_user_id""",
        (bc_id, owner_id, bc_id, int(time.time())),
    )
    conn.execute("INSERT OR IGNORE INTO settings (business_connection_id) VALUES (?)", (bc_id,))
    conn.commit(); conn.close()


def get_owner_id(bc_id: str) -> int | None:
    conn = db_connect()
    row = conn.execute(
        "SELECT owner_user_id FROM connections WHERE business_connection_id = ?", (bc_id,)
    ).fetchone()
    conn.close()
    return row["owner_user_id"] if row else None


def list_connections_for_owner(owner_id: int) -> list[str]:
    conn = db_connect()
    rows = conn.execute(
        "SELECT business_connection_id FROM connections WHERE owner_user_id = ? ORDER BY created_at",
        (owner_id,),
    ).fetchall()
    conn.close()
    return [r["business_connection_id"] for r in rows]


def set_away(bc_id: str, away: bool) -> None:
    conn = db_connect()
    conn.execute("UPDATE connections SET is_away = ? WHERE business_connection_id = ?",
                 (1 if away else 0, bc_id))
    conn.commit(); conn.close()


def is_away(bc_id: str) -> bool:
    conn = db_connect()
    row = conn.execute(
        "SELECT is_away FROM connections WHERE business_connection_id = ?", (bc_id,)
    ).fetchone()
    conn.close()
    return bool(row and row["is_away"])


def get_settings(bc_id: str) -> dict:
    conn = db_connect()
    row = conn.execute(
        "SELECT * FROM settings WHERE business_connection_id = ?", (bc_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


def update_setting(bc_id: str, key: str, value) -> None:
    allowed = {"cooldown_sec", "typing_delay_ms", "quiet_from", "quiet_to",
               "quiet_enabled", "autoreply_enabled", "forward_deleted"}
    if key not in allowed:
        return
    conn = db_connect()
    conn.execute(f"UPDATE settings SET {key} = ? WHERE business_connection_id = ?", (value, bc_id))
    conn.commit(); conn.close()


def mute_chat(bc_id: str, chat_id: int) -> None:
    conn = db_connect()
    conn.execute("INSERT OR IGNORE INTO muted (business_connection_id, chat_id) VALUES (?, ?)",
                 (bc_id, chat_id))
    conn.commit(); conn.close()


def unmute_chat(bc_id: str, chat_id: int) -> None:
    conn = db_connect()
    conn.execute("DELETE FROM muted WHERE business_connection_id = ? AND chat_id = ?",
                 (bc_id, chat_id))
    conn.commit(); conn.close()


def is_muted(bc_id: str, chat_id: int) -> bool:
    conn = db_connect()
    row = conn.execute(
        "SELECT 1 FROM muted WHERE business_connection_id = ? AND chat_id = ?",
        (bc_id, chat_id),
    ).fetchone()
    conn.close()
    return row is not None


def list_muted_chats(bc_id: str) -> list[int]:
    conn = db_connect()
    rows = conn.execute(
        "SELECT chat_id FROM muted WHERE business_connection_id = ?", (bc_id,)
    ).fetchall()
    conn.close()
    return [r["chat_id"] for r in rows]


def set_custom_reply(bc_id: str, chat_id: int, text: str) -> None:
    conn = db_connect()
    conn.execute(
        """INSERT INTO custom_reply (business_connection_id, chat_id, text) VALUES (?, ?, ?)
           ON CONFLICT(business_connection_id, chat_id) DO UPDATE SET text = excluded.text""",
        (bc_id, chat_id, text),
    )
    conn.commit(); conn.close()


def get_custom_reply(bc_id: str, chat_id: int) -> str | None:
    conn = db_connect()
    row = conn.execute(
        "SELECT text FROM custom_reply WHERE business_connection_id = ? AND chat_id = ?",
        (bc_id, chat_id),
    ).fetchone()
    conn.close()
    return row["text"] if row else None


def remember_message(bc_id: str, chat_id: int, message_id: int,
                     from_user_id: int | None, from_name: str | None, text: str | None) -> None:
    conn = db_connect()
    conn.execute(
        """INSERT OR REPLACE INTO seen_messages
           (business_connection_id, chat_id, message_id, from_user_id, from_name, text, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (bc_id, chat_id, message_id, from_user_id, from_name, text, int(time.time())),
    )
    conn.commit(); conn.close()


def get_remembered_message(bc_id: str, chat_id: int, message_id: int):
    conn = db_connect()
    row = conn.execute(
        "SELECT * FROM seen_messages WHERE business_connection_id=? AND chat_id=? AND message_id=?",
        (bc_id, chat_id, message_id),
    ).fetchone()
    conn.close()
    return row


def should_send_autoreply(bc_id: str, chat_id: int, cooldown_sec: int) -> bool:
    conn = db_connect()
    row = conn.execute(
        "SELECT last_sent_at FROM autoreply_sent WHERE business_connection_id = ? AND chat_id = ?",
        (bc_id, chat_id),
    ).fetchone()
    now = int(time.time())
    send = (row is None) or (now - row["last_sent_at"] >= cooldown_sec)
    if send:
        conn.execute(
            """INSERT INTO autoreply_sent (business_connection_id, chat_id, last_sent_at)
               VALUES (?, ?, ?)
               ON CONFLICT(business_connection_id, chat_id) DO UPDATE SET last_sent_at = excluded.last_sent_at""",
            (bc_id, chat_id, now),
        )
        conn.commit()
    conn.close()
    return send


def set_afk(bc_id: str, reason: str | None) -> None:
    conn = db_connect()
    conn.execute(
        """INSERT INTO afk (business_connection_id, since_ts, reason) VALUES (?, ?, ?)
           ON CONFLICT(business_connection_id) DO UPDATE SET since_ts=excluded.since_ts, reason=excluded.reason""",
        (bc_id, int(time.time()), reason),
    )
    conn.commit(); conn.close()


def clear_afk(bc_id: str) -> None:
    conn = db_connect()
    conn.execute("DELETE FROM afk WHERE business_connection_id = ?", (bc_id,))
    conn.commit(); conn.close()


def get_afk(bc_id: str):
    conn = db_connect()
    row = conn.execute("SELECT * FROM afk WHERE business_connection_id = ?", (bc_id,)).fetchone()
    conn.close()
    return row


def add_note(bc_id: str, text: str) -> int:
    conn = db_connect()
    cur = conn.execute(
        "INSERT INTO notes (business_connection_id, text, created_at) VALUES (?, ?, ?)",
        (bc_id, text, int(time.time())),
    )
    conn.commit(); nid = cur.lastrowid; conn.close()
    return nid


def list_notes(bc_id: str) -> list[dict]:
    conn = db_connect()
    rows = conn.execute(
        "SELECT * FROM notes WHERE business_connection_id = ? ORDER BY id", (bc_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def del_note(bc_id: str, note_id: int) -> bool:
    conn = db_connect()
    cur = conn.execute("DELETE FROM notes WHERE business_connection_id = ? AND id = ?",
                       (bc_id, note_id))
    conn.commit(); ok = cur.rowcount > 0; conn.close()
    return ok


def add_banword(bc_id: str, word: str) -> None:
    conn = db_connect()
    conn.execute("INSERT OR IGNORE INTO banwords (business_connection_id, word) VALUES (?, ?)",
                 (bc_id, word.lower()))
    conn.commit(); conn.close()


def del_banword(bc_id: str, word: str) -> bool:
    conn = db_connect()
    cur = conn.execute("DELETE FROM banwords WHERE business_connection_id = ? AND word = ?",
                       (bc_id, word.lower()))
    conn.commit(); ok = cur.rowcount > 0; conn.close()
    return ok


def list_banwords(bc_id: str) -> list[str]:
    conn = db_connect()
    rows = conn.execute(
        "SELECT word FROM banwords WHERE business_connection_id = ?", (bc_id,)
    ).fetchall()
    conn.close()
    return [r["word"] for r in rows]


def add_reminder(owner_id: int, text: str, due_ts: int) -> int:
    conn = db_connect()
    cur = conn.execute(
        "INSERT INTO reminders (owner_user_id, text, due_ts) VALUES (?, ?, ?)",
        (owner_id, text, due_ts),
    )
    conn.commit(); rid = cur.lastrowid; conn.close()
    return rid


def pop_due_reminders(now_ts: int) -> list[dict]:
    conn = db_connect()
    rows = conn.execute(
        "SELECT * FROM reminders WHERE done = 0 AND due_ts <= ?", (now_ts,)
    ).fetchall()
    for r in rows:
        conn.execute("UPDATE reminders SET done = 1 WHERE id = ?", (r["id"],))
    conn.commit(); conn.close()
    return [dict(r) for r in rows]


def bump_stat(bc_id: str, chat_id: int, field: str) -> None:
    if field not in ("msgs_in", "msgs_deleted"):
        return
    conn = db_connect()
    conn.execute(
        f"""INSERT INTO stats (business_connection_id, chat_id, {field}) VALUES (?, ?, 1)
            ON CONFLICT(business_connection_id, chat_id) DO UPDATE SET {field} = {field} + 1""",
        (bc_id, chat_id),
    )
    conn.commit(); conn.close()


def get_stats(bc_id: str) -> list[dict]:
    conn = db_connect()
    rows = conn.execute(
        "SELECT * FROM stats WHERE business_connection_id = ? ORDER BY msgs_in DESC LIMIT 10",
        (bc_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def total_stats(bc_id: str) -> tuple[int, int]:
    conn = db_connect()
    row = conn.execute(
        "SELECT COALESCE(SUM(msgs_in),0) a, COALESCE(SUM(msgs_deleted),0) b FROM stats WHERE business_connection_id = ?",
        (bc_id,),
    ).fetchone()
    conn.close()
    return (row["a"], row["b"])


# ---------------------------------------------------------------------------
# Форматтеры
# ---------------------------------------------------------------------------

SEP = "━━━━━━━━━━━━━━━"

def h(icon: str, title: str) -> str:
    return f"{icon} <b>{html.escape(title)}</b>\n{SEP}"

def kv(key: str, value: str) -> str:
    return f"• {html.escape(key)}: <b>{html.escape(value)}</b>"

def code(v) -> str:
    return f"<code>{html.escape(str(v))}</code>"

def quote(t: str) -> str:
    return f"<blockquote>{html.escape(t)}</blockquote>"


def _describe_message(msg) -> str | None:
    if msg is None:
        return None
    text = getattr(msg, "text", None) or getattr(msg, "caption", None)
    if text:
        return text
    for attr, label in [
        ("photo", "[фото]"), ("video", "[видео]"),
        ("video_note", "[видеосообщение]"), ("voice", "[голосовое]"),
        ("audio", "[аудио]"), ("document", "[документ]"),
        ("sticker", "[стикер]"), ("animation", "[гиф]"),
        ("contact", "[контакт]"), ("location", "[локация]"),
        ("poll", "[опрос]"),
    ]:
        if getattr(msg, attr, None):
            return label
    return None


# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------

def _is_cmd(text_lowered: str, cmd: str) -> bool:
    if not text_lowered.startswith(cmd):
        return False
    if len(text_lowered) == len(cmd):
        return True
    return text_lowered[len(cmd)].isspace()


def _arg_or(text: str, cmd: str, default: int) -> int:
    rest = text[len(cmd):].strip()
    if rest:
        try:
            return int(rest)
        except ValueError:
            pass
    return default


def _fmt_dur(secs: int) -> str:
    d, rem = divmod(secs, 86400)
    h_, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if d: parts.append(f"{d}д")
    if h_: parts.append(f"{h_}ч")
    if m: parts.append(f"{m}м")
    if s or not parts: parts.append(f"{s}с")
    return " ".join(parts)


async def safe_edit(q, text: str, reply_markup=None, parse_mode=ParseMode.HTML):
    try:
        await q.edit_message_text(text=text, parse_mode=parse_mode, reply_markup=reply_markup)
    except BadRequest as e:
        m = str(e).lower()
        if "message is not modified" in m:
            return
        if "can't parse entities" in m or "unsupported start tag" in m or "can't find end tag" in m:
            log.warning("HTML parse error, fallback to plain: %s", e)
            plain = re.sub(r"<[^>]+>", "", text)
            try:
                await q.edit_message_text(text=plain, reply_markup=reply_markup)
            except BadRequest as e2:
                if "message is not modified" not in str(e2).lower():
                    log.error("Fallback edit failed: %s", e2)
            return
        log.error("edit_message_text BadRequest: %s", e)
    except TelegramError as e:
        log.error("edit_message_text TelegramError: %s", e)


# ---------------------------------------------------------------------------
# Анимации
# ---------------------------------------------------------------------------

async def animate_type_text(context, bc_id: str, chat_id: int, final_text: str,
                            delay: float = 0.15, prefix: str = "⌨️ "):
    try:
        msg = await context.bot.send_message(
            chat_id=chat_id, text=f"{prefix}▌",
            business_connection_id=bc_id,
        )
    except TelegramError as e:
        log.error("animate_type start: %s", e)
        return

    try:
        await context.bot.send_chat_action(
            chat_id=chat_id, action=ChatAction.TYPING, business_connection_id=bc_id)
    except TelegramError:
        pass

    current = ""
    for ch in final_text:
        current += ch
        try:
            await msg.edit_text(f"{prefix}{html.escape(current)}▌", parse_mode=ParseMode.HTML)
        except TelegramError:
            pass
        await asyncio.sleep(delay)

    try:
        await msg.edit_text(f"{prefix}{html.escape(final_text)}", parse_mode=ParseMode.HTML)
    except TelegramError:
        pass


async def animate_loading(context, bc_id: str, chat_id: int, final_text: str,
                          steps: int = 4, delay: float = 0.5):
    spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    try:
        msg = await context.bot.send_message(
            chat_id=chat_id, text="⏳ Загрузка ",
            business_connection_id=bc_id,
        )
    except TelegramError as e:
        log.error("animate_loading start: %s", e)
        return

    for i in range(steps * 4):
        spinner = spinners[i % len(spinners)]
        dots = "." * ((i // 4) % 4)
        try:
            await msg.edit_text(f"⏳ Загрузка {spinner}{dots}")
        except TelegramError:
            pass
        await asyncio.sleep(delay)

    try:
        await msg.edit_text(final_text, parse_mode=ParseMode.HTML)
    except TelegramError:
        pass


async def animate_glitch(context, bc_id: str, chat_id: int, final_text: str,
                         steps: int = 5, delay: float = 0.3):
    glitch_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"
    try:
        msg = await context.bot.send_message(
            chat_id=chat_id, text="⚡",
            business_connection_id=bc_id,
        )
    except TelegramError as e:
        log.error("animate_glitch start: %s", e)
        return

    for _ in range(steps):
        mutated = "".join(
            random.choice(glitch_chars) if random.random() < 0.3 else c
            for c in final_text
        )
        try:
            await msg.edit_text(f"⚡ <code>{html.escape(mutated)}</code>",
                                parse_mode=ParseMode.HTML)
        except TelegramError:
            pass
        await asyncio.sleep(delay)

    try:
        await msg.edit_text(f"⚡ <b>{html.escape(final_text)}</b>", parse_mode=ParseMode.HTML)
    except TelegramError:
        pass


# ---------------------------------------------------------------------------
# Игры
# ---------------------------------------------------------------------------

games: dict[str, dict] = {}
game_counter = 0


def new_game(bc_id: str, chat_id: int, kind: str) -> str:
    global game_counter
    game_counter += 1
    game_key = f"g{game_counter}"
    games[game_key] = {
        "kind": kind, "bc_id": bc_id, "chat_id": chat_id,
        "players": [], "scores": {}, "created": time.time(),
    }
    return game_key


def cleanup_old_games():
    now = time.time()
    for k in [k for k, v in games.items() if now - v["created"] > 600]:
        games.pop(k, None)


# ---------------------------------------------------------------------------
# Панель
# ---------------------------------------------------------------------------

def panel_main_kb(bc_id: str | None) -> InlineKeyboardMarkup:
    b = bc_id or "-"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Настройки", callback_data=f"p:settings:{b}")],
        [InlineKeyboardButton("🚫 Заглушки", callback_data=f"p:muted:{b}"),
         InlineKeyboardButton("✍️ Автоответ", callback_data=f"p:reply:{b}")],
        [InlineKeyboardButton("📝 Заметки", callback_data=f"p:notes:{b}"),
         InlineKeyboardButton("🔞 Банворды", callback_data=f"p:ban:{b}")],
        [InlineKeyboardButton("📊 Статистика", callback_data=f"p:stats:{b}"),
         InlineKeyboardButton("🎮 Игры", callback_data="p:games")],
        [InlineKeyboardButton("✨ Эффекты", callback_data="p:fx"),
         InlineKeyboardButton("⌨️ Анимации", callback_data="p:anim")],
        [InlineKeyboardButton("📋 Все команды", callback_data="p:help")],
    ])


def panel_games_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Кубик", callback_data="g:info:dice"),
         InlineKeyboardButton("🏀 Баскетбол", callback_data="g:info:basket")],
        [InlineKeyboardButton("🎯 Дартс", callback_data="g:info:darts"),
         InlineKeyboardButton("🎳 Боулинг", callback_data="g:info:bowling")],
        [InlineKeyboardButton("⚽ Футбол", callback_data="g:info:football")],
        [InlineKeyboardButton("🔙 Назад", callback_data="p:main:-")],
    ])


def panel_fx_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Fire", callback_data="fx:fire"),
         InlineKeyboardButton("🎉 Confetti", callback_data="fx:confetti")],
        [InlineKeyboardButton("❤️ Heart", callback_data="fx:heart"),
         InlineKeyboardButton("💥 Boom", callback_data="fx:boom")],
        [InlineKeyboardButton("🎇 Sparkles", callback_data="fx:sparkles"),
         InlineKeyboardButton("🎈 Balloon", callback_data="fx:balloon")],
        [InlineKeyboardButton("🎊 Party", callback_data="fx:party"),
         InlineKeyboardButton("🎆 Fireworks", callback_data="fx:fireworks")],
        [InlineKeyboardButton("⚡ Lightning", callback_data="fx:lightning"),
         InlineKeyboardButton("💯 Hundred", callback_data="fx:hundred")],
        [InlineKeyboardButton("💩 Poo", callback_data="fx:poo"),
         InlineKeyboardButton("👍 Thumbsup", callback_data="fx:thumbsup")],
        [InlineKeyboardButton("🔙 Назад", callback_data="p:main:-")],
    ])


def panel_anim_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⌨️ .type — печатает по буквам", callback_data="anim:type")],
        [InlineKeyboardButton("⏳ .loading — загрузка + текст", callback_data="anim:loading")],
        [InlineKeyboardButton("⚡ .glitch — глитч + текст", callback_data="anim:glitch")],
        [InlineKeyboardButton("🔙 Назад", callback_data="p:main:-")],
    ])


def panel_settings_kb(bc_id: str) -> InlineKeyboardMarkup:
    s = get_settings(bc_id)
    qf = s.get("quiet_from") or 23
    qt = s.get("quiet_to") or 8
    cd = s.get("cooldown_sec") or 3600
    td = s.get("typing_delay_ms") or 1500
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"Автоответ: {'🟢 вкл' if s.get('autoreply_enabled') else '🔴 выкл'}",
            callback_data=f"t:autoreply_enabled:{bc_id}")],
        [InlineKeyboardButton(
            f"Уведомления об удалённых: {'🟢 вкл' if s.get('forward_deleted') else '🔴 выкл'}",
            callback_data=f"t:forward_deleted:{bc_id}")],
        [InlineKeyboardButton(
            f"Тихие часы: {'🟢 вкл' if s.get('quiet_enabled') else '🔴 выкл'}",
            callback_data=f"t:quiet_enabled:{bc_id}")],
        [InlineKeyboardButton(f"С {qf:02d}:00", callback_data=f"q:from:{bc_id}"),
         InlineKeyboardButton(f"До {qt:02d}:00", callback_data=f"q:to:{bc_id}")],
        [InlineKeyboardButton(
            f"Кулдаун автоответа: {cd//60} мин", callback_data=f"c:cooldown:{bc_id}")],
        [InlineKeyboardButton(
            f"Задержка «печатает»: {td} мс", callback_data=f"t:typing:{bc_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"p:main:{bc_id}")],
    ])


def panel_muted_kb(bc_id: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"🔊 Снять {cid}", callback_data=f"u:{cid}:{bc_id}")]
            for cid in list_muted_chats(bc_id)]
    rows.append([InlineKeyboardButton("🔙 Назад", callback_data=f"p:main:{bc_id}")])
    return InlineKeyboardMarkup(rows)


def panel_notes_kb(bc_id: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(
        f"🗑 #{n['id']} {n['text'][:30]}", callback_data=f"dn:{n['id']}:{bc_id}")]
        for n in list_notes(bc_id)[:20]]
    rows.append([InlineKeyboardButton("🔙 Назад", callback_data=f"p:main:{bc_id}")])
    return InlineKeyboardMarkup(rows)


def panel_ban_kb(bc_id: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"❌ {w}", callback_data=f"db:{w}:{bc_id}")]
            for w in list_banwords(bc_id)[:20]]
    rows.append([InlineKeyboardButton("🔙 Назад", callback_data=f"p:main:{bc_id}")])
    return InlineKeyboardMarkup(rows)


def _settings_text(bc_id: str) -> str:
    s = get_settings(bc_id)
    qf = s.get("quiet_from") or 23
    qt = s.get("quiet_to") or 8
    cd = s.get("cooldown_sec") or 3600
    td = s.get("typing_delay_ms") or 1500
    return (
        h("⚙️", "Настройки")
        + "\n" + kv("Автоответ", "вкл" if s.get("autoreply_enabled") else "выкл")
        + "\n" + kv("Уведомления об удалённых", "вкл" if s.get("forward_deleted") else "выкл")
        + "\n" + kv("Тихие часы", "вкл" if s.get("quiet_enabled") else "выкл")
        + f"\n• Тишина: с {qf:02d}:00 до {qt:02d}:00"
        + "\n" + kv("Кулдаун автоответа", f"{cd//60} мин")
        + "\n" + kv("Задержка «печатает»", f"{td} мс")
    )


def _main_text(bc_id: str | None) -> str:
    if not bc_id or bc_id == "-":
        return h("🛡", BOT_NAME) + "\nСначала подключите бизнес-бота в Telegram."
    s = get_settings(bc_id)
    return (
        h("🛡", f"Панель {BOT_NAME}")
        + "\n" + kv("Business connection", bc_id[:16] + "…")
        + "\n" + kv("Автоответ", "вкл" if s.get("autoreply_enabled") else "выкл")
        + "\n" + kv("Тихие часы", "вкл" if s.get("quiet_enabled") else "выкл")
        + "\n" + kv("Заглушено чатов", str(len(list_muted_chats(bc_id))))
        + "\n\nВыберите раздел:"
    )


# ---------------------------------------------------------------------------
# Callback-хэндлер
# ---------------------------------------------------------------------------

async def on_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if q is None:
        return
    data = q.data or ""
    try:
        await q.answer()
    except TelegramError:
        pass

    parts = data.split(":")
    kind = parts[0]

    # --- Ответы на предложение (Да / Нет) ---
    if kind == "love_ask":
        answer = parts[1]
        if answer == "yes":
            await safe_edit(
                q,
                "💖 <b>Спасибо!</b> 💕💕💕",
                reply_markup=None
            )
        elif answer == "no":
            await safe_edit(
                q,
                "Ладно...",
                reply_markup=None
            )
        return

    if kind == "p":
        section = parts[1]
        bc_id = parts[2] if len(parts) > 2 else None
        if section == "main":
            await safe_edit(q, _main_text(None if bc_id in (None, "-") else bc_id),
                            panel_main_kb(bc_id))
        elif section == "settings":
            await safe_edit(q, _settings_text(bc_id), panel_settings_kb(bc_id))
        elif section == "muted":
            chats = list_muted_chats(bc_id)
            body = "\n".join("• " + code(c) for c in chats) or "—"
            await safe_edit(q, h("🚫", "Заглушенные чаты") + "\n" + body,
                            panel_muted_kb(bc_id))
        elif section == "reply":
            await safe_edit(q,
                h("✍️", "Автоответ") + "\n"
                "Меняется командой в бизнес-чате:\n"
                f"{code(CMD_SETREPLY + ' <текст>')}\n\n"
                "По умолчанию:\n" + quote(AUTOREPLY_TEXT),
                InlineKeyboardMarkup([[InlineKeyboardButton(
                    "🔙 Назад", callback_data=f"p:main:{bc_id}")]]))
        elif section == "notes":
            notes = list_notes(bc_id)
            body = "\n".join(f"• #{n['id']} {html.escape(n['text'][:60])}" for n in notes) or "—"
            await safe_edit(q,
                h("📝", "Заметки") + "\n" + body
                + f"\n\nДобавить: {code(CMD_NOTE_ADD + ' <текст>')}",
                panel_notes_kb(bc_id))
        elif section == "ban":
            ws = list_banwords(bc_id)
            body = ", ".join(code(w) for w in ws) if ws else "—"
            await safe_edit(q,
                h("🔞", "Банворды") + "\n" + body
                + f"\n\nДобавить: {code(CMD_BANWORD_ADD + ' <слово>')}",
                panel_ban_kb(bc_id))
        elif section == "stats":
            tin, tdel = total_stats(bc_id)
            top = get_stats(bc_id)
            body = "\n".join(
                f"• {code(r['chat_id'])}: {r['msgs_in']} вх / {r['msgs_deleted']} удал."
                for r in top) or "—"
            await safe_edit(q,
                h("📊", "Статистика") + "\n"
                + kv("Всего входящих", str(tin)) + "\n"
                + kv("Всего удалённых", str(tdel)) + "\n\n"
                + "<b>Топ чатов:</b>\n" + body,
                InlineKeyboardMarkup([[InlineKeyboardButton(
                    "🔙 Назад", callback_data=f"p:main:{bc_id}")]]))
        elif section == "games":
            await safe_edit(q, h("🎮", "Игры") + "\nВыберите игру:", panel_games_kb())
        elif section == "fx":
            await safe_edit(q, h("✨", "Эффекты") + "\nВыберите эффект:", panel_fx_kb())
        elif section == "anim":
            await safe_edit(q,
                h("⌨️", "Анимации") + "\n"
                "Эти команды пишутся в бизнес-чате вместе с текстом:\n\n"
                f"{code(CMD_TYPE + ' <текст>')} — печатает по буквам\n"
                f"{code(CMD_LOADING + ' <текст>')} — загрузка, потом текст\n"
                f"{code(CMD_GLITCH + ' <текст>')} — глитч, потом текст",
                panel_anim_kb())
        elif section == "help":
            await safe_edit(q,
                build_help_text(bc_id if bc_id != "-" else None),
                InlineKeyboardMarkup([[InlineKeyboardButton(
                    "🔙 Назад", callback_data=f"p:main:{bc_id}")]]))
        return

    if kind == "t":
        key, bc_id = parts[1], parts[2]
        s = get_settings(bc_id)
        if key == "autoreply_enabled":
            update_setting(bc_id, "autoreply_enabled", 0 if s.get("autoreply_enabled") else 1)
        elif key == "forward_deleted":
            update_setting(bc_id, "forward_deleted", 0 if s.get("forward_deleted") else 1)
        elif key == "quiet_enabled":
            update_setting(bc_id, "quiet_enabled", 0 if s.get("quiet_enabled") else 1)
        elif key == "typing":
            cur = s.get("typing_delay_ms") or 1500
            try:
                idx = TYPING_STEPS.index(cur)
                nxt = TYPING_STEPS[(idx + 1) % len(TYPING_STEPS)]
            except ValueError:
                nxt = TYPING_STEPS[0]
            update_setting(bc_id, "typing_delay_ms", nxt)
        await safe_edit(q, _settings_text(bc_id), panel_settings_kb(bc_id))
        return

    if kind == "q":
        which, bc_id = parts[1], parts[2]
        s = get_settings(bc_id)
        if which == "from":
            update_setting(bc_id, "quiet_from", ((s.get("quiet_from") or 23) + 1) % 24)
        else:
            update_setting(bc_id, "quiet_to", ((s.get("quiet_to") or 8) + 1) % 24)
        await safe_edit(q, _settings_text(bc_id), panel_settings_kb(bc_id))
        return

    if kind == "c":
        bc_id = parts[2]
        s = get_settings(bc_id)
        cur = s.get("cooldown_sec") or 3600
        try:
            idx = COOLDOWN_STEPS.index(cur)
            nxt = COOLDOWN_STEPS[(idx + 1) % len(COOLDOWN_STEPS)]
        except ValueError:
            nxt = COOLDOWN_STEPS[0]
        update_setting(bc_id, "cooldown_sec", nxt)
        await safe_edit(q, _settings_text(bc_id), panel_settings_kb(bc_id))
        return

    if kind == "u":
        cid, bc_id = int(parts[1]), parts[2]
        unmute_chat(bc_id, cid)
        chats = list_muted_chats(bc_id)
        body = "\n".join("• " + code(c) for c in chats) or "—"
        await safe_edit(q, h("🚫", "Заглушенные чаты") + "\n" + body, panel_muted_kb(bc_id))
        return

    if kind == "dn":
        nid, bc_id = int(parts[1]), parts[2]
        del_note(bc_id, nid)
        notes = list_notes(bc_id)
        body = "\n".join(f"• #{n['id']} {html.escape(n['text'][:60])}" for n in notes) or "—"
        await safe_edit(q, h("📝", "Заметки") + "\n" + body, panel_notes_kb(bc_id))
        return

    if kind == "db":
        w, bc_id = parts[1], parts[2]
        del_banword(bc_id, w)
        ws = list_banwords(bc_id)
        body = ", ".join(code(x) for x in ws) if ws else "—"
        await safe_edit(q, h("🔞", "Банворды") + "\n" + body, panel_ban_kb(bc_id))
        return

    if kind == "g":
        game_kind = parts[1]
        emoji = GAME_EMOJI.get(game_kind, "🎲")
        cmd = {
            "dice": CMD_GAME_DICE, "basket": CMD_GAME_BASKET,
            "darts": CMD_GAME_DARTS, "bowling": CMD_GAME_BOWLING,
            "football": CMD_GAME_FOOTBALL,
        }.get(game_kind, "")
        await safe_edit(q,
            h(emoji, f"Игра: {game_kind}") + "\n"
            f"Команда: {code(cmd)}\n\n"
            "Как играть:\n"
            "1. Отправьте команду в бизнес-чат.\n"
            "2. Появится сообщение с кнопкой «Готов».\n"
            "3. Нажмите двое разных людей.\n"
            "4. Первый игрок бросает, затем второй.\n"
            "5. У кого больше — тот победил.",
            InlineKeyboardMarkup([[InlineKeyboardButton(
                "🔙 Назад", callback_data="p:games")]]))
        return

    if kind == "fx":
        fx_name = parts[1]
        user_id = update.effective_user.id if update.effective_user else None
        if not user_id:
            return
        effect_id = FX.get(fx_name)
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"<b>{html.escape(fx_name)}</b>\n{SEP}\n"
                     f"Команда для чата: {code('.' + fx_name)}",
                parse_mode=ParseMode.HTML,
                message_effect_id=effect_id,
            )
        except TelegramError as e:
            log.warning("effect send failed (fallback): %s", e)
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"<b>{html.escape(fx_name)}</b>\n"
                         f"Команда: {code('.' + fx_name)}",
                    parse_mode=ParseMode.HTML,
                )
            except TelegramError as e2:
                log.error("effect fallback failed: %s", e2)
        return

    if kind == "anim":
        anim = parts[1]
        user_id = update.effective_user.id if update.effective_user else None
        if not user_id:
            return
        if anim == "type":
            await animate_type_text(context, None, user_id, "Привет! Это демонстрация анимации набора текста.")
        elif anim == "loading":
            await animate_loading(context, None, user_id, "✅ <b>Загрузка завершена!</b>\nЭто демонстрация.")
        elif anim == "glitch":
            await animate_glitch(context, None, user_id, "Глитч-эффект работает!")
        return

    if kind == "game":
        game_key = parts[2]
        g = games.get(game_key)
        if not g:
            await q.answer("Игра не найдена или устарела", alert=True)
            return
        user = q.from_user
        if user.id in g["players"]:
            await q.answer("Ты уже готов", alert=True)
            return
        g["players"].append(user.id)

        emoji = GAME_EMOJI[g["kind"]]
        names = ", ".join(f"user {uid}" for uid in g["players"])
        kb = None
        if len(g["players"]) < 2:
            kb = InlineKeyboardMarkup([[InlineKeyboardButton(
                "✅ Готов", callback_data=f"game:join:{game_key}")]])
        await safe_edit(q,
            h(emoji, f"Игра: {g['kind']}") + "\n"
            f"Готовы: <b>{len(g['players'])}/2</b>\n"
            f"{html.escape(names) if names else '—'}\n\n"
            + ("Ожидаем второго игрока…" if len(g["players"]) < 2 else "Оба готовы! Игра начинается…"),
            kb)
        if len(g["players"]) >= 2:
            context.application.create_task(_run_game(context, game_key))
        return


async def _run_game(context: ContextTypes.DEFAULT_TYPE, game_key: str) -> None:
    g = games.get(game_key)
    if not g:
        return
    emoji = GAME_EMOJI[g["kind"]]
    bc_id, chat_id = g["bc_id"], g["chat_id"]
    p1, p2 = g["players"][0], g["players"][1]

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=h(emoji, "Ход 1-го игрока") + f"\nИгрок {p1}, бросай!",
            parse_mode=ParseMode.HTML, business_connection_id=bc_id)
        d1 = await context.bot.send_dice(chat_id=chat_id, emoji=emoji,
                                         business_connection_id=bc_id)
        v1 = d1.dice.value
    except TelegramError as e:
        log.error("game p1: %s", e); return

    await asyncio.sleep(2)
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=h(emoji, "Ход 2-го игрока") + f"\nИгрок {p2}, бросай!",
            parse_mode=ParseMode.HTML, business_connection_id=bc_id)
        d2 = await context.bot.send_dice(chat_id=chat_id, emoji=emoji,
                                         business_connection_id=bc_id)
        v2 = d2.dice.value
    except TelegramError as e:
        log.error("game p2: %s", e); return

    await asyncio.sleep(2)
    if v1 == v2:
        result = "Ничья 🤝"
    elif v1 > v2:
        result = f"🏆 Победил игрок {p1}!"
    else:
        result = f"🏆 Победил игрок {p2}!"
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=h("🎉", "Итог") + f"\nИгрок 1: <b>{v1}</b>\nИгрок 2: <b>{v2}</b>\n\n{result}",
            parse_mode=ParseMode.HTML, business_connection_id=bc_id)
    except TelegramError as e:
        log.error("game result: %s", e)
    games.pop(game_key, None)


# ---------------------------------------------------------------------------
# Бизнес-апдейты
# ---------------------------------------------------------------------------

async def _safe_delete(context, bc_id: str, message_id: int) -> None:
    try:
        await context.bot.delete_business_messages(
            business_connection_id=bc_id, message_ids=[message_id])
    except (TelegramError, AttributeError) as e:
        log.warning("delete msg %s: %s", message_id, e)


async def _typing(context, bc_id: str | None, chat_id: int, delay_ms: int) -> None:
    try:
        await context.bot.send_chat_action(
            chat_id=chat_id, action=ChatAction.TYPING, business_connection_id=bc_id)
    except TelegramError:
        pass
    if delay_ms > 0:
        await asyncio.sleep(delay_ms / 1000.0)


def in_quiet_hours(s: dict) -> bool:
    if not s.get("quiet_enabled"):
        return False
    hnow = datetime.now(timezone.utc).hour
    qf = s.get("quiet_from") or 23
    qt = s.get("quiet_to") or 8
    if qf <= qt:
        return qf <= hnow < qt
    return hnow >= qf or hnow < qt


async def on_business_connection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bc = update.business_connection
    if bc is None:
        return
    upsert_connection(bc.id, bc.user.id)
    log.info("Business connection %s set up for owner %s", bc.id, bc.user.id)


async def on_business_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.business_message
    if msg is None:
        return
    bc_id = msg.business_connection_id
    chat_id = msg.chat_id
    text = msg.text or msg.caption or ""
    sender = msg.from_user

    owner_id = get_owner_id(bc_id)
    if owner_id is None:
        try:
            bc = await context.bot.get_business_connection(bc_id)
            upsert_connection(bc.id, bc.user.id)
            owner_id = bc.user.id
        except TelegramError as e:
            log.warning("resolve bc %s: %s", bc_id, e)

    remember_message(bc_id, chat_id, msg.message_id,
                     sender.id if sender else None,
                     _display_name(sender),
                     _describe_message(msg))
    bump_stat(bc_id, chat_id, "msgs_in")

    if sender and owner_id and sender.id == owner_id:
        await handle_owner_command(update, context, bc_id, chat_id, text)
        return

    if is_muted(bc_id, chat_id):
        return

    s = get_settings(bc_id)
    if not s.get("autoreply_enabled", 1):
        return
    if in_quiet_hours(s):
        return

    if is_away(bc_id):
        if should_send_autoreply(bc_id, chat_id, s.get("cooldown_sec") or 3600):
            reply = get_custom_reply(bc_id, chat_id) or AUTOREPLY_TEXT
            await _typing(context, bc_id, chat_id, s.get("typing_delay_ms") or 1500)
            try:
                await context.bot.send_message(
                    chat_id=chat_id, text=reply, business_connection_id=bc_id)
            except TelegramError as e:
                log.error("autoreply: %s", e)


# ---------------------------------------------------------------------------
# Обработка команд владельца
# ---------------------------------------------------------------------------

ALL_OWNER_CMDS = [
    CMD_AWAY, CMD_ONLINE, CMD_MUTE, CMD_UNMUTE, CMD_STATUS, CMD_HELP,
    CMD_MUTELIST, CMD_SETREPLY, CMD_AFK, CMD_BACK, CMD_REMIND,
    CMD_NOTE_ADD, CMD_NOTE_LIST, CMD_NOTE_DEL,
    CMD_BANWORD_ADD, CMD_BANWORD_LIST, CMD_BANWORD_DEL,
    CMD_QUIET_START, CMD_QUIET_STOP, CMD_STATS, CMD_PING, CMD_UPTIME, CMD_ID,
    CMD_ASKOUT, CMD_PROPOSAL, CMD_LOVEASK,
    CMD_GAME_DICE, CMD_GAME_BASKET, CMD_GAME_DARTS, CMD_GAME_BOWLING, CMD_GAME_FOOTBALL,
    CMD_LOVE, CMD_COMPLIMENT, CMD_QUOTE, CMD_FACT, CMD_TIP, CMD_ROAST,
    CMD_FX_FIRE, CMD_FX_CONFETTI, CMD_FX_HEART, CMD_FX_POO, CMD_FX_BOOM,
    CMD_FX_SPARKLES, CMD_FX_BALLOON, CMD_FX_PARTY, CMD_FX_THUMBSUP,
    CMD_FX_FIREWORKS, CMD_FX_LIGHTNING, CMD_FX_HUNDRED,
    CMD_TYPE, CMD_LOADING, CMD_GLITCH,
]


async def handle_owner_command(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               bc_id: str, chat_id: int, text: str) -> None:
    msg = update.business_message
    stripped = text.strip()
    lowered = stripped.lower()

    is_any_cmd = any(_is_cmd(lowered, c) for c in ALL_OWNER_CMDS)
    is_start_panel = lowered in ("/start", "/panel", ".start", ".panel")

    if not is_any_cmd and not is_start_panel:
        return

    async def reply(txt: str, effect_id: str | None = None, reply_markup=None) -> None:
        s = get_settings(bc_id)
        await _typing(context, bc_id, chat_id, min(s.get("typing_delay_ms") or 1500, 800))
        kwargs = dict(
            chat_id=chat_id, text=txt, parse_mode=ParseMode.HTML,
            business_connection_id=bc_id,
        )
        if effect_id:
            kwargs["message_effect_id"] = effect_id
        if reply_markup:
            kwargs["reply_markup"] = reply_markup
        try:
            await context.bot.send_message(**kwargs)
        except BadRequest as e:
            if "effect" in str(e).lower() or "message_effect" in str(e).lower():
                kwargs.pop("message_effect_id", None)
                try:
                    await context.bot.send_message(**kwargs)
                except TelegramError as e2:
                    log.error("reply fallback: %s", e2)
            else:
                log.error("reply to owner: %s", e)
        except TelegramError as e:
            log.error("reply to owner: %s", e)

    # ── /start, /panel ────────────────────────────────────────────────
    if is_start_panel:
        owner_id = get_owner_id(bc_id)
        sent_ok = False
        if owner_id:
            try:
                conns = list_connections_for_owner(owner_id)
                bc_first = conns[0] if conns else "-"
                await context.bot.send_message(
                    chat_id=owner_id,
                    text=_main_text(None if bc_first == "-" else bc_first),
                    parse_mode=ParseMode.HTML,
                    reply_markup=panel_main_kb(bc_first))
                sent_ok = True
            except TelegramError as e:
                log.error("send panel: %s", e)
        await _safe_delete(context, bc_id, msg.message_id)
        if sent_ok:
            await reply(h("📩", "Панель отправлена в личку бота"))
        else:
            await reply(h("⚠️", "Не удалось отправить панель")
                        + "\nНапишите /start боту в личку.")
        return

    # ── Команда предложения встречаться (.askout / .proposal / .loveask) ─────
    if any(_is_cmd(lowered, c) for c in (CMD_ASKOUT, CMD_PROPOSAL, CMD_LOVEASK)):
        await _safe_delete(context, bc_id, msg.message_id)
        
        proposal_text = (
            "✨ <b>Знаешь...</b> ✨\n"
            "━━━━━━━━━━━━━━━\n"
            "Знаешь, ты действительно очень важный и дорогой для меня человек, "
            "и я тебя очень сильно люблю... ❤️\n\n"
            "Ты не против стать моей девушкой и начать встречаться? 🥺👉👈"
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Да 💕", callback_data="love_ask:yes"),
                InlineKeyboardButton("Нет 💔", callback_data="love_ask:no")
            ]
        ])
        
        # Отправляем сообщение с эффектом сердечек
        await reply(proposal_text, effect_id=FX["heart"], reply_markup=keyboard)
        return

    # ── Анимации ──────────────────────────────────────────────────────
    if _is_cmd(lowered, CMD_TYPE):
        content = stripped[len(CMD_TYPE):].strip()
        if not content:
            await reply(h("⌨️", "Использование") + "\n" + code(CMD_TYPE + " <текст>")); return
        await _safe_delete(context, bc_id, msg.message_id)
        await animate_type_text(context, bc_id, chat_id, content)
        return

    if _is_cmd(lowered, CMD_LOADING):
        content = stripped[len(CMD_LOADING):].strip()
        if not content:
            await reply(h("⏳", "Использование") + "\n" + code(CMD_LOADING + " <текст>")); return
        await _safe_delete(context, bc_id, msg.message_id)
        await animate_loading(context, bc_id, chat_id, f"✅ <b>{html.escape(content)}</b>")
        return

    if _is_cmd(lowered, CMD_GLITCH):
        content = stripped[len(CMD_GLITCH):].strip()
        if not content:
            await reply(h("⚡", "Использование") + "\n" + code(CMD_GLITCH + " <текст>")); return
        await _safe_delete(context, bc_id, msg.message_id)
        await animate_glitch(context, bc_id, chat_id, content)
        return

    # ── Игры ───────────────────────────────────────────────────────────
    for cmd, kind in [
        (CMD_GAME_DICE, "dice"), (CMD_GAME_BASKET, "basket"),
        (CMD_GAME_DARTS, "darts"), (CMD_GAME_BOWLING, "bowling"),
        (CMD_GAME_FOOTBALL, "football"),
    ]:
        if _is_cmd(lowered, cmd):
            await _start_game(context, bc_id, chat_id, kind)
            await _safe_delete(context, bc_id, msg.message_id)
            return

    # ── Эффекты (текст + эффект, БЕЗ эмодзи в начале) ─────────────────
    for cmd_key, fx_name in [
        (CMD_FX_FIRE, "fire"), (CMD_FX_CONFETTI, "confetti"),
        (CMD_FX_HEART, "heart"), (CMD_FX_POO, "poo"),
        (CMD_FX_BOOM, "boom"), (CMD_FX_SPARKLES, "sparkles"),
        (CMD_FX_BALLOON, "balloon"), (CMD_FX_PARTY, "party"),
        (CMD_FX_THUMBSUP, "thumbsup"), (CMD_FX_FIREWORKS, "fireworks"),
        (CMD_FX_LIGHTNING, "lightning"), (CMD_FX_HUNDRED, "hundred"),
    ]:
        if _is_cmd(lowered, cmd_key):
            content = stripped[len(cmd_key):].strip()
            effect_id = FX[fx_name]
            text_out = html.escape(content) if content else f"<b>{html.escape(fx_name)}</b>"
            await reply(text_out, effect_id)
            await _safe_delete(context, bc_id, msg.message_id)
            return

    # ── Остальные команды ─────────────────────────────────────────────
    await _safe_delete(context, bc_id, msg.message_id)

    if _is_cmd(lowered, CMD_AWAY):
        set_away(bc_id, True); set_afk(bc_id, None)
        await reply(h("🔕", "Автоответчик включён") + "\nВы «не на связи»."); return
    if _is_cmd(lowered, CMD_ONLINE):
        set_away(bc_id, False); clear_afk(bc_id)
        await reply(h("🔔", "Автоответчик выключен") + "\nВы «на связи»."); return
    if _is_cmd(lowered, CMD_STATUS):
        s = get_settings(bc_id); afk = get_afk(bc_id)
        await reply(
            h("🛡", "Статус") + "\n"
            + kv("Автоответ", "вкл" if s.get("autoreply_enabled") else "выкл") + "\n"
            + kv("Away", "да" if is_away(bc_id) else "нет") + "\n"
            + kv("AFK", "да" if afk else "нет") + "\n"
            + kv("Тихие часы", "вкл" if s.get("quiet_enabled") else "выкл") + "\n"
            + kv("Этот чат заглушен", "да" if is_muted(bc_id, chat_id) else "нет") + "\n"
            + kv("ID чата", str(chat_id))); return
    if _is_cmd(lowered, CMD_MUTE):
        target = _arg_or(stripped, CMD_MUTE, chat_id)
        mute_chat(bc_id, target)
        await reply(h("🚫", "Заглушено") + "\n" + kv("Чат", str(target))); return
    if _is_cmd(lowered, CMD_UNMUTE):
        target = _arg_or(stripped, CMD_UNMUTE, chat_id)
        unmute_chat(bc_id, target)
        await reply(h("✅", "Заглушка снята") + "\n" + kv("Чат", str(target))); return
    if _is_cmd(lowered, CMD_MUTELIST):
        chats = list_muted_chats(bc_id)
        body = "\n".join("• " + code(c) for c in chats) or "—"
        await reply(h("🚫", "Заглушенные чаты") + "\n" + body); return
    if _is_cmd(lowered, CMD_SETREPLY):
        t = stripped[len(CMD_SETREPLY):].strip()
        if not t:
            await reply(h("✍️", "Использование") + "\n" + code(CMD_SETREPLY + " <текст>")); return
        set_custom_reply(bc_id, chat_id, t)
        await reply(h("✍️", "Автоответ обновлён") + "\n" + quote(t)); return
    if _is_cmd(lowered, CMD_HELP):
        await reply(build_help_text(bc_id)); return
    if _is_cmd(lowered, CMD_PING):
        await reply(h("🏓", "Pong") + "\nБот на связи."); return
    if _is_cmd(lowered, CMD_UPTIME):
        conn = db_connect()
        row = conn.execute(
            "SELECT created_at FROM connections WHERE business_connection_id = ?", (bc_id,)
        ).fetchone()
        conn.close()
        if row:
            await reply(h("⏱", "Uptime")
                        + f"\nРаботает с вами: <b>{_fmt_dur(int(time.time()-row['created_at']))}</b>")
        return
    if _is_cmd(lowered, CMD_ID):
        await reply(h("🆔", "ID") + "\n"
                    + kv("Текущий чат", str(chat_id)) + "\n"
                    + kv("Business connection", bc_id)); return
    if _is_cmd(lowered, CMD_AFK):
        reason = stripped[len(CMD_AFK):].strip() or None
        set_afk(bc_id, reason); set_away(bc_id, True)
        await reply(h("💤", "AFK") + ("\nПричина: " + quote(reason) if reason else "")); return
    if _is_cmd(lowered, CMD_BACK):
        clear_afk(bc_id); set_away(bc_id, False)
        await reply(h("↩️", "С возвращением") + "\nАвтоответчик выключен."); return
    if _is_cmd(lowered, CMD_REMIND):
        rest = stripped[len(CMD_REMIND):].strip()
        pp = rest.split(maxsplit=1)
        if len(pp) < 2 or not pp[0].isdigit():
            await reply(h("⏰", "Напоминание") + "\n" + code(".remind <сек> <текст>")); return
        secs = int(pp[0]); txt = pp[1]
        owner_id = get_owner_id(bc_id)
        if owner_id:
            rid = add_reminder(owner_id, txt, int(time.time()) + secs)
            await reply(h("⏰", "Напоминание создано")
                        + "\n" + kv("Через", f"{secs} сек") + "\n" + kv("ID", str(rid)))
        return
    if _is_cmd(lowered, CMD_NOTE_ADD):
        t = stripped[len(CMD_NOTE_ADD):].strip()
        if not t:
            await reply(h("📝", "Заметки") + "\n" + code(".note <текст>")); return
        nid = add_note(bc_id, t)
        await reply(h("📝", "Заметка добавлена") + "\n" + kv("ID", str(nid))); return
    if _is_cmd(lowered, CMD_NOTE_LIST):
        notes = list_notes(bc_id)
        body = "\n".join(f"• #{n['id']} {html.escape(n['text'][:80])}" for n in notes) or "—"
        await reply(h("📝", "Заметки") + "\n" + body); return
    if _is_cmd(lowered, CMD_NOTE_DEL):
        rest = stripped[len(CMD_NOTE_DEL):].strip()
        if not rest.isdigit():
            await reply(h("📝", "Использование") + "\n" + code(".delnote <id>")); return
        ok = del_note(bc_id, int(rest))
        await reply(h("📝", "Заметка " + ("удалена" if ok else "не найдена"))); return
    if _is_cmd(lowered, CMD_BANWORD_DEL):
        w = stripped[len(CMD_BANWORD_DEL):].strip()
        if not w:
            await reply(h("🔞", "Банворды") + "\n" + code(".unbanword <слово>")); return
        ok = del_banword(bc_id, w)
        await reply(h("🔞", "Слово " + ("удалено" if ok else "не найдено"))); return
    if _is_cmd(lowered, CMD_BANWORD_ADD):
        w = stripped[len(CMD_BANWORD_ADD):].strip()
        if not w:
            await reply(h("🔞", "Банворды") + "\n" + code(".banword <слово>")); return
        add_banword(bc_id, w)
        await reply(h("🔞", "Слово добавлено в бан") + "\n" + quote(w)); return
    if _is_cmd(lowered, CMD_BANWORD_LIST):
        ws = list_banwords(bc_id)
        body = ", ".join(code(w) for w in ws) if ws else "—"
        await reply(h("🔞", "Банворды") + "\n" + body); return
    if _is_cmd(lowered, CMD_QUIET_START):
        update_setting(bc_id, "quiet_enabled", 1)
        s = get_settings(bc_id)
        qf = s.get("quiet_from") or 23
        qt = s.get("quiet_to") or 8
        await reply(h("🌙", "Тихие часы включены")
                    + f"\nС {qf:02d}:00 до {qt:02d}:00 UTC"); return
    if _is_cmd(lowered, CMD_QUIET_STOP):
        update_setting(bc_id, "quiet_enabled", 0)
        await reply(h("☀️", "Тихие часы выключены")); return
    if _is_cmd(lowered, CMD_STATS):
        tin, tdel = total_stats(bc_id)
        await reply(h("📊", "Статистика") + "\n"
                    + kv("Входящих", str(tin)) + "\n" + kv("Удалённых", str(tdel))); return

    # ── Весёлые ──────────────────────────────────────────────────────
    if _is_cmd(lowered, CMD_LOVE):
        await reply(h("💙", "Напоминание") + "\n" + quote(random.choice(LOVE_PHRASES))); return
    if _is_cmd(lowered, CMD_COMPLIMENT):
        await reply(h("💙", "Комплимент") + "\n" + quote(random.choice(COMPLIMENTS))); return
    if _is_cmd(lowered, CMD_QUOTE):
        await reply(h("📜", "Цитата") + "\n" + quote(random.choice(QUOTES))); return
    if _is_cmd(lowered, CMD_FACT):
        await reply(h("🧠", "Факт") + "\n" + quote(random.choice(FACTS))); return
    if _is_cmd(lowered, CMD_TIP):
        await reply(h("💡", "Совет") + "\n" + quote(random.choice(TIPS))); return
    if _is_cmd(lowered, CMD_ROAST):
        await reply(h("🔥", "Роаст") + "\n" + quote(random.choice(ROASTS))); return


async def _start_game(context: ContextTypes.DEFAULT_TYPE, bc_id: str, chat_id: int, kind: str):
    cleanup_old_games()
    game_key = new_game(bc_id, chat_id, kind)
    emoji = GAME_EMOJI[kind]
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=h(emoji, f"Игра: {kind}") + "\n"
                 "Нажмите «Готов», чтобы участвовать.\n"
                 "Нужно двое разных людей.\n\n"
                 "Готовы: <b>0/2</b>",
            parse_mode=ParseMode.HTML,
            business_connection_id=bc_id,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                "✅ Готов", callback_data=f"game:join:{game_key}")]]))
    except TelegramError as e:
        log.error("start game: %s", e)


async def on_deleted_business_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    deleted = update.deleted_business_messages
    if deleted is None:
        return
    bc_id = deleted.business_connection_id
    chat_id = deleted.chat.id
    owner_id = get_owner_id(bc_id)
    if owner_id is None:
        try:
            bc = await context.bot.get_business_connection(bc_id)
            upsert_connection(bc.id, bc.user.id)
            owner_id = bc.user.id
        except TelegramError as e:
            log.warning("resolve bc %s: %s", bc_id, e)
            return

    bump_stat(bc_id, chat_id, "msgs_deleted")

    s = get_settings(bc_id)
    if not s.get("forward_deleted", 1):
        return
    if is_muted(bc_id, chat_id):
        return

    lines = [h("🗑", "Сообщение удалено"), f"Чат: {code(chat_id)}"]
    for mid in deleted.message_ids:
        row = get_remembered_message(bc_id, chat_id, mid)
        if row and row["text"]:
            who = row["from_name"] or "неизвестно"
            lines.append(f"\n👤 <b>{html.escape(who)}</b>\n{quote(row['text'])}")
        else:
            lines.append(
                f"\n• Сообщение {code(mid)} — <i>текст недоступен "
                f"(отправлено до запуска бота или не сохранилось)</i>")
    try:
        await context.bot.send_message(
            chat_id=owner_id, text="\n".join(lines), parse_mode=ParseMode.HTML)
    except TelegramError as e:
        log.error("notify owner: %s", e)


def _display_name(user) -> str:
    if user is None:
        return "неизвестный"
    if user.username:
        return f"@{user.username}"
    full = " ".join(filter(None, [user.first_name, user.last_name]))
    return full or str(user.id)


# ---------------------------------------------------------------------------
# .help
# ---------------------------------------------------------------------------

def build_help_text(bc_id: str | None) -> str:
    return (
        h("🛡", f"Команды {BOT_NAME}") + "\n"
        "<i>Все команды пишутся в бизнес-чате и автоматически удаляются после обработки.</i>\n\n"

        "<b>❤️ Признание</b>\n"
        f"• {code(CMD_ASKOUT)} (или {code(CMD_PROPOSAL)}) — красивое признание в любви с кнопками «Да/Нет»\n\n"

        "<b>🔹 Основные</b>\n"
        f"• {code(CMD_AWAY)} — включить автоответчик («не на связи»)\n"
        f"• {code(CMD_ONLINE)} — выключить автоответчик («на связи»)\n"
        f"• {code(CMD_STATUS)} — показать текущий статус бота\n"
        f"• {code(CMD_HELP)} — это сообщение\n\n"

        "<b>🔹 Управление чатами</b>\n"
        f"• {code(CMD_MUTE + ' [id]')} — заглушить чат (без id — текущий)\n"
        f"• {code(CMD_UNMUTE + ' [id]')} — снять заглушку\n"
        f"• {code(CMD_MUTELIST)} — список заглушенных чатов\n"
        f"• {code(CMD_SETREPLY + ' <текст>')} — свой текст автоответа для этого чата\n\n"

        "<b>🔹 AFK и напоминания</b>\n"
        f"• {code(CMD_AFK + ' [причина]')} — уйти в AFK (включает автоответ)\n"
        f"• {code(CMD_BACK)} — вернуться из AFK\n"
        f"• {code(CMD_REMIND + ' <сек> <текст>')} — напоминание в личку бота\n"
        f"  <i>Пример: {code(CMD_REMIND + ' 300 Позвонить маме')}</i>\n\n"

        "<b>🔹 Заметки</b>\n"
        f"• {code(CMD_NOTE_ADD + ' <текст>')} — сохранить заметку\n"
        f"• {code(CMD_NOTE_LIST)} — список заметок\n"
        f"• {code(CMD_NOTE_DEL + ' <id>')} — удалить заметку по ID\n\n"

        "<b>🔹 Банворды</b>\n"
        f"• {code(CMD_BANWORD_ADD + ' <слово>')} — добавить слово в бан\n"
        f"• {code(CMD_BANWORD_LIST)} — список банвордов\n"
        f"• {code(CMD_BANWORD_DEL + ' <слово>')} — удалить из банвордов\n\n"

        "<b>🔹 Тихие часы и статистика</b>\n"
        f"• {code(CMD_QUIET_START)} — включить тихие часы (автоответ молчит)\n"
        f"• {code(CMD_QUIET_STOP)} — выключить тихие часы\n"
        f"• {code(CMD_STATS)} — статистика входящих/удалённых\n"
        f"• {code(CMD_PING)} — проверить, жив ли бот\n"
        f"• {code(CMD_UPTIME)} — сколько бот работает с вами\n"
        f"• {code(CMD_ID)} — показать ID текущего чата\n\n"

        "<b>💙 Весёлые</b>\n"
        f"• {code(CMD_LOVE)} — случайное милое сообщение\n"
        f"• {code(CMD_COMPLIMENT)} — комплимент\n"
        f"• {code(CMD_QUOTE)} — цитата\n"
        f"• {code(CMD_FACT)} — интересный факт\n"
        f"• {code(CMD_TIP)} — полезный совет\n"
        f"• {code(CMD_ROAST)} — дружеский роаст\n\n"

        "<b>✨ Эффекты (анимация появления)</b>\n"
        "<i>Можно добавить текст после команды — он придёт вместе с эффектом. "
        "Смайлика в начале не будет, только ваш текст.</i>\n"
        f"• {code(CMD_FX_FIRE + ' [текст]')} — огонь\n"
        f"• {code(CMD_FX_CONFETTI + ' [текст]')} — конфетти\n"
        f"• {code(CMD_FX_HEART + ' [текст]')} — сердечки\n"
        f"• {code(CMD_FX_BOOM + ' [текст]')} — взрыв\n"
        f"• {code(CMD_FX_SPARKLES + ' [текст]')} — искры\n"
        f"• {code(CMD_FX_BALLOON + ' [текст]')} — шарики\n"
        f"• {code(CMD_FX_PARTY + ' [текст]')} — вечеринка\n"
        f"• {code(CMD_FX_FIREWORKS + ' [текст]')} — фейерверк\n"
        f"• {code(CMD_FX_LIGHTNING + ' [текст]')} — молния\n"
        f"• {code(CMD_FX_HUNDRED + ' [текст]')} — сотка\n"
        f"• {code(CMD_FX_POO + ' [текст]')} — какашка\n"
        f"• {code(CMD_FX_THUMBSUP + ' [текст]')} — палец вверх\n\n"

        "<b>⌨️ Анимации «набора»</b>\n"
        f"• {code(CMD_TYPE + ' <текст>')} — печатает текст по буквам\n"
        f"• {code(CMD_LOADING + ' <текст>')} — показывает загрузку, потом текст\n"
        f"• {code(CMD_GLITCH + ' <текст>')} — глитч-эффект, потом текст\n\n"

        "<b>🎮 Игры на двоих</b>\n"
        f"• {code(CMD_GAME_DICE)} — кубик\n"
        f"• {code(CMD_GAME_BASKET)} — баскетбол\n"
        f"• {code(CMD_GAME_DARTS)} — дартс\n"
        f"• {code(CMD_GAME_BOWLING)} — боулинг\n"
        f"• {code(CMD_GAME_FOOTBALL)} — футбол\n"
        "<i>Нажмите «Готов» двум разным людям — потом оба «бросают».</i>"
    )


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conns = list_connections_for_owner(user_id)
    bc_id = conns[0] if conns else "-"
    await update.message.reply_text(
        _main_text(None if bc_id == "-" else bc_id),
        parse_mode=ParseMode.HTML,
        reply_markup=panel_main_kb(bc_id))


async def panel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    conns = list_connections_for_owner(user_id)
    bc_id = conns[0] if conns else "-"
    await update.message.reply_text(
        _main_text(None if bc_id == "-" else bc_id),
        parse_mode=ParseMode.HTML,
        reply_markup=panel_main_kb(bc_id))


async def reminder_loop(context: ContextTypes.DEFAULT_TYPE) -> None:
    for r in pop_due_reminders(int(time.time())):
        try:
            await context.bot.send_message(
                chat_id=r["owner_user_id"],
                text=h("⏰", "Напоминание") + "\n" + quote(r["text"]),
                parse_mode=ParseMode.HTML)
        except TelegramError as e:
            log.error("reminder send: %s", e)


async def router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if update.message and update.message.text and update.message.text.startswith("/"):
            return
    except AttributeError:
        pass
    if update.business_connection is not None:
        await on_business_connection(update, context)
    elif update.business_message is not None:
        await on_business_message(update, context)
    elif update.deleted_business_messages is not None:
        await on_deleted_business_messages(update, context)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Exception while handling update:", exc_info=context.error)
    try:
        if isinstance(update, Update) and update.callback_query:
            await update.callback_query.answer()
    except Exception:
        pass


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Установите BOT_TOKEN.")
    db_init()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("panel", panel_cmd))
    app.add_handler(CallbackQueryHandler(on_panel_callback))
    app.add_handler(TypeHandler(Update, router))
    app.add_error_handler(error_handler)

    allowed = [
        "message", "edited_message", "callback_query",
        "business_connection", "business_message",
        "edited_business_message", "deleted_business_messages",
    ]

    if app.job_queue:
        app.job_queue.run_repeating(reminder_loop, interval=30, first=10)

    log.info("%s (%s) запущен", BOT_NAME, BOT_USERNAME)
    app.run_polling(allowed_updates=allowed, close_loop=False)


if __name__ == "__main__":
    main()
