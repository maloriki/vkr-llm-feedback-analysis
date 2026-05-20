"""
Telegram-бот для ИАС анализа обратной связи.

Демонстрирует работу LLM-конвейера: отзывы клиентов + чаты курьеров
через Qwen 2.5 7B (Ollama).

Запуск:
    export BOT_TOKEN=...
    python telegram_bot.py
"""
import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

TOKEN = os.environ["BOT_TOKEN"]
OLLAMA = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher(storage=MemoryStorage())


# --- данные ---
# хранятся в памяти: для демо этого достаточно
data = {}
chat_buffer: dict = {}             # chat_id -> [{text, sender, date}, ...]
chat_meta: dict = {}               # chat_id -> {title, type, last_seen}
selected_chat: dict = {}           # user_id -> chat_id (для анализа из лички)
BUFFER_LIMIT = 200


def _find_file(*candidates):
    """Ищем файл в нескольких возможных местах: рядом со скриптом или в cwd."""
    base = os.path.dirname(os.path.abspath(__file__))
    for c in candidates:
        p = os.path.join(base, c)
        if os.path.exists(p):
            return p
        if os.path.exists(c):
            return c
    return None


def load_data():
    """Загружаем результаты экспериментов и тестовую выборку.
    Структура репо: bot/ и research/ на одном уровне."""
    test_path = _find_file(
        "../research/data/test_set_500.csv",
        "test_set_500.csv",
    )
    data["test"] = pd.read_csv(test_path) if test_path else None

    preds_path = _find_file(
        "../research/results/predictions_qwen2.5_7b.csv",
        "predictions_qwen2.5_7b.csv",
    )
    data["preds"] = pd.read_csv(preds_path) if preds_path else None

    data["results"] = {}
    base = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [
        os.path.join(base, "..", "research", "results"),
        base,
        ".",
    ]
    seen = set()
    for sd in search_dirs:
        if not os.path.isdir(sd):
            continue
        for fname in os.listdir(sd):
            if fname.startswith("results_") and fname.endswith(".json") and fname not in seen:
                seen.add(fname)
                try:
                    with open(os.path.join(sd, fname), encoding="utf-8") as f:
                        obj = json.load(f)
                        data["results"][obj.get("model", fname)] = obj
                except Exception:
                    pass

    report_path = _find_file(
        "../research/analytical_report_demo.md",
        "analytical_report_demo.md",
    )
    if report_path:
        with open(report_path, encoding="utf-8") as f:
            data["report"] = f.read()
    else:
        data["report"] = None


# --- FSM для ввода произвольных дат ---
class DateRange(StatesGroup):
    start = State()
    end = State()


# --- клавиатура выбора периода ---
def period_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 1 день", callback_data="p:1d"),
            InlineKeyboardButton(text="📅 3 дня", callback_data="p:3d"),
        ],
        [
            InlineKeyboardButton(text="📅 Неделя", callback_data="p:7d"),
            InlineKeyboardButton(text="📅 Месяц", callback_data="p:30d"),
        ],
        [
            InlineKeyboardButton(text="📊 Всё", callback_data="p:all"),
            InlineKeyboardButton(text="🗓 Свои даты", callback_data="p:custom"),
        ],
    ])


PERIOD_HOURS = {"1d": 24, "3d": 72, "7d": 168, "30d": 720, "all": None}
PERIOD_LABELS = {
    "1d": "за последние 24 часа",
    "3d": "за последние 3 дня",
    "7d": "за последнюю неделю",
    "30d": "за последний месяц",
    "all": "за всё время",
}


def filter_messages(messages: list, *, hours: int = None,
                    date_from=None, date_to=None) -> list:
    """Фильтрует сообщения по интервалу.

    Можно передать либо hours (отступ назад от текущего времени),
    либо пару date_from/date_to (объекты datetime).
    """
    if hours is None and date_from is None:
        return messages

    out = []
    if hours is not None:
        cutoff = datetime.now() - timedelta(hours=hours)
        for m in messages:
            try:
                dt = datetime.strptime(m["date"], "%Y-%m-%d %H:%M")
            except Exception:
                out.append(m)
                continue
            if dt >= cutoff:
                out.append(m)
        return out

    # кастомный диапазон
    for m in messages:
        try:
            dt = datetime.strptime(m["date"], "%Y-%m-%d %H:%M")
        except Exception:
            continue
        if date_from <= dt <= date_to:
            out.append(m)
    return out


