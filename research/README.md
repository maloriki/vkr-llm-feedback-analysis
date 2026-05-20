# Исследование: сравнение моделей анализа тональности

Здесь весь экспериментальный код, данные и результаты сравнения 7 моделей на сбалансированной выборке RuReviews.

## Структура

```
research/
├── scripts/                # код экспериментов
│   ├── 01_baseline_tfidf.py     # TF-IDF + XGBoost (классический baseline)
│   ├── 02_llm_pipeline.py       # универсальный пайплайн под Ollama
│   ├── 03_llm_gpt35.py          # GPT-3.5 (для сравнения с локальными)
│   ├── 04_deepseek_100.py       # быстрый прогон DeepSeek на 100 отзывах
│   ├── 05_yandexgpt.py          # YandexGPT Pro через Yandex Cloud
│   ├── 06_yandex_classifier.py  # YandexGPT Embeddings + Classifier
│   └── prompts.py               # системные промпты для всех LLM
├── data/                   # датасеты
│   ├── rureviews.csv             # полный (90K отзывов)
│   └── test_set_*.csv            # балансированные выборки (100/500/1000)
├── results/                # результаты экспериментов
│   ├── results_*.json            # метрики (Accuracy, Macro F1, Precision, Recall, время)
│   └── predictions_*.csv         # предсказания моделей на 500 отзывах
├── dashboard.py            # Streamlit-дашборд (4 вкладки)
├── analytical_report_demo.md  # пример отчёта, который генерирует Qwen 2.5
└── EXPERIMENT_RESULTS.md   # выводы по эксперименту + bootstrap-CI
```

## Запуск экспериментов

```bash
cd research
python scripts/01_baseline_tfidf.py
python scripts/02_llm_pipeline.py --model qwen2.5:7b
python scripts/02_llm_pipeline.py --model deepseek-llm:7b

# Для облачных моделей нужны переменные:
export YANDEX_FOLDER_ID="..."
export YANDEX_API_KEY="..."
python scripts/05_yandexgpt.py
```

Все результаты пишутся в `results/`.

## Дашборд

```bash
cd research
streamlit run dashboard.py
```

Откроется на http://localhost:8501. Четыре вкладки:
1. **Сравнение моделей** — F1, точность, скорость
2. **Анализ предсказаний** — confusion matrix, распределение ошибок
3. **Инсайты LLM** — топ-15 тем, которые модель сама вытянула из отзывов
4. **Данные** — сырые JSON + тестовая выборка + пример отчёта

## Главное

См. [EXPERIMENT_RESULTS.md](EXPERIMENT_RESULTS.md) — там подробный разбор результатов и обоснование выбора Qwen 2.5 7B как production-модели.

## Источник данных

[RuReviews](https://github.com/sismetanin/rureviews) — Smetanin S., Komarov M. *Sentiment Analysis of Product Reviews in Russian using Convolutional Neural Networks* // IEEE 21st Conference on Business Informatics, 2019.
