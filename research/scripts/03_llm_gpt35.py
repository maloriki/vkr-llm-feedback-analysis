"""
LLM Experiment: GPT-3.5 Turbo через OpenAI API.
Тестирует на тех же 500 отзывах, что и baseline.
"""
import pandas as pd
import json
import time
import os
from openai import OpenAI
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    classification_report
)

API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = "gpt-3.5-turbo"

SYSTEM_PROMPT = """Ты — аналитик клиентской обратной связи. Твоя задача — определить тональность отзыва.

Правила:
1. Определи тональность: positive, negative или neutral
2. Выдели основную тему отзыва (1-3 слова)
3. Кратко объясни причину такой тональности (1 предложение)

Ответ СТРОГО в формате JSON:
{"sentiment": "positive|negative|neutral", "topic": "тема", "reason": "причина"}

Ничего кроме JSON не пиши."""


def query_gpt(client, review: str) -> dict:
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f'Определи тональность следующего отзыва:\n\n"{review}"'}
            ],
            temperature=0.1,
            max_tokens=200,
            timeout=30,
        )
        text = resp.choices[0].message.content.strip()

        # Parse JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(text[start:end])
            sentiment = parsed.get("sentiment", "").lower().strip()

            norm = {
                "positive": "positive", "позитивный": "positive",
                "позитивная": "positive", "положительный": "positive",
                "положительная": "positive",
                "negative": "negative", "негативный": "negative",
                "негативная": "negative", "отрицательный": "negative",
                "отрицательная": "negative",
                "neutral": "neutral", "нейтральный": "neutral",
                "нейтральная": "neutral",
            }
            sentiment = norm.get(sentiment, sentiment)

            return {
                "sentiment": sentiment,
                "topic": parsed.get("topic", ""),
                "reason": parsed.get("reason", ""),
                "raw": text,
                "error": None,
                "tokens": resp.usage.total_tokens if resp.usage else 0,
            }

        return {"sentiment": "", "topic": "", "reason": "",
                "raw": text, "error": "no_json", "tokens": 0}

    except Exception as e:
        return {"sentiment": "", "topic": "", "reason": "",
                "raw": "", "error": str(e), "tokens": 0}


def main():
    if not API_KEY:
        print("ERROR: Set OPENAI_API_KEY environment variable")
        return

    client = OpenAI(api_key=API_KEY)

    print("=" * 60)
    print(f"LLM EXPERIMENT: {MODEL}")
    print("=" * 60)

    df = pd.read_csv('test_set_500.csv')
    print(f"Test set: {len(df)} reviews")

    results = []
    errors = 0
    total_tokens = 0
    t0 = time.time()

    for i, row in df.iterrows():
        review = row['review']
        if len(review) > 500:
            review = review[:500] + "..."

        r = query_gpt(client, review)
        results.append(r)
        total_tokens += r.get('tokens', 0)

        if r['error']:
            errors += 1

        if (i + 1) % 50 == 0:
            elapsed = time.time() - t0
            speed = (i + 1) / elapsed
            eta = (len(df) - i - 1) / speed
            cost = total_tokens / 1_000_000 * 0.5  # approx $0.50/M tokens
            print(f"  [{i+1}/{len(df)}] "
                  f"{elapsed:.0f}s, ~{eta:.0f}s left, "
                  f"errors: {errors}, "
                  f"tokens: {total_tokens}, ~${cost:.3f}")

        # Small delay to avoid rate limiting
        time.sleep(0.1)

    total_time = time.time() - t0
    cost_est = total_tokens / 1_000_000 * 0.5

    print(f"\nTotal time: {total_time:.1f}s")
    print(f"Total tokens: {total_tokens}")
    print(f"Est. cost: ${cost_est:.3f}")
    print(f"Errors: {errors}/{len(df)}")

    # Evaluate
    y_true = df['sentiment'].values
    y_pred = [r['sentiment'] for r in results]
    y_pred_clean = [p if p in ['positive', 'negative', 'neutral'] else 'neutral'
                    for p in y_pred]

    valid_count = sum(1 for p in y_pred if p in ['positive', 'negative', 'neutral'])

    label_names = ['negative', 'neutral', 'positive']
    accuracy = accuracy_score(y_true, y_pred_clean)
    macro_f1 = f1_score(y_true, y_pred_clean, average='macro', labels=label_names)
    macro_prec = precision_score(y_true, y_pred_clean, average='macro', labels=label_names)
    macro_rec = recall_score(y_true, y_pred_clean, average='macro', labels=label_names)

    print("\n" + "=" * 60)
    print(f"RESULTS: {MODEL}")
    print("=" * 60)
    print(f"\nAccuracy:        {accuracy:.4f}")
    print(f"Macro F1:        {macro_f1:.4f}")
    print(f"Macro Precision: {macro_prec:.4f}")
    print(f"Macro Recall:    {macro_rec:.4f}")
    print(f"Valid preds:     {valid_count}/{len(df)}")

    print("\n--- Classification Report ---")
    print(classification_report(y_true, y_pred_clean,
                                target_names=label_names, digits=4))

    # Save
    summary = {
        'model': MODEL,
        'accuracy': round(accuracy, 4),
        'macro_f1': round(macro_f1, 4),
        'macro_precision': round(macro_prec, 4),
        'macro_recall': round(macro_rec, 4),
        'total_time_s': round(total_time, 1),
        'avg_time_per_review_s': round(total_time / len(df), 2),
        'total_tokens': total_tokens,
        'est_cost_usd': round(cost_est, 4),
        'valid_predictions': valid_count,
        'total_reviews': len(df),
        'errors': errors,
    }

    report = classification_report(y_true, y_pred_clean,
                                   target_names=label_names, output_dict=True)
    summary['per_class'] = {}
    for cls in label_names:
        summary['per_class'][cls] = {
            'precision': round(report[cls]['precision'], 4),
            'recall': round(report[cls]['recall'], 4),
            'f1': round(report[cls]['f1-score'], 4),
        }

    with open('results_gpt-3.5-turbo.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to results_gpt-3.5-turbo.json")

    pred_df = df.copy()
    pred_df['gpt35_pred'] = y_pred_clean
    pred_df['gpt35_topic'] = [r.get('topic', '') for r in results]
    pred_df['gpt35_reason'] = [r.get('reason', '') for r in results]
    pred_df.to_csv('predictions_gpt-3.5-turbo.csv', index=False)
    print("Predictions saved to predictions_gpt-3.5-turbo.csv")

    # Sample insights
    print("\n--- Sample Insights ---")
    for i, (_, row) in enumerate(df[df['sentiment'] == 'negative'].head(5).iterrows()):
        idx = row.name
        r = results[idx]
        print(f"\n[{i+1}] \"{row['review'][:80]}...\"")
        print(f"    -> {r['sentiment']} | {r.get('topic','')} | {r.get('reason','')[:70]}")


if __name__ == '__main__':
    main()