def parse_user_date(text: str, end_of_day: bool = False):
    """Парсит дату в одном из распространённых форматов."""
    text = text.strip()
    formats = [
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
        "%d.%m.%y",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            if end_of_day and " " not in text:
                dt = dt.replace(hour=23, minute=59)
            return dt
        except ValueError:
            continue
    return None


# --- LLM ---
def ask_llm(prompt: str, system: str, *,
            max_tokens: int = 200, timeout: int = 120) -> str:
    """Простой вызов Ollama, возвращает сырой ответ."""
    r = requests.post(OLLAMA, json={
        "model": MODEL,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": max_tokens},
    }, timeout=timeout)
    return r.json().get("response", "")


REVIEW_SYSTEM = (
    "Ты — аналитик клиентской обратной связи.\n"
    "Определи: sentiment (positive/negative/neutral), topic (1-3 слова), "
    "reason (1 предложение).\n"
    "ВАЖНО: все поля на русском языке.\n"
    'Формат ответа — строго JSON: {"sentiment":"...","topic":"...","reason":"..."}'
)


def classify_review(text: str) -> dict:
    """Классифицирует один отзыв и парсит JSON-ответ."""
    raw = ask_llm(f'Отзыв: "{text[:300]}"', REVIEW_SYSTEM)
    # иногда LLM оборачивает в ```json
    if "```" in raw:
        raw = raw.split("```", 2)[1].lstrip("json\n")
    s = raw.find("{")
    e = raw.rfind("}") + 1
    if s < 0 or e <= s:
        return {"error": "no_json"}
    try:
        p = json.loads(raw[s:e])
    except json.JSONDecodeError:
        return {"error": "bad_json"}
    # приводим тональность к латинским меткам
    sentiment = p.get("sentiment", "").lower().strip()
    mapping = {
        "позитивный": "positive", "положительный": "positive",
        "негативный": "negative", "отрицательный": "negative",
        "нейтральный": "neutral",
    }
    sentiment = mapping.get(sentiment, sentiment)
    return {
        "sentiment": sentiment,
        "topic": p.get("topic", ""),
        "reason": p.get("reason", ""),
    }


EMOJI = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}


# --- вспомогательное: отправка длинных сообщений ---
async def send_long(target, text: str):
    """Разбивает длинный текст на части <=4000 символов."""
    while text:
        if len(text) <= 4000:
            await target.answer(text, parse_mode=None)
            break
        split = text.rfind("\n", 0, 3900)
        if split < 2000:
            split = 3900
        await target.answer(text[:split], parse_mode=None)
        text = text[split:].lstrip()


# ============================================================
#  Команды в личке: демо на датасете RuReviews
# ============================================================

@dp.message(CommandStart())
async def start_cmd(msg: Message):
    await msg.answer(
        "👋 *ИАС анализа обратной связи*\n\n"
        "ВКР | НИУ ВШЭ, Высшая школа бизнеса, 2026\n"
        "Модель: Qwen 2.5 7B (Ollama, self-hosted)\n\n"
        "*🆕 Просто отправьте боту:*\n"
        "• любой *текст* — LLM сделает аналитический разбор\n"
        "• *файл* CSV / XLSX / TXT / JSON — пакетный анализ содержимого\n\n"
        "*В личке:*\n"
        "/analyze — живой анализ 5 отзывов из RuReviews\n"
        "/report — аналитический отчёт на 20 отзывах\n"
        "/stats — статистика тестовой выборки\n"
        "/alerts — критические негативные темы\n"
        "/compare — сравнение 6 моделей\n"
        "/chats — выбрать чат из подключённых\n\n"
        "*В группе (бот-админ):*\n"
        "/chat\\_analyze — анализ переписки с выбором периода\n"
        "/chat\\_stats — статистика собранных сообщений"
    )


@dp.message(Command("help"))
async def help_cmd(msg: Message):
    await msg.answer(
        "*Как это работает*\n\n"
        "1. В личке бот работает с готовым датасетом RuReviews "
        "(500 клиентских отзывов) — показывает результаты эксперимента.\n\n"
        "2. В группе бот собирает сообщения (нужны права администратора) "
        "и анализирует их через LLM по запросу.\n\n"
        "Подробнее — /start"
    )


