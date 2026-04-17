# ИАС Анализа Обратной Связи на основе LLM

**Выпускная квалификационная работа (ВКР)** — НИУ ВШЭ, Высшая Школа Бизнеса
Направление: Бизнес-информатика
Тема: Автоматизация бизнес-процессов промышленной компании с использованием больших языковых моделей

## Описание

Информационно-аналитическая система для автоматизации анализа клиентской обратной связи и внутренних коммуникаций курьеров на основе больших языковых моделей (LLM).

**Ключевые особенности:**
- Мульти-источниковый сбор данных (OMS API + Telegram Bot)
- LLM-конвейер с паттерном MapReduce и auto-batching
- Поддержка self-hosted моделей (Qwen 2.5, DeepSeek) и облачных API (YandexGPT)
- Автоматическая генерация аналитических инсайтов с цитатами и рекомендациями
- Интерактивный дашборд (Streamlit) и Telegram-бот

## Результаты эксперимента

Сравнение 6 моделей на 500 клиентских отзывах (датасет RuReviews):

| Модель | Тип | Accuracy | Macro F1 |
|--------|-----|:---:|:---:|
| TF-IDF + XGBoost | Обученная (89.5K) | **0.744** | **0.747** |
| YandexGPT Embeddings + LogReg | Обученная (300) | 0.675 | 0.676 |
| YandexGPT Pro | Zero-shot, cloud | 0.674 | 0.652 |
| Qwen 2.5 7B | Zero-shot, self-hosted | 0.656 | 0.634 |
| DeepSeek LLM 7B | Zero-shot, self-hosted | 0.646 | 0.640 |
| DeepSeek R1 7B | Reasoning, self-hosted | 0.480 | 0.496 |

## Структура проекта

```
├── 01_baseline_tfidf.py      # TF-IDF + XGBoost baseline
├── 02_llm_pipeline.py         # Универсальный пайплайн для Ollama
├── 05_yandexgpt.py            # YandexGPT Pro эксперимент
├── 06_yandex_classifier.py    # YandexGPT Classifier + Embeddings
├── prompts.py                 # Системные промпты (4 шт)
├── dashboard.py               # Streamlit дашборд
├── telegram_bot.py            # Telegram-бот для демо
├── results_*.json             # Метрики экспериментов
├── predictions_*.csv          # Предсказания моделей
└── test_set_500.csv           # Тестовая выборка (500 отзывов)
```

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install pandas scikit-learn xgboost openai requests streamlit plotly aiogram
```

Установите Ollama: https://ollama.com

```bash
ollama pull qwen2.5:7b
ollama pull deepseek-llm:7b
```

### 2. Скачивание датасета

```bash
curl -L -o rureviews.csv "https://raw.githubusercontent.com/sismetanin/rureviews/master/women-clothing-accessories.3-class.balanced.csv"
```

### 3. Запуск экспериментов

```bash
# Baseline
python 01_baseline_tfidf.py

# LLM через Ollama
python 02_llm_pipeline.py --model qwen2.5:7b
python 02_llm_pipeline.py --model deepseek-llm:7b

# YandexGPT (нужен API-ключ)
export YANDEX_FOLDER_ID="b1g..."
export YANDEX_API_KEY="..."
python 05_yandexgpt.py
python 06_yandex_classifier.py
```

### 4. Запуск дашборда

```bash
streamlit run dashboard.py
```

Открыть: http://localhost:8501

### 5. Запуск Telegram-бота

```bash
# Windows PowerShell
$env:BOT_TOKEN="ваш_токен"
python telegram_bot.py

# Linux/Mac
export BOT_TOKEN="ваш_токен"
python telegram_bot.py
```

## Технологический стек

- **Python 3.10+**
- **LLM:** Qwen 2.5 7B / DeepSeek LLM 7B / YandexGPT Pro
- **ML:** scikit-learn, XGBoost
- **Инфраструктура:** Ollama (self-hosted), Yandex Cloud (API)
- **Визуализация:** Streamlit, Plotly
- **Бот:** aiogram 3.x

## Датасет

**RuReviews** (Smetanin & Komarov, 2019):
- 90 000 русскоязычных отзывов
- 3 класса: positive / negative / neutral
- Источник: [github.com/sismetanin/rureviews](https://github.com/sismetanin/rureviews)

## Автор

**Биксалин Артём**, группа ББИ 221
НИУ ВШЭ, ВШБ, 2026

---

*Проект создан в рамках ВКР по направлению "Бизнес-информатика".*
