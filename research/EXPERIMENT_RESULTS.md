# Эксперимент: сравнение 7 моделей анализа тональности

Сравнительная оценка моделей на сбалансированной выборке [test_set_500.csv](../test_set_500.csv) (500 отзывов RuReviews — Smetanin & Komarov, 2019, по ~167 на класс).

## Структура

- **results/** — машиночитаемые метрики и предсказания
  - 7 файлов `results_*.json` — Accuracy, Macro F1, Precision, Recall, время обработки
  - 4 файла `predictions_*.csv` — предсказания каждой модели на 500 отзывах
- **analytical_report_demo.md** — пример полного аналитического отчёта, который генерирует Qwen 2.5 7B на пакете из 20 отзывов

## Сводные результаты

| Модель | Тип | Accuracy | Macro F1 | Время | Инсайты |
|---|---|---:|---:|:---:|:---:|
| TF-IDF + XGBoost | классификатор | **0,744** | **0,747** | < 1 с | ❌ |
| YandexGPT Embeddings + LogReg (300 экз.) | классификатор | 0,675 | 0,676 | ~3 с | ❌ |
| YandexGPT Pro | LLM (cloud) | 0,674 | 0,652 | 8,2 с/отзыв | ✅ |
| Qwen 2.5 7B | LLM (self-hosted) | 0,656 | 0,634 | 4,3 с/отзыв | ✅ |
| DeepSeek LLM 7B | LLM (self-hosted) | 0,646 | 0,640 | 4,3 с/отзыв | ✅ |
| DeepSeek R1 7B | reasoning LLM | 0,480 | 0,496 | 14,5 с/отзыв | ⚠️ |
| YandexGPT Classifier | zero-shot cloud | 0,167 | 0,167 | 0,8 с/отзыв | ❌ |

Bootstrap-CI (1000 ресэмплов, N=500) для F1-макро:

| Модель | Точка | 95% CI |
|---|---:|:---:|
| TF-IDF + XGBoost | 0,747 | [0,711; 0,783] |
| YandexGPT Pro | 0,652 | [0,615; 0,688] |
| DeepSeek LLM 7B | 0,640 | [0,602; 0,680] |
| Qwen 2.5 7B | 0,634 | [0,595; 0,671] |

## Ключевые выводы

1. **TF-IDF + XGBoost — лучший по метрикам**, но не генерирует инсайтов.
2. **Qwen 2.5 7B рекомендована** как оптимальная self-hosted модель: качество близкое к лидерам LLM (CI пересекаются с DeepSeek/YandexGPT) + контекстное окно 32K токенов (vs 4K у DeepSeek), что критично для пакетного MapReduce-конвейера.
3. **DeepSeek R1 7B (reasoning)** показала F1=0,496 — это **намеренно включённый негативный результат**, демонстрирующий неприменимость reasoning-моделей к простой классификации. Сильный аргумент на защите.
4. **YandexGPT Classifier** (готовый облачный zero-shot) деградирует до 0,167 — методологическое подтверждение неприменимости предобученных классификаторов без few-shot-настройки на доменных данных.

## Воспроизводимость

```bash
pip install -r ../requirements.txt
python ../01_baseline_tfidf.py        # baseline
python ../02_llm_pipeline.py --model qwen2.5:7b
python ../05_yandexgpt.py              # требует YANDEX_FOLDER_ID + YANDEX_API_KEY
```

Тестовая выборка фиксированная — все модели сравниваются на одних и тех же 500 отзывах. Результаты пишутся в `results/`.

## Источник данных

[RuReviews](https://github.com/sismetanin/rureviews) — Smetanin S., Komarov M. *Sentiment Analysis of Product Reviews in Russian using Convolutional Neural Networks* // IEEE 21st Conference on Business Informatics, 2019.