@dp.message(Command("analyze"))
async def analyze_cmd(msg: Message):
    if data.get("test") is None:
        await msg.answer("⚠️ Тестовая выборка не загружена.")
        return

    await msg.answer(
        "🔍 *Запускаю LLM*\n"
        f"Модель: `{MODEL}`\n"
        "Пакет: 5 случайных отзывов\n\n"
        "⏳ Жду ответа..."
    )

    sample = data["test"].sample(5, random_state=int(time.time()) % 100)
    t0 = time.time()
    results = []
    for _, row in sample.iterrows():
        r = classify_review(row["review"])
        r["review"] = row["review"]
        r["true"] = row["sentiment"]
        results.append(r)
    dt = time.time() - t0

    lines = [f"✅ Готово за {dt:.1f} с ({dt/5:.1f} с на отзыв)\n"]
    for i, r in enumerate(results, 1):
        pred = r.get("sentiment", "?")
        ok = "✓" if pred == r["true"] else "✗"
        text = r["review"][:100].replace("*", "").replace("_", "")
        lines.append(
            f"*{i}.* {EMOJI.get(pred, '❓')} _{pred}_ {ok} "
            f"(истина: {r['true']})\n"
            f"  💬 «{text}...»\n"
            f"  🏷 {r.get('topic', '—')}\n"
            f"  💡 {r.get('reason', '—')[:110]}\n"
        )
    correct = sum(1 for r in results if r.get("sentiment") == r["true"])
    lines.append(f"\n📊 Точность: {correct}/5 ({correct*20}%)")

    out = "\n".join(lines)
    await msg.answer(out[:4000])


@dp.message(Command("report"))
async def report_cmd(msg: Message):
    if not data.get("report"):
        await msg.answer("⚠️ Отчёт не найден.")
        return

    await msg.answer(
        "📄 *Аналитический отчёт*\n"
        "Источник: 20 клиентских отзывов\n"
        f"Модель: `{MODEL}` | фаза: MAP"
    )
    # экранируем markdown-спецсимволы чтобы не сломать форматирование
    text = data["report"].replace("_", "\\_").replace("[", "\\[").replace("]", "\\]")
    await send_long(msg, text)


@dp.message(Command("stats"))
async def stats_cmd(msg: Message):
    if data.get("test") is None:
        await msg.answer("⚠️ Данные не загружены.")
        return
    df = data["test"]
    dist = df["sentiment"].value_counts()
    await msg.answer(
        "📊 *Тестовая выборка*\n\n"
        f"Всего: {len(df)} отзывов\n"
        f"Датасет: RuReviews (Smetanin, 2019)\n\n"
        f"🟢 positive: {dist.get('positive', 0)}\n"
        f"🔴 negative: {dist.get('negative', 0)}\n"
        f"⚪ neutral: {dist.get('neutral', 0)}\n\n"
        f"Средняя длина: {df['review'].str.len().mean():.0f} симв."
    )


@dp.message(Command("alerts"))
async def alerts_cmd(msg: Message):
    if data.get("preds") is None:
        await msg.answer("⚠️ Данные предсказаний не загружены.")
        return
    df = data["preds"]
    pred_col = [c for c in df.columns if "_pred" in c][0]
    topic_col = [c for c in df.columns if "_topic" in c][0]
    reason_col = [c for c in df.columns if "_reason" in c][0]

    neg = df[df[pred_col] == "negative"]
    top = neg[topic_col].value_counts().head(5)

    lines = [
        "🚨 *Критические алерты*\n",
        f"Негативных отзывов: {len(neg)} из {len(df)} "
        f"({len(neg)/len(df)*100:.0f}%)\n",
        "*Топ-5 негативных тем:*",
    ]
    for topic, cnt in top.items():
        if not topic or str(topic) == "nan":
            continue
        t = str(topic).replace("*", "").replace("_", "")[:50]
        icon = "🔴🔴🔴" if cnt > 10 else "🔴🔴" if cnt > 5 else "🔴"
        lines.append(f"{icon} *{t}* — {cnt}")

    if len(neg) > 0:
        ex = neg.iloc[0]
        lines.append(
            f"\n*Пример:*\n_«{ex['review'][:150]}...»_\n"
            f"🏷 {ex[topic_col]}\n💡 {ex[reason_col][:150]}"
        )
    lines.append("\n⏰ *Рекомендация:* разобрать топ-1 в течение 24 ч.")
    await msg.answer("\n".join(lines))


