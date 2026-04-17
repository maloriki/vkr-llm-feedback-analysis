"""
LLM Pipeline: эксперимент с Qwen 2.5 и DeepSeek через Ollama.
Тестирует на тех же 500 отзывах, что и baseline.

Использование:
  python 02_llm_pipeline.py --model qwen2.5:7b
  python 02_llm_pipeline.py --model deepseek-r1:7b
  python 02_llm_pipeline.py --model all
"""
import pandas as pd
import numpy as np
import json
import time
import argparse
import requests
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    classification_report
)

OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_PROMPT = """Ты — аналитик клиентской обратной связи. Твоя задача — определить тональность отзыва.

Правила:
1. Определи тональность: positive, negative или neutral
2. Выдели основную тему отзыва (1-3 слова)
3. Кратко объясни причину такой тональности (1 предложение)

Ответ СТРОГО в формате JSON:
{"sentiment": "positive|negative|neutral", "topic": "тема", "reason": "причина"}

Ничего кроме JSON не пиши."""


def query_ollama(model: str, review: str, timeout: int = 120) -> dict:
    """Send a single review to Ollama and parse response."""
    prompt = f"Определи тональность следующего отзыва:\n\n\"{review}\""

    payload = {
        "model": model,
        "prompt": prompt,
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 200,
        }
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        response_text = data.get("response", "")

        # Try to parse JSON from response
        # Handle cases where model wraps JSON in markdown
        text = response_text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        # Find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(text[start:end])
            sentiment = parsed.get("sentiment", "").lower().strip()
            # Normalize
            if sentiment in ["positive", "позитивный", "позитивная", "положительный", "положительная"]:
                sentiment = "positive"
            elif sentiment in ["negative", "негативный", "негативная", "отрицательный", "отрицательная"]:
                sentiment = "negative"
            elif sentiment in ["neutral", "нейтральный", "нейтральная"]:
                sentiment = "neutral"

            return {
                "sentiment": sentiment,
                "topic": parsed.get("topic", ""),
                "reason": parsed.get("reason", ""),
                "raw_response": response_text,
                "error": None
            }
        else:
            return {
                "sentiment": "",
                "topic": "",
                "reason": "",
                "raw_response": response_text,
                "error": "no_json_found"
            }

    except requests.exceptions.ConnectionError:
        return {"sentiment": "", "error": "connection_error",
                "raw_response": "", "topic": "", "reason": ""}
    except requests.exceptions.Timeout:
        return {"sentiment": "", "error": "timeout",
                "raw_response": "", "topic": "", "reason": ""}
    except Exception as e:
        return {"sentiment": "", "error": str(e),
                "raw_response": "", "topic": "", "reason": ""}


