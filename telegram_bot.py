"""
ИАС Анализа Обратной Связи — Telegram-бот для защиты ВКР.
Демонстрирует:
  - Живой LLM-анализ отзывов через Qwen 2.5 (Ollama)
  - Автоматическую генерацию аналитических отчётов
  - Отправку критических алертов

Запуск:
  set BOT_TOKEN=<твой_токен>
  python telegram_bot.py
"""
import asyncio
import json
import logging
import os
import random
import time
from datetime import datetime

import pandas as pd
import requests

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, BotCommand
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'qwen2.5:7b'

if not BOT_TOKEN:
    raise SystemExit('ERROR: Set BOT_TOKEN environment variable')

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher()


# ============================================================
# DATA LOADING & CHAT BUFFER
# ============================================================
DATA = {}
# In-memory buffer for group chat messages: {chat_id: [{text, sender, date}, ...]}
CHAT_BUFFER: dict = {}
MAX_BUFFER = 200


def load_data():
    """Load results and predictions."""
    try:
        DATA['test'] = pd.read_csv('test_set_500.csv')
    except Exception:
        DATA['test'] = None

    try:
        DATA['qwen_preds'] = pd.read_csv('predictions_qwen2.5_7b.csv')
    except Exception:
        DATA['qwen_preds'] = None

    DATA['results'] = {}
    for f in os.listdir('.'):
        if f.startswith('results_') and f.endswith('.json'):
            with open(f, 'r', encoding='utf-8') as fh:
                try:
                    d = json.load(fh)
                    DATA['results'][d.get('model', f)] = d
                except Exception:
                    pass

    try:
        with open('analytical_report_demo.md', 'r', encoding='utf-8') as fh:
            DATA['report'] = fh.read()
    except Exception:
        DATA['report'] = None

    logging.info(
        f"Loaded: test={DATA['test'] is not None}, "
        f"preds={DATA['qwen_preds'] is not None}, "
        f"results={len(DATA['results'])}, "
        f"report={DATA['report'] is not None}"
    )


# ============================================================
# COMMANDS
# ============================================================

@dp.message(CommandStart())
async def cmd_start(msg: Message):
    text = (
        "👋 *Добро пожаловать в ИАС Анализа Обратной Связи*\n\n"
        "Информационно-аналитическая система на основе LLM для автоматизации "
        "анализа клиентских отзывов и внутренних коммуникаций курьеров.\n\n"
        "*Разработка:* ВКР | НИУ ВШЭ | Биксалин А., 2026\n"
        "*Модель:* Qwen 2.5 7B (self-hosted через Ollama)\n"
        "*Нагрузка:* 500 тестовых отзывов | 6 сравниваемых моделей\n\n"
        "*Команды в личном чате:*\n"
        "/analyze — 🔥 живой анализ 5 отзывов (~30 сек)\n"
        "/report — 📄 аналитический отчёт по 20 отзывам\n"
        "/stats — 📊 статистика тестовой выборки\n"
        "/alerts — 🚨 критические негативные темы\n"
        "/compare — 🏆 сравнение 6 моделей\n\n"
        "*Команды в группе (добавьте бота):*\n"
        "/chat\\_analyze — 💬 анализ последних 20 сообщений\n"
        "/chat\\_stats — 💬 статистика собранных сообщений\n\n"
        "/help — 🔖 полная справка"
    )
    await msg.answer(text)


@dp.message(Command('help'))
async def cmd_help(msg: Message):
    text = (
        "*ℹ️ Справка по системе*\n\n"
        "Данный бот демонстрирует работу информационно-аналитической системы, "
        "разработанной в рамках ВКР. Система автоматически анализирует "
        "клиентскую обратную связь и генерирует структурированные инсайты.\n\n"
        "*Архитектура:*\n"
        "• Коннекторы сбора (OMS API, Telegram Bot)\n"
        "• Хранилище (PostgreSQL + MinIO)\n"
        "• LLM-конвейер (MapReduce + auto-batching)\n"
        "• Дашборд (Streamlit) + этот Telegram-бот\n\n"
        "*Технологический стек:*\n"
        "• Python 3.10, FastAPI, aiogram 3\n"
        "• Ollama + Qwen 2.5 7B (NVIDIA RTX 3080)\n"
        "• Альтернативы: YandexGPT Pro, DeepSeek LLM 7B\n\n"
        "*Ключевой результат:*\n"
        "Сокращение Time-to-Insight с 1–2 дней до минут, "
        "экономия ~780 тыс. руб/год на команду."
    )
    await msg.answer(text)