@dp.message(Command("compare"))
async def compare_cmd(msg: Message):
    if not data.get("results"):
        await msg.answer("⚠️ Результаты не найдены.")
        return

    order = [
        ("TF-IDF + XGBoost", "TF-IDF + XGBoost"),
        ("YandexGPT Pro", "YandexGPT Pro"),
        ("YandexGPT Embeddings + LogReg", "YandexGPT Emb+LogReg"),
        ("qwen2.5:7b", "Qwen 2.5 7B"),
        ("deepseek-llm:7b", "DeepSeek LLM 7B"),
        ("deepseek-r1:7b", "DeepSeek R1 7B"),
    ]
    lines = ["🏆 *Сравнение моделей*\n", "```",
             f"{'Модель':<26}{'Acc':>6}{'F1':>6}", "─" * 38]
    for key, title in order:
        if key in data["results"]:
            d = data["results"][key]
            lines.append(f"{title:<26}{d.get('accuracy',0):>6.3f}{d.get('macro_f1',0):>6.3f}")
    lines.append("```\n")
    lines.append(
        "TF-IDF лидирует (обучен на 89K), но LLM генерируют "
        "*инсайты* с рекомендациями — что baseline не умеет."
    )
    await msg.answer("\n".join(lines))


# ============================================================
#  Групповой чат: сбор и анализ сообщений
# ============================================================

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def on_group_message(msg: Message):
    # команды обрабатываем отдельно
    if msg.text and msg.text.startswith("/"):
        cmd = msg.text.split()[0].split("@")[0]
        if cmd == "/chat_analyze":
            await prompt_period(msg)
        elif cmd == "/chat_stats":
            await chat_stats(msg)
        return

    if not msg.text or len(msg.text.strip()) < 3:
        return

    chat_id = msg.chat.id
    buf = chat_buffer.setdefault(chat_id, [])
    buf.append({
        "text": msg.text,
        "sender": msg.from_user.full_name if msg.from_user else "—",
        "date": msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else "",
    })
    if len(buf) > BUFFER_LIMIT:
        del buf[:-BUFFER_LIMIT]

    # Запоминаем мета чата для команды /chats
    chat_meta[chat_id] = {
        "title": msg.chat.title or msg.chat.full_name or f"chat#{chat_id}",
        "type": msg.chat.type,
        "last_seen": msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else "",
    }


async def prompt_period(msg: Message):
    chat_id = msg.chat.id
    n = len(chat_buffer.get(chat_id, []))
    if n == 0:
        await msg.answer(
            "📭 В этом чате пока нет сообщений.\n"
            "Напишите что-нибудь и попробуйте снова.\n"
            "(боту нужны права администратора)"
        )
        return

    await msg.answer(
        f"🗓 *Выберите период*\nСобрано сообщений: {n}",
        reply_markup=period_kb()
    )


async def chat_stats(msg: Message):
    chat_id = msg.chat.id
    buf = chat_buffer.get(chat_id, [])
    if not buf:
        await msg.answer(
            "📭 Сообщений ещё нет.\n"
            "Добавьте бота в админы и напишите пару сообщений."
        )
        return

    senders = {}
    for m in buf:
        senders[m["sender"]] = senders.get(m["sender"], 0) + 1
    top = sorted(senders.items(), key=lambda x: -x[1])[:5]

    text = (
        f"📊 *Статистика чата*\n\n"
        f"Сообщений: {len(buf)}\n"
        f"Авторов: {len(senders)}\n"
        f"Первое: {buf[0]['date']}\n"
        f"Последнее: {buf[-1]['date']}\n\n"
        "*Активные участники:*\n"
    )
    for s, c in top:
        name = s.replace("*", "").replace("_", "")[:30]
        text += f"• {name}: {c}\n"

    text += "\n*По периодам:*\n"
    for key in ("1d", "3d", "7d", "30d"):
        cnt = len(filter_messages(buf, hours=PERIOD_HOURS[key]))
        text += f"• {PERIOD_LABELS[key]}: {cnt}\n"

    text += "\n💡 /chat\\_analyze — запустить анализ."
    await msg.answer(text)


