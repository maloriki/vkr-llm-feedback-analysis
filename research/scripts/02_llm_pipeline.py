"""
LLM-пайплайн через Ollama.

Запускает sentiment-классификацию на тестовых 500 отзывах
через любую модель, поднятую в Ollama.

Примеры:
    python 02_llm_pipeline.py --model qwen2.5:7b
    python 02_llm_pipeline.py --model deepseek-llm:7b
    python 02_llm_pipeline.py --model all
"""
import argparse
import json
import time

import pandas as pd
import requests
from sklearn.metrics import (
    accuracy_score, classification_report, f1_score,
    precision_score, recall_score,
)

OLLAMA = "http://localhost:11434/api/generate"
LABELS = ["negative", "neutral", "positive"]

SYSTEM_PROMPT = """Ты — аналитик клиентской обратной связи.

Задача:
1. Определи тональность: positive / negative / neutral.
2. Выдели тему (1-3 слова).
3. Кратко (1 предложение) обоснуй тональность.

Все поля на русском языке.
Ответ СТРОГО в формате JSON:
{"sentiment": "positive|negative|neutral", "topic": "...", "reason": "..."}"""


def normalise_label(s: str) -> str:
    """Приводим русскоязычные варианты тональности к латинским меткам."""
    s = s.lower().strip()
    if s in ("positive", "позитивный", "позитивная", "положительный", "положительная"):
        return "positive"
    if s in ("negative", "негативный", "негативная", "отрицательный", "отрицательная"):
        return "negative"
    if s in ("neutral", "нейтральный", "нейтральная"):
        return "neutral"
    return s


def query_ollama(model: str, review: str, timeout: int = 120) -> dict:
    """Один запрос к Ollama и парсинг JSON-ответа."""
    payload = {
        "model": model,
        "prompt": f'Определи тональность следующего отзыва:\n\n"{review}"',
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 200},
    }
    try:
        r = requests.post(OLLAMA, json=payload, timeout=timeout)
        r.raise_for_status()
        text = r.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return {"sentiment": "", "error": "connection_error"}
    except requests.exceptions.Timeout:
        return {"sentiment": "", "error": "timeout"}
    except Exception as e:
        return {"sentiment": "", "error": str(e)}

    # иногда ответ обёрнут в ```json ... ```
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()

    # у reasoning-моделей — <think>...</think> перед JSON
    if "</think>" in text:
        text = text.split("</think>", 1)[1].strip()

    lo = text.find("{")
    hi = text.rfind("}") + 1
    if lo < 0 or hi <= lo:
        return {"sentiment": "", "error": "no_json", "raw": text}

    try:
        parsed = json.loads(text[lo:hi])
    except json.JSONDecodeError:
        return {"sentiment": "", "error": "bad_json", "raw": text}

    return {
        "sentiment": normalise_label(parsed.get("sentiment", "")),
        "topic": parsed.get("topic", ""),
        "reason": parsed.get("reason", ""),
        "error": None,
    }