def query_llm(review: str, timeout: int = 120) -> dict:
    """Send review to Ollama."""
    system = (
        "Ты — аналитик клиентской обратной связи.\n"
        "Определи тональность отзыва (positive/negative/neutral), "
        "тему (1-3 слова), причину (1 предложение).\n"
        "ВАЖНО: все поля ответа (topic, reason) должны быть на "
        "РУССКОМ ЯЗЫКЕ. Не используй китайский, английский или другие языки.\n"
        'Ответ СТРОГО JSON: {"sentiment": "...", "topic": "...", "reason": "..."}'
    )
    try:
        r = requests.post(OLLAMA_URL, json={
            'model': MODEL,
            'system': system,
            'prompt': f'Определи тональность:\n"{review[:300]}"',
            'stream': False,
            'options': {'temperature': 0.1, 'num_predict': 200},
        }, timeout=timeout)
        text = r.json().get('response', '').strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            parsed = json.loads(text[start:end])
            return {
                'sentiment': parsed.get('sentiment', '').lower().strip(),
                'topic': parsed.get('topic', ''),
                'reason': parsed.get('reason', ''),
            }
    except Exception as e:
        return {'error': str(e)}
    return {'error': 'no_json'}


EMOJI = {'positive': '🟢', 'negative': '🔴', 'neutral': '⚪', '': '❓'}


# ============================================================
# GROUP CHAT MESSAGE COLLECTOR
# ============================================================
@dp.message(F.chat.type.in_({'group', 'supergroup'}))
async def collect_group_message(msg: Message):
    """Collect messages from group chats (when bot is admin)."""
    # Skip commands
    if msg.text and msg.text.startswith('/'):
        await handle_group_command(msg)
        return

    if not msg.text or len(msg.text.strip()) < 3:
        return

    chat_id = msg.chat.id
    if chat_id not in CHAT_BUFFER:
        CHAT_BUFFER[chat_id] = []

    sender = msg.from_user.full_name if msg.from_user else 'Аноним'
    CHAT_BUFFER[chat_id].append({
        'text': msg.text,
        'sender': sender,
        'date': msg.date.strftime('%Y-%m-%d %H:%M') if msg.date else '',
    })

    # Keep only last MAX_BUFFER messages
    if len(CHAT_BUFFER[chat_id]) > MAX_BUFFER:
        CHAT_BUFFER[chat_id] = CHAT_BUFFER[chat_id][-MAX_BUFFER:]


async def handle_group_command(msg: Message):
    """Handle /chat_analyze in group chats."""
    if not msg.text:
        return
    cmd = msg.text.split()[0].split('@')[0]

    if cmd == '/chat_analyze':
        await cmd_chat_analyze(msg)
    elif cmd == '/chat_stats':
        await cmd_chat_stats(msg)