async def analyze_messages(target, messages: list, period_label: str):
    """Общий код анализа списка сообщений."""
    if len(messages) < 3:
        await target.answer(
            f"⚠️ В периоде всего {len(messages)} сообщений "
            "(нужно минимум 3). Возьмите период побольше."
        )
        return

    # ограничиваем 20 последними — чтобы не перегружать контекст
    sample = messages[-20:] if len(messages) > 20 else messages

    await target.answer(
        f"🔍 Анализ: {period_label}\n"
        f"Сообщений в периоде: {len(messages)}, "
        f"обработаю последние: {len(sample)}\n"
        "⏳ ..."
    )

    chat_text = "\n".join(
        f'[{m["date"]}] {m["sender"]}: {m["text"][:200]}'
        for m in sample
    )

    system = (
        "Ты — аналитик переписки в рабочем чате. Выдели:\n"
        "1) Основные темы обсуждения с частотой\n"
        "2) Общее настроение группы\n"
        "3) Проблемы и жалобы — с цитатами\n"
        "4) Рекомендации для руководства\n\n"
        "Отвечай ТОЛЬКО на русском."
    )

    t0 = time.time()
    try:
        raw = ask_llm(
            f"Пакет из {len(sample)} сообщений ({period_label}):\n\n{chat_text}",
            system,
            max_tokens=1500,
            timeout=240,
        )
    except Exception as e:
        await target.answer(f"⚠️ Ошибка LLM: {e}")
        return
    dt = time.time() - t0

    header = (
        f"✅ Готово за {dt:.1f} с\n"
        f"Период: {period_label}\n"
        f"Обработано: {len(sample)}\n"
        f"─────────────────"
    )
    await target.answer(header)

    body = raw.replace("_", "\\_").replace("[", "\\[").replace("]", "\\]")
    await send_long(target, body)


# --- обработка нажатий кнопок периода ---
@dp.callback_query(F.data.startswith("p:"))
async def on_period(cb: CallbackQuery, state: FSMContext):
    period = cb.data.split(":", 1)[1]

    if period == "custom":
        await cb.answer()
        try:
            await cb.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        # В личке источник — выбранный чат, в группе — сам чат
        src_id = (selected_chat.get(cb.from_user.id)
                  if cb.message.chat.type == "private"
                  else cb.message.chat.id)
        await state.update_data(source_chat_id=src_id)
        await state.set_state(DateRange.start)
        await cb.message.answer(
            "🗓 *Свой диапазон дат*\n\n"
            "Введите *дату начала* одним из форматов:\n"
            "• `2026-04-10`\n"
            "• `10.04.2026`\n"
            "• `10.04.2026 14:30`\n\n"
            "Или /cancel — отмена."
        )
        return

    # пресет
    await cb.answer(PERIOD_LABELS.get(period, period))
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    # В личке источник — выбранный чат, в группе — сам чат
    if cb.message.chat.type == "private":
        chat_id = selected_chat.get(cb.from_user.id)
        if chat_id is None:
            await cb.message.answer("⚠️ Сначала выберите чат через /chats.")
            return
    else:
        chat_id = cb.message.chat.id
    all_msgs = chat_buffer.get(chat_id, [])
    filtered = filter_messages(all_msgs, hours=PERIOD_HOURS.get(period))
    await analyze_messages(cb.message, filtered, PERIOD_LABELS.get(period, period))


