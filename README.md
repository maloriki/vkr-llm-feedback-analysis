# vkr-llm-feedback-analysis

**ВКР Биксалина Артёма Ильнуровича** | НИУ ВШЭ, Высшая школа бизнеса, ББИ-221, 2026

Информационно-аналитическая система (ИАС) для автоматизированного мульти-источникового анализа обратной связи в логистической e-commerce компании на основе больших языковых моделей.

## Структура репозитория

```
.
├── vkr_thesis/             # текст ВКР: PDF, аннотации
├── diagrams/               # все 12 диаграмм из ВКР
│   ├── images/             # финальные PNG
│   ├── sources/            # исходники: drawio, bpmn, puml, archimate
│   ├── svg/                # векторные версии
│   └── code/               # python-генераторы
├── experiments/            # сравнение 7 моделей
│   ├── results/            # results_*.json + predictions_*.csv
│   ├── analytical_report_demo.md
│   └── README.md           # выводы по моделям
├── 01_baseline_tfidf.py    # TF-IDF + XGBoost
├── 02_llm_pipeline.py      # универсальный Ollama-пайплайн
├── 03_llm_gpt35.py         # GPT-3.5
├── 04_deepseek_100.py      # DeepSeek на 100 отзывах
├── 05_yandexgpt.py         # YandexGPT Pro
├── 06_yandex_classifier.py # YandexGPT Embeddings/Classifier
├── prompts.py              # системные промпты
├── dashboard.py            # Streamlit-дашборд
├── telegram_bot.py         # Telegram-бот (aiogram 3, multi-chat, файлы)
├── test_set_500.csv        # балансированная выборка для эксперимента
├── rureviews.csv           # полный датасет
├── PROJECT_BRIEF.md        # бриф для передачи контекста
├── requirements.txt
└── .gitignore
```

## Быстрый старт

### Воспроизвести эксперимент

```bash
pip install -r requirements.txt
python 01_baseline_tfidf.py
python 02_llm_pipeline.py --model qwen2.5:7b
```

Результаты появятся в `experiments/results/`.

### Запустить дашборд

```bash
streamlit run dashboard.py
```

Откроется на http://localhost:8501 — четыре вкладки: Сравнение моделей, Анализ предсказаний, Инсайты LLM, Данные.

### Запустить Telegram-бот

```bash
# Установить Ollama (https://ollama.com/download) и модель:
ollama pull qwen2.5:7b

# Запустить бота:
export BOT_TOKEN=<токен от @BotFather>
python telegram_bot.py
```

Бот: [@vkr_reviews_analyzer_bot](https://t.me/vkr_reviews_analyzer_bot)

Команды:
- `/analyze`, `/report`, `/stats`, `/alerts`, `/compare` — демо на встроенной выборке
- `/chats` — список подключённых групповых чатов с inline-выбором
- `/chat_analyze`, `/chat_stats` — анализ выбранного/текущего чата
- **Любой текст** в личке → LLM делает аналитический разбор
- **CSV / XLSX / TXT / JSON файл** → пакетный анализ содержимого

## Финальный текст ВКР

**[vkr_thesis/VKR_Biksalin_final.pdf](vkr_thesis/VKR_Biksalin_final.pdf)** (94 страницы, прошёл LMS НИУ ВШЭ).

## Ключевые результаты (7 моделей, RuReviews-500)

| Модель | Macro F1 | Тип | Инсайты |
|---|---:|---|:---:|
| TF-IDF + XGBoost | **0,747** | классификатор | ❌ |
| YandexGPT Embeddings + LogReg | 0,676 | классификатор (300 экз.) | ❌ |
| YandexGPT Pro | 0,652 | LLM, облако | ✅ |
| DeepSeek LLM 7B | 0,640 | LLM, self-hosted | ✅ |
| **Qwen 2.5 7B** | 0,634 | **рекомендованная** self-hosted | ✅ |
| DeepSeek R1 7B | 0,496 | reasoning | ⚠️ |
| YandexGPT Classifier | 0,167 | zero-shot облачный | ❌ |

Подробный разбор — в [experiments/README.md](experiments/README.md).

## Реквизиты

- **Автор**: Биксалин Артём Ильнурович, ББИ-221
- **Научный руководитель**: Попов Виктор Юрьевич, профессор департамента бизнес-информатики ВШБ НИУ ВШЭ
- **Защита**: 17.05.2026

## Контакты

Telegram: [@vkr_reviews_analyzer_bot](https://t.me/vkr_reviews_analyzer_bot)