async def cmd_chat_analyze(msg: Message):
    """Analyze last N messages from the current group chat."""
    chat_id = msg.chat.id
    messages = CHAT_BUFFER.get(chat_id, [])

    if len(messages) < 3:
        await msg.answer(
            f"📭 Собрано пока {len(messages)} сообщений. "
            f"Нужно минимум 3 для анализа.\n\n"
            f"Напишите ещё несколько сообщений и попробуйте снова."
        )
        return

    # Take last 20 messages for analysis
    sample = messages[-20:]

    await msg.answer(
        f"🔍 *Анализ последних {len(sample)} сообщений чата*\n\n"
        f"Модель: `Qwen 2.5 7B` (self-hosted)\n"
        f"Промпт: MAP-фаза (анализ групповой переписки)\n\n"
        f"⏳ Выполняется обработка..."
    )

    # Compose messages text
    msgs_text = '\n'.join(
        f'[{m["date"]}] {m["sender"]}: {m["text"][:200]}'
        for m in sample
    )

    system = (
        "Ты — старший аналитик операционной эффективности. "
        "Проанализируй пакет сообщений из рабочего чата и выдели:\n"
        "1. Основные темы обсуждения (с частотой)\n"
        "2. Настроение группы (позитивное/негативное/нейтральное)\n"
        "3. Проблемы и жалобы (с цитатами)\n"
        "4. Рекомендации для руководства\n\n"
        "ВАЖНО: отвечай ТОЛЬКО на русском языке. "
        "Не используй китайский, английский или другие языки."
    )

    prompt = f"Проанализируй следующий пакет из {len(sample)} сообщений чата:\n\n{msgs_text}"

    t0 = time.time()
    try:
        r = requests.post(OLLAMA_URL, json={
            'model': MODEL,
            'system': system,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.3, 'num_predict': 1500},
        }, timeout=240)
        response_text = r.json().get('response', '')
    except Exception as e:
        await msg.answer(f'⚠️ Ошибка: {e}')
        return

    elapsed = time.time() - t0

    header = (
        f"✅ *Анализ готов за {elapsed:.1f} сек*\n"
        f"Проанализировано: {len(sample)} сообщений\n"
        f"─────────────────\n"
    )

    # Escape markdown specials
    clean = response_text.replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')

    response = header + clean

    if len(response) > 4000:
        # Send in chunks
        await msg.answer(header, parse_mode=ParseMode.MARKDOWN)
        remaining = clean
        while remaining:
            chunk = remaining[:3900]
            split_at = chunk.rfind('\n')
            if split_at > 2000:
                chunk = remaining[:split_at]
            else:
                chunk = remaining[:3900]
            await msg.answer(chunk, parse_mode=None)
            remaining = remaining[len(chunk):].lstrip()
    else:
        await msg.answer(response)


async def cmd_chat_stats(msg: Message):
    """Show stats about collected messages in this chat."""
    chat_id = msg.chat.id
    messages = CHAT_BUFFER.get(chat_id, [])

    if not messages:
        await msg.answer(
            "📭 В этом чате пока не собрано сообщений.\n"
            "Добавьте бота в админы чата и напишите несколько сообщений."
        )
        return

    senders = {}
    for m in messages:
        senders[m['sender']] = senders.get(m['sender'], 0) + 1

    top_senders = sorted(senders.items(), key=lambda x: -x[1])[:5]

    text = (
        f"📊 *Статистика чата*\n\n"
        f"*Собрано сообщений:* {len(messages)}\n"
        f"*Уникальных авторов:* {len(senders)}\n"
        f"*Первое сообщение:* {messages[0]['date']}\n"
        f"*Последнее сообщение:* {messages[-1]['date']}\n\n"
        f"*Топ-5 активных участников:*\n"
    )
    for sender, count in top_senders:
        sender_clean = sender.replace('*', '').replace('_', '')[:30]
        text += f"• {sender_clean}: {count} сообщ.\n"

    text += f"\n💡 Используйте `/chat\\_analyze` для AI-анализа."
    await msg.answer(text)