# --- FSM: ввод начальной даты ---
@dp.message(DateRange.start, Command("cancel"))
@dp.message(DateRange.end, Command("cancel"))
async def cancel_fsm(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("❌ Ввод дат отменён.")


@dp.message(DateRange.start)
async def set_start_date(msg: Message, state: FSMContext):
    dt = parse_user_date(msg.text or "")
    if not dt:
        await msg.answer(
            "⚠️ Не понял дату. Попробуйте формат:\n"
            "`2026-04-10` или `10.04.2026`\n\n"
            "Или /cancel для отмены."
        )
        return
    await state.update_data(date_from=dt.isoformat())
    await state.set_state(DateRange.end)
    await msg.answer(
        f"✅ Начало: {dt.strftime('%d.%m.%Y %H:%M')}\n\n"
        "Теперь введите *дату окончания* (тот же формат)."
    )


@dp.message(DateRange.end)
async def set_end_date(msg: Message, state: FSMContext):
    dt_to = parse_user_date(msg.text or "", end_of_day=True)
    if not dt_to:
        await msg.answer(
            "⚠️ Не понял дату. Повторите в формате\n"
            "`2026-04-17` или `17.04.2026 23:59`.\n\n"
            "Или /cancel."
        )
        return

    user_data = await state.get_data()
    dt_from = datetime.fromisoformat(user_data["date_from"])
    source_chat_id = user_data.get("source_chat_id", msg.chat.id)
    await state.clear()

    if dt_to < dt_from:
        await msg.answer(
            "⚠️ Дата окончания раньше даты начала. "
            "Запустите `/chat_analyze` заново."
        )
        return

    label = (f"с {dt_from.strftime('%d.%m.%Y')} "
             f"по {dt_to.strftime('%d.%m.%Y')}")

    all_msgs = chat_buffer.get(source_chat_id, [])
    filtered = filter_messages(all_msgs, date_from=dt_from, date_to=dt_to)
    await analyze_messages(msg, filtered, label)


# ============================================================
#  В личке — подсказка про групповые команды
# ============================================================

@dp.message(Command("chat_analyze"))
async def chat_analyze_dm(msg: Message):
    if msg.chat.type != "private":
        return  # уже обработано в групповом хэндлере
    # В личке — если выбран чат через /chats, анализируем его
    user_id = msg.from_user.id
    target_chat_id = selected_chat.get(user_id)
    if target_chat_id is None:
        await msg.answer(
            "💬 *Сначала выберите чат через /chats*\n\n"
            "Либо вызовите /chat\\_analyze прямо в нужном групповом чате."
        )
        return
    meta = chat_meta.get(target_chat_id, {})
    n = len(chat_buffer.get(target_chat_id, []))
    if n == 0:
        await msg.answer("📭 В выбранном чате пока нет сообщений.")
        return
    await msg.answer(
        f"💬 Чат: *{meta.get('title','—')}*\nСобрано сообщений: {n}\n\n🗓 Выберите период:",
        reply_markup=period_kb()
    )


@dp.message(Command("chat_stats"))
async def chat_stats_dm(msg: Message):
    if msg.chat.type != "private":
        return
    user_id = msg.from_user.id
    target_chat_id = selected_chat.get(user_id)
    if target_chat_id is None:
        await msg.answer(
            "💬 Сначала выберите чат через /chats — потом /chat\\_stats покажет статистику."
        )
        return
    # Эмулируем msg для статистики выбранного чата
    buf = chat_buffer.get(target_chat_id, [])
    meta = chat_meta.get(target_chat_id, {})
    if not buf:
        await msg.answer("📭 В выбранном чате нет сообщений.")
        return
    senders = {}
    for m in buf:
        senders[m["sender"]] = senders.get(m["sender"], 0) + 1
    top = sorted(senders.items(), key=lambda x: -x[1])[:5]
    text = (
        f"📊 *Статистика чата:* {meta.get('title','—')}\n\n"
        f"Сообщений: {len(buf)}\n"
        f"Авторов: {len(senders)}\n"
        f"Первое: {buf[0]['date']}\nПоследнее: {buf[-1]['date']}\n\n"
        "*Активные участники:*\n"
    )
    for s, c in top:
        name = s.replace("*", "").replace("_", "")[:30]
        text += f"• {name}: {c}\n"
    text += "\n*По периодам:*\n"
    for key in ("1d", "3d", "7d", "30d"):
        cnt = len(filter_messages(buf, hours=PERIOD_HOURS[key]))
        text += f"• {PERIOD_LABELS[key]}: {cnt}\n"
    text += "\n💡 /chat\\_analyze — запустить анализ."
    await msg.answer(text)


# ============================================================
#  /chats — список доступных чатов и выбор для анализа из лички
# ============================================================

@dp.message(Command("chats"))
async def list_chats(msg: Message):
    if msg.chat.type != "private":
        await msg.answer("💬 /chats работает только в личке с ботом.")
        return
    if not chat_meta:
        await msg.answer(
            "📭 *Пока ни одного чата.*\n\n"
            "Чтобы добавить чат для анализа:\n"
            "1. Добавьте бота в групповой чат\n"
            "2. Сделайте *администратором* (иначе бот не видит сообщения)\n"
            "3. Напишите там несколько сообщений\n"
            "4. Вернитесь в личку и снова /chats"
        )
        return
    buttons = []
    for cid, meta in chat_meta.items():
        n = len(chat_buffer.get(cid, []))
        title = meta.get("title", "—")[:35]
        buttons.append([InlineKeyboardButton(
            text=f"💬 {title} ({n} сообщ.)",
            callback_data=f"selchat:{cid}"
        )])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    user_id = msg.from_user.id
    current = selected_chat.get(user_id)
    current_meta = chat_meta.get(current, {}) if current else {}
    current_str = f"\n\n📌 *Текущий выбор:* {current_meta.get('title','—')}" if current else ""
    await msg.answer(
        f"💬 *Доступные чаты* ({len(chat_meta)}){current_str}\n\n"
        "Выберите чат — потом /chat\\_analyze или /chat\\_stats:",
        reply_markup=kb
    )


@dp.callback_query(F.data.startswith("selchat:"))
async def on_chat_select(cb: CallbackQuery):
    chat_id = int(cb.data.split(":", 1)[1])
    user_id = cb.from_user.id
    selected_chat[user_id] = chat_id
    meta = chat_meta.get(chat_id, {})
    n = len(chat_buffer.get(chat_id, []))
    await cb.answer(f"Выбран чат: {meta.get('title','—')}")
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.message.answer(
        f"✅ *Выбран чат:* {meta.get('title','—')}\n"
        f"Сообщений в буфере: {n}\n\n"
        "📊 /chat\\_stats — статистика\n"
        "🔬 /chat\\_analyze — анализ LLM"
    )


# ============================================================
#  Свободный анализ: текст в личке + загрузка файлов CSV/XLSX/TXT/JSON
# ============================================================

FREEFORM_SYSTEM = (
    "Ты — опытный бизнес-аналитик. На входе тебе дают произвольный текст "
    "(отзыв, переписка, фрагмент данных). Сделай краткий аналитический "
    "разбор на русском языке: тональность, ключевые темы, проблемы или "
    "позитив, краткие рекомендации. Структурируй ответ маркированным списком, "
    "пиши по делу, без воды."
)


async def analyze_freeform_text(target, text: str, label: str = "сообщение"):
    """LLM-разбор произвольного текста."""
    text = text.strip()
    if len(text) < 5:
        await target.answer("⚠️ Сообщение слишком короткое для анализа.")
        return
    await target.answer(
        f"🔍 *Анализирую {label}*\nМодель: `{MODEL}`\n⏳ Жду ответа..."
    )
    t0 = time.time()
    try:
        raw = ask_llm(text[:4000], FREEFORM_SYSTEM, max_tokens=500, timeout=120)
    except Exception as e:
        await target.answer(f"⚠️ Ошибка LLM: {e}")
        return
    dt = time.time() - t0
    body = raw.replace("_", "\\_").replace("[", "\\[").replace("]", "\\]")
    await target.answer(f"✅ Готово за {dt:.1f} с\n─────────────────")
    await send_long(target, body)


def extract_texts_from_file(file_bytes: bytes, filename: str) -> tuple[list, str]:
    """Парсит файл, возвращает (список_текстов, описание_формата).
    Поддерживает: CSV, XLSX, TXT, JSON."""
    name = filename.lower()
    import io as _io
    if name.endswith(".csv"):
        # Пробуем несколько кодировок
        for enc in ("utf-8", "cp1251", "latin-1"):
            try:
                df = pd.read_csv(_io.BytesIO(file_bytes), encoding=enc)
                break
            except Exception:
                df = None
        if df is None:
            return [], "CSV (не удалось распарсить)"
        return _texts_from_df(df), f"CSV ({len(df)} строк, {len(df.columns)} колонок)"
    if name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(_io.BytesIO(file_bytes))
        return _texts_from_df(df), f"Excel ({len(df)} строк, {len(df.columns)} колонок)"
    if name.endswith(".json"):
        import json as _json
        try:
            data_obj = _json.loads(file_bytes.decode("utf-8"))
        except Exception:
            return [], "JSON (битый)"
        if isinstance(data_obj, list):
            # Список словарей или строк
            texts = []
            for item in data_obj:
                if isinstance(item, str):
                    texts.append(item)
                elif isinstance(item, dict):
                    for key in ("text", "review", "comment", "message", "body"):
                        if key in item and isinstance(item[key], str):
                            texts.append(item[key])
                            break
            return texts, f"JSON-массив ({len(texts)} элементов)"
        if isinstance(data_obj, dict):
            return [str(data_obj)[:4000]], "JSON-объект"
        return [str(data_obj)[:4000]], "JSON"
    # TXT и всё остальное — как текст
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("cp1251", errors="ignore")
    # Разбиваем по непустым строкам
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 5]
    return lines, f"Текст ({len(lines)} непустых строк)"