def run(model: str):
    print("=" * 60)
    print(f" LLM experiment: {model}")
    print("=" * 60)

    df = pd.read_csv("test_set_500.csv")
    print(f"Тест: {len(df)} отзывов")
    print(df["sentiment"].value_counts().to_dict())

    # проверка доступности модели
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        available = [m["name"] for m in r.json().get("models", [])]
        if not any(model in m for m in available):
            print(f"\nМодель '{model}' не найдена. Скачайте её: ollama pull {model}")
            return None
    except Exception as e:
        print(f"Ollama недоступна: {e}")
        return None

    results = []
    errors = 0
    t0 = time.time()

    for i, row in df.iterrows():
        review = row["review"]
        if len(review) > 500:
            review = review[:500] + "..."
        r = query_ollama(model, review)
        results.append(r)
        if r.get("error"):
            errors += 1

        if (i + 1) % 25 == 0:
            elapsed = time.time() - t0
            eta = (len(df) - i - 1) / ((i + 1) / elapsed)
            print(f"  [{i+1}/{len(df)}] "
                  f"{elapsed:.0f}s, ~{eta:.0f}s left, "
                  f"errors={errors}")

    total = time.time() - t0
    print(f"\nВремя: {total:.1f}s ({total/len(df):.2f}s на отзыв)")
    print(f"Ошибок парсинга: {errors}/{len(df)}")

    y_true = df["sentiment"].values
    y_pred = [r["sentiment"] for r in results]
    valid = sum(1 for p in y_pred if p in LABELS)
    # непарсенные ответы считаем нейтральными — чтобы не ломать расчёт метрик
    y_pred_clean = [p if p in LABELS else "neutral" for p in y_pred]

    acc = accuracy_score(y_true, y_pred_clean)
    f1 = f1_score(y_true, y_pred_clean, average="macro", labels=LABELS)
    prec = precision_score(y_true, y_pred_clean, average="macro", labels=LABELS)
    rec = recall_score(y_true, y_pred_clean, average="macro", labels=LABELS)

    print(f"\nAcc={acc:.4f}  F1={f1:.4f}  Prec={prec:.4f}  Rec={rec:.4f}")
    print(f"Валидных предсказаний: {valid}/{len(df)}\n")
    print(classification_report(y_true, y_pred_clean,
                                target_names=LABELS, digits=4))

    # --- сохраняем результаты ---
    report = classification_report(y_true, y_pred_clean,
                                   target_names=LABELS, output_dict=True)
    summary = {
        "model": model,
        "accuracy": round(acc, 4),
        "macro_f1": round(f1, 4),
        "macro_precision": round(prec, 4),
        "macro_recall": round(rec, 4),
        "total_time_s": round(total, 1),
        "avg_time_per_review_s": round(total / len(df), 2),
        "valid_predictions": valid,
        "total_reviews": len(df),
        "errors": errors,
        "per_class": {
            c: {
                "precision": round(report[c]["precision"], 4),
                "recall": round(report[c]["recall"], 4),
                "f1": round(report[c]["f1-score"], 4),
            }
            for c in LABELS
        },
    }
    safe = model.replace(":", "_").replace("/", "_")
    with open(f"results_{safe}.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    pred_df = df.copy()
    pred_df[f"{safe}_pred"] = y_pred_clean
    pred_df[f"{safe}_topic"] = [r.get("topic", "") for r in results]
    pred_df[f"{safe}_reason"] = [r.get("reason", "") for r in results]
    pred_df.to_csv(f"predictions_{safe}.csv", index=False)

    print(f"Сохранено: results_{safe}.json, predictions_{safe}.csv")

    # покажем пару инсайтов — просто для sanity check
    print("\nНегативные отзывы (первые 3):")
    neg = df[df["sentiment"] == "negative"].head(3)
    for i, (_, row) in enumerate(neg.iterrows()):
        r = results[row.name]
        print(f"  [{i+1}] {row['review'][:80]}...")
        print(f"      -> {r.get('sentiment')} | {r.get('topic', '')} | "
              f"{r.get('reason', '')[:60]}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:7b",
                        help='название модели в Ollama или "all"')
    args = parser.parse_args()

    if args.model == "all":
        all_results = []
        for m in ("qwen2.5:7b", "deepseek-llm:7b"):
            res = run(m)
            if res:
                all_results.append(res)
        if all_results:
            print("\n" + "=" * 60)
            print(" SUMMARY")
            print("=" * 60)
            print(f"{'Model':<25}{'Acc':>8}{'F1':>8}{'Time':>10}")
            print("-" * 51)
            for r in all_results:
                print(f"{r['model']:<25}{r['accuracy']:>8.4f}"
                      f"{r['macro_f1']:>8.4f}{r['total_time_s']:>9.0f}s")
    else:
        run(args.model)