@dp.message(Command('analyze'))
async def cmd_analyze(msg: Message):
    """Live LLM analysis of 5 random reviews."""
    if DATA.get('test') is None:
        await msg.answer('⚠️ Тестовая выборка не загружена.')
        return

    await msg.answer(
        "🔍 *Запуск LLM-анализа*\n\n"
        "Модель: `Qwen 2.5 7B` (self-hosted)\n"
        "Инфраструктура: NVIDIA RTX 3080 через Ollama\n"
        "Размер пакета: 5 отзывов\n\n"
        "⏳ Выполняется анализ..."
    )

    # Random 5 reviews
    sample = DATA['test'].sample(5, random_state=int(time.time()) % 100)

    t0 = time.time()
    results = []
    for _, row in sample.iterrows():
        r = query_llm(row['review'])
        results.append({
            'review': row['review'],
            'true': row['sentiment'],
            **r
        })
    elapsed = time.time() - t0

    # Format response
    lines = [
        f"✅ *Анализ завершён за {elapsed:.1f} сек* "
        f"({elapsed/len(results):.1f} сек/отзыв)\n",
        "*Результаты:*\n"
    ]

    for i, r in enumerate(results, 1):
        true = r['true']
        pred = r.get('sentiment', 'ошибка')
        match = '✓' if pred == true else '✗'
        review_text = r['review'][:100].replace('*', '').replace('_', '')

        lines.append(
            f"*{i}.* {EMOJI.get(pred, '❓')} _{pred}_ {match} "
            f"(истина: {true})\n"
            f"  💬 «{review_text}...»\n"
            f"  🏷 Тема: _{r.get('topic', '—')}_\n"
            f"  💡 {r.get('reason', '—')[:120]}\n"
        )

    # Summary
    correct = sum(1 for r in results if r.get('sentiment') == r['true'])
    lines.append(
        f"\n📊 *Точность на выборке:* {correct}/{len(results)} "
        f"({correct/len(results)*100:.0f}%)"
    )

    response = '\n'.join(lines)
    # Telegram limit 4096 chars
    if len(response) > 4000:
        response = response[:3990] + '...'

    await msg.answer(response)


@dp.message(Command('report'))
async def cmd_report(msg: Message):
    """Show analytical report from MAP phase demo."""
    if DATA.get('report') is None:
        await msg.answer('⚠️ Аналитический отчёт не найден.')
        return

    await msg.answer(
        "📄 *Аналитический отчёт*\n\n"
        "Источник: анализ 20 клиентских отзывов\n"
        "Модель: Qwen 2.5 7B | Фаза: MAP\n"
        "Промпт: развёрнутый аналитический\n"
    )

    # Split report into chunks if too long
    report = DATA['report']
    # Escape markdown specials that might break telegram formatting
    report = report.replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')

    chunks = []
    while report:
        if len(report) <= 3800:
            chunks.append(report)
            break
        split_at = report.rfind('\n', 0, 3800)
        if split_at < 0:
            split_at = 3800
        chunks.append(report[:split_at])
        report = report[split_at:].lstrip()

    for chunk in chunks:
        await msg.answer(chunk, parse_mode=None)


@dp.message(Command('stats'))
async def cmd_stats(msg: Message):
    if DATA.get('test') is None:
        await msg.answer('⚠️ Данные не загружены.')
        return

    df = DATA['test']
    dist = df['sentiment'].value_counts()

    text = (
        "📊 *Статистика тестовой выборки*\n\n"
        f"*Всего отзывов:* {len(df)}\n"
        f"*Датасет:* RuReviews (Smetanin, 2019)\n"
        f"*Категория:* клиентские отзывы e-commerce\n\n"
        f"*Распределение по классам:*\n"
        f"🟢 positive: {dist.get('positive', 0)} ({dist.get('positive', 0)/len(df)*100:.1f}%)\n"
        f"🔴 negative: {dist.get('negative', 0)} ({dist.get('negative', 0)/len(df)*100:.1f}%)\n"
        f"⚪ neutral: {dist.get('neutral', 0)} ({dist.get('neutral', 0)/len(df)*100:.1f}%)\n\n"
        f"*Средняя длина отзыва:* {df['review'].str.len().mean():.0f} символов\n"
        f"*Минимум / Максимум:* {df['review'].str.len().min()} / {df['review'].str.len().max()} символов"
    )
    await msg.answer(text)