def _texts_from_df(df) -> list:
    """Найти подходящую текстовую колонку в DataFrame."""
    # Приоритет — типовые имена
    for cand in ("text", "review", "comment", "message", "feedback", "body", "content"):
        for col in df.columns:
            if col.lower().strip() == cand:
                return [str(v) for v in df[col].dropna().tolist() if str(v).strip()]
    # Иначе — первая колонка типа object/string
    for col in df.columns:
        if df[col].dtype == object:
            return [str(v) for v in df[col].dropna().tolist() if str(v).strip()]
    # Иначе — первая колонка как есть
    return [str(v) for v in df.iloc[:, 0].dropna().tolist()]


@dp.message(F.chat.type == "private", F.document)
async def on_document(msg: Message):
    """Принимает CSV/XLSX/TXT/JSON и анализирует содержимое через LLM."""
    doc = msg.document
    fname = doc.file_name or "file"
    fsize_mb = (doc.file_size or 0) / 1024 / 1024
    if fsize_mb > 20:
        await msg.answer(f"⚠️ Файл слишком большой ({fsize_mb:.1f} МБ). Лимит 20 МБ.")
        return

    await msg.answer(
        f"📎 *Принял файл:* `{fname}`\nРазмер: {fsize_mb:.2f} МБ\n⏳ Загружаю..."
    )
    # Скачиваем
    try:
        bio = await bot.download(doc)
        file_bytes = bio.read()
    except Exception as e:
        await msg.answer(f"⚠️ Не удалось скачать: {e}")
        return

    # Парсим
    try:
        texts, fmt = extract_texts_from_file(file_bytes, fname)
    except Exception as e:
        await msg.answer(f"⚠️ Не смог разобрать файл ({fname}): {e}")
        return

    if not texts:
        await msg.answer(f"⚠️ Не нашёл подходящих данных в {fmt}.")
        return

    sample = texts[:20] if len(texts) > 20 else texts
    await msg.answer(
        f"📊 *Формат:* {fmt}\n"
        f"Найдено фрагментов: {len(texts)}\n"
        f"Анализирую первые {len(sample)} через LLM...\n"
        f"⏳ ~{int(len(sample) * 5)} с..."
    )

    t0 = time.time()
    joined = "\n\n".join(f"{i+1}. {t[:300]}" for i, t in enumerate(sample))
    system = (
        "Ты — опытный бизнес-аналитик. На входе — пакет коротких текстовых "
        "сообщений (отзывы, комментарии, переписка). Сделай сводный анализ "
        "на русском языке: 1) распределение тональности, 2) топ-3 ключевые темы, "
        "3) топ-3 проблемы или жалобы, 4) краткие рекомендации. "
        "Формат — маркированные списки, без воды."
    )
    try:
        raw = ask_llm(joined[:8000], system, max_tokens=700, timeout=180)
    except Exception as e:
        await msg.answer(f"⚠️ Ошибка LLM: {e}")
        return
    dt = time.time() - t0
    body = raw.replace("_", "\\_").replace("[", "\\[").replace("]", "\\]")
    await msg.answer(
        f"✅ Готово за {dt:.1f} с\n"
        f"Файл: `{fname}`\nПроанализировано: {len(sample)} из {len(texts)}\n"
        "─────────────────"
    )
    await send_long(msg, body)