def run_experiment(model_name: str):
    """Run full experiment for one model."""
    print("=" * 60)
    print(f"LLM EXPERIMENT: {model_name}")
    print("=" * 60)

    # Load test set
    df = pd.read_csv('test_set_500.csv')
    print(f"Test set: {len(df)} reviews")
    print(f"Class distribution: {df['sentiment'].value_counts().to_dict()}")

    # Check Ollama connection
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m['name'] for m in r.json().get('models', [])]
        print(f"Ollama models available: {models}")
        if not any(model_name in m for m in models):
            print(f"\nWARNING: Model '{model_name}' not found!")
            print(f"Run: ollama pull {model_name}")
            return
    except Exception as e:
        print(f"\nERROR: Cannot connect to Ollama: {e}")
        print("Make sure Ollama is running (ollama serve)")
        return

    # Process reviews
    results = []
    errors = 0
    label_map = {'negative': 0, 'neutral': 1, 'positive': 2}

    t0 = time.time()
    for i, row in df.iterrows():
        review = row['review']
        # Truncate very long reviews
        if len(review) > 500:
            review = review[:500] + "..."

        result = query_ollama(model_name, review)
        results.append(result)

        if result['error']:
            errors += 1

        # Progress
        if (i + 1) % 25 == 0:
            elapsed = time.time() - t0
            speed = (i + 1) / elapsed
            eta = (len(df) - i - 1) / speed
            print(f"  [{i+1}/{len(df)}] "
                  f"{elapsed:.0f}s elapsed, "
                  f"~{eta:.0f}s remaining, "
                  f"errors: {errors}")

    total_time = time.time() - t0
    print(f"\nTotal time: {total_time:.1f}s")
    print(f"Avg per review: {total_time/len(df):.2f}s")
    print(f"Errors: {errors}/{len(df)}")

    # Evaluate
    y_true = df['sentiment'].values
    y_pred = [r['sentiment'] for r in results]

    # Handle unparseable responses
    valid_mask = [p in ['positive', 'negative', 'neutral'] for p in y_pred]
    valid_count = sum(valid_mask)
    print(f"Valid predictions: {valid_count}/{len(df)}")

    if valid_count < len(df) * 0.5:
        print("WARNING: Less than 50% valid predictions! Check model output.")
        # Print some examples of failed parses
        for i, r in enumerate(results[:10]):
            if r['error'] or r['sentiment'] not in ['positive', 'negative', 'neutral']:
                print(f"  Example [{i}]: {r['raw_response'][:100]}")

    # For evaluation, replace invalid predictions with 'neutral'
    y_pred_clean = [p if p in ['positive', 'negative', 'neutral'] else 'neutral'
                    for p in y_pred]

    label_names = ['negative', 'neutral', 'positive']

    accuracy = accuracy_score(y_true, y_pred_clean)
    macro_f1 = f1_score(y_true, y_pred_clean, average='macro',
                        labels=label_names)
    macro_precision = precision_score(y_true, y_pred_clean, average='macro',
                                      labels=label_names)
    macro_recall = recall_score(y_true, y_pred_clean, average='macro',
                                labels=label_names)

    print("\n" + "=" * 60)
    print(f"RESULTS: {model_name}")
    print("=" * 60)
    print(f"\nAccuracy:        {accuracy:.4f}")
    print(f"Macro F1:        {macro_f1:.4f}")
    print(f"Macro Precision: {macro_precision:.4f}")
    print(f"Macro Recall:    {macro_recall:.4f}")
    print(f"\nTotal time:      {total_time:.1f}s")
    print(f"Valid preds:     {valid_count}/{len(df)}")

    print("\n--- Classification Report ---")
    print(classification_report(y_true, y_pred_clean,
                                target_names=label_names, digits=4))

    # Save results
    safe_name = model_name.replace(":", "_").replace("/", "_")

    result_summary = {
        'model': model_name,
        'accuracy': round(accuracy, 4),
        'macro_f1': round(macro_f1, 4),
        'macro_precision': round(macro_precision, 4),
        'macro_recall': round(macro_recall, 4),
        'total_time_s': round(total_time, 1),
        'avg_time_per_review_s': round(total_time / len(df), 2),
        'valid_predictions': valid_count,
        'total_reviews': len(df),
        'errors': errors,
    }

    report = classification_report(y_true, y_pred_clean,
                                   target_names=label_names, output_dict=True)
    result_summary['per_class'] = {}
    for cls in label_names:
        result_summary['per_class'][cls] = {
            'precision': round(report[cls]['precision'], 4),
            'recall': round(report[cls]['recall'], 4),
            'f1': round(report[cls]['f1-score'], 4),
        }

    with open(f'results_{safe_name}.json', 'w', encoding='utf-8') as f:
        json.dump(result_summary, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to results_{safe_name}.json")

    # Save detailed predictions with topics & reasons
    pred_df = df.copy()
    pred_df[f'{safe_name}_pred'] = y_pred_clean
    pred_df[f'{safe_name}_topic'] = [r.get('topic', '') for r in results]
    pred_df[f'{safe_name}_reason'] = [r.get('reason', '') for r in results]
    pred_df.to_csv(f'predictions_{safe_name}.csv', index=False)
    print(f"Predictions saved to predictions_{safe_name}.csv")

    # Show sample insights
    print("\n--- Sample Insights (первые 5 negative) ---")
    for i, (_, row) in enumerate(df[df['sentiment'] == 'negative'].head(5).iterrows()):
        idx = row.name
        r = results[idx]
        print(f"\n[{i+1}] Review: {row['review'][:80]}...")
        print(f"    Pred: {r['sentiment']} | Topic: {r.get('topic','')} | "
              f"Reason: {r.get('reason','')[:60]}")

    return result_summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LLM sentiment experiment')
    parser.add_argument('--model', type=str, default='qwen2.5:7b',
                        help='Ollama model name or "all"')
    args = parser.parse_args()

    if args.model == 'all':
        all_models = ['qwen2.5:7b', 'deepseek-r1:7b']
        all_results = []
        for m in all_models:
            r = run_experiment(m)
            if r:
                all_results.append(r)
        # Print comparison
        if all_results:
            print("\n" + "=" * 60)
            print("COMPARISON TABLE")
            print("=" * 60)
            header = f"{'Model':<25} {'Acc':>7} {'F1':>7} {'Prec':>7} {'Rec':>7} {'Time':>8}"
            print(header)
            print("-" * len(header))
            for r in all_results:
                print(f"{r['model']:<25} "
                      f"{r['accuracy']:>7.4f} "
                      f"{r['macro_f1']:>7.4f} "
                      f"{r['macro_precision']:>7.4f} "
                      f"{r['macro_recall']:>7.4f} "
                      f"{r['total_time_s']:>7.1f}s")
    else:
        run_experiment(args.model)