@dp.message(Command('alerts'))
async def cmd_alerts(msg: Message):
    if DATA.get('qwen_preds') is None:
        await msg.answer('⚠️ Данные предсказаний не загружены.')
        return

    df = DATA['qwen_preds']
    pred_col = [c for c in df.columns if '_pred' in c][0]
    topic_col = [c for c in df.columns if '_topic' in c][0]

    negative = df[df[pred_col] == 'negative']
    top_topics = negative[topic_col].value_counts().head(5)

    lines = [
        "🚨 *Критические алерты*\n",
        f"Выявлено {len(negative)} негативных отзывов из {len(df)} "
        f"({len(negative)/len(df)*100:.0f}%)\n",
        "*Топ-5 негативных тем:*\n"
    ]

    for topic, count in top_topics.items():
        if not topic or str(topic) == 'nan':
            continue
        # Clean topic
        topic_clean = str(topic).replace('*', '').replace('_', '')[:50]
        severity = '🔴🔴🔴' if count > 10 else '🔴🔴' if count > 5 else '🔴'
        lines.append(f"{severity} *{topic_clean}* — {count} упоминаний")

    # Most urgent negative example
    if len(negative) > 0:
        example = negative.iloc[0]
        reason_col = [c for c in df.columns if '_reason' in c][0]
        lines.append(
            f"\n*Пример критичного отзыва:*\n"
            f"_«{example['review'][:150]}...»_\n\n"
            f"🏷 Тема: {example[topic_col]}\n"
            f"💡 {example[reason_col][:150]}"
        )

    lines.append(
        f"\n\n⏰ *Рекомендация:* разобрать топ-1 тему в течение 24 часов."
    )

    await msg.answer('\n'.join(lines))


@dp.message(Command('compare'))
async def cmd_compare(msg: Message):
    if not DATA.get('results'):
        await msg.answer('⚠️ Результаты не найдены.')
        return

    lines = [
        "🏆 *Сравнение моделей*\n",
        "Эксперимент: 500 отзывов, 3 класса (pos/neg/neu)\n",
        "```",
        f"{'Модель':<26} {'Acc':>6} {'F1':>6}",
        "─" * 40,
    ]

    # Known model display order
    model_order = [
        ('TF-IDF + XGBoost', 'TF-IDF + XGBoost'),
        ('YandexGPT Pro', 'YandexGPT Pro'),
        ('YandexGPT Embeddings + LogReg', 'YandexGPT Emb+LogReg'),
        ('qwen2.5:7b', 'Qwen 2.5 7B'),
        ('deepseek-llm:7b', 'DeepSeek LLM 7B'),
        ('deepseek-r1:7b', 'DeepSeek R1 7B'),
    ]

    for key, display in model_order:
        if key in DATA['results']:
            d = DATA['results'][key]
            acc = d.get('accuracy', 0)
            f1 = d.get('macro_f1', 0)
            lines.append(f"{display:<26} {acc:>6.3f} {f1:>6.3f}")

    lines.append("```\n")
    lines.append(
        "*Вывод:* TF-IDF лидирует по метрикам (обучен на 89K), "
        "но LLM (Qwen, YandexGPT) генерируют *аналитические инсайты* — "
        "то, что baseline не умеет."
    )

    await msg.answer('\n'.join(lines))


# ============================================================
# STARTUP
# ============================================================
async def on_startup():
    load_data()
    await bot.set_my_commands([
        BotCommand(command='start', description='Описание системы'),
        BotCommand(command='analyze', description='🔥 Живой анализ 5 отзывов'),
        BotCommand(command='report', description='📄 Аналитический отчёт'),
        BotCommand(command='stats', description='📊 Статистика выборки'),
        BotCommand(command='alerts', description='🚨 Критические инсайты'),
        BotCommand(command='compare', description='🏆 Сравнение моделей'),
        BotCommand(command='chat_analyze', description='💬 Анализ группового чата'),
        BotCommand(command='chat_stats', description='💬 Статистика собран. сообщений'),
        BotCommand(command='help', description='Справка'),
    ])
    logging.info('Bot ready!')


async def main():
    await on_startup()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