@dp.message(F.chat.type == "private", F.text & ~F.text.startswith("/"))
async def on_freeform_text(msg: Message, state: FSMContext):
    """Любое текстовое сообщение в личке (не команда) — LLM-разбор.
    Игнорируем когда активен FSM (например, ввод дат)."""
    cur = await state.get_state()
    if cur is not None:
        return  # пусть FSM-хэндлеры разбираются
    await analyze_freeform_text(msg, msg.text or "")


# --- старт ---
async def main():
    load_data()
    log.info(
        "Loaded: test=%s, preds=%s, results=%d, report=%s",
        data.get("test") is not None,
        data.get("preds") is not None,
        len(data.get("results", {})),
        data.get("report") is not None,
    )
    await bot.set_my_commands([
        BotCommand(command="start", description="Описание"),
        BotCommand(command="analyze", description="🔥 Живой анализ 5 отзывов"),
        BotCommand(command="report", description="📄 Аналитический отчёт"),
        BotCommand(command="stats", description="📊 Статистика выборки"),
        BotCommand(command="alerts", description="🚨 Критические темы"),
        BotCommand(command="compare", description="🏆 Сравнение моделей"),
        BotCommand(command="chats", description="💬 Список чатов для анализа"),
        BotCommand(command="chat_analyze", description="💬 Анализ выбранного/текущего чата"),
        BotCommand(command="chat_stats", description="💬 Статистика выбранного/текущего чата"),
        BotCommand(command="help", description="Справка"),
    ])
    log.info("Bot ready")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
