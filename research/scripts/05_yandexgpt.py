"""YandexGPT Pro experiment on 500 reviews."""
import os
import pandas as pd
import json
import time
import requests
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    classification_report
)

FOLDER_ID = os.environ.get('YANDEX_FOLDER_ID', '')
API_KEY = os.environ.get('YANDEX_API_KEY', '')

if not FOLDER_ID or not API_KEY:
    raise SystemExit(
        'ERROR: Set YANDEX_FOLDER_ID and YANDEX_API_KEY environment variables'
    )
MODEL_URI = f'gpt://{FOLDER_ID}/yandexgpt'
URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
HEADERS = {
    'Authorization': f'Api-Key {API_KEY}',
    'Content-Type': 'application/json',
}

SYSTEM = """Ты — аналитик клиентской обратной связи в e-commerce логистической компании.

Задача: определи тональность клиентского отзыва.

Инструкция:
1. Определи общую тональность отзыва: positive, negative или neutral.
2. Выдели основную тему отзыва (1–3 слова).
3. Кратко (1 предложение) объясни причину тональности.

Формат ответа — строго JSON, без дополнительного текста:
{"sentiment": "positive|negative|neutral", "topic": "тема", "reason": "краткое обоснование"}"""


def query_yandex(review):
    body = {
        'modelUri': MODEL_URI,
        'completionOptions': {'stream': False, 'temperature': 0.1, 'maxTokens': 200},
        'messages': [
            {'role': 'system', 'text': SYSTEM},
            {'role': 'user', 'text': f'Определи тональность следующего отзыва:\n\n"{review}"'}
        ]
    }
    try:
        r = requests.post(URL, headers=HEADERS, json=body, timeout=60)
        if r.status_code == 429:
            time.sleep(2)
            r = requests.post(URL, headers=HEADERS, json=body, timeout=60)

        data = r.json()
        if 'result' not in data:
            return {'sentiment': '', 'topic': '', 'reason': '',
                    'error': data.get('error', {}).get('message', 'unknown'),
                    'tokens': 0}

        text = data['result']['alternatives'][0]['message']['text'].strip()
        tokens = int(data['result']['usage'].get('totalTokens', 0))

        # Parse JSON
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            parsed = json.loads(text[start:end])
            s = parsed.get('sentiment', '').lower().strip()
            norm = {
                'positive': 'positive', 'позитивный': 'positive',
                'позитивная': 'positive', 'положительный': 'positive',
                'положительная': 'positive',
                'negative': 'negative', 'негативный': 'negative',
                'негативная': 'negative', 'отрицательный': 'negative',
                'отрицательная': 'negative',
                'neutral': 'neutral', 'нейтральный': 'neutral',
                'нейтральная': 'neutral',
            }
            return {
                'sentiment': norm.get(s, s),
                'topic': parsed.get('topic', ''),
                'reason': parsed.get('reason', ''),
                'error': None,
                'tokens': tokens,
            }
        return {'sentiment': '', 'topic': '', 'reason': '',
                'error': 'no_json', 'tokens': tokens}

    except Exception as e:
        return {'sentiment': '', 'topic': '', 'reason': '',
                'error': str(e), 'tokens': 0}


# ===== MAIN =====
print("=" * 60)
print("LLM EXPERIMENT: YandexGPT Pro")
print("=" * 60)

df = pd.read_csv('test_set_500.csv')
print(f"Test set: {len(df)} reviews")

results = []
errors = 0
total_tokens = 0
t0 = time.time()

for i, row in df.iterrows():
    review = row['review'][:400]
    r = query_yandex(review)
    results.append(r)
    total_tokens += r.get('tokens', 0)

    if r['error']:
        errors += 1

    if (i + 1) % 50 == 0:
        elapsed = time.time() - t0
        speed = (i + 1) / elapsed
        eta = (len(df) - i - 1) / speed
        cost = total_tokens / 1000 * 1.2  # ~1.2 rub/1000 tokens (Pro)
        print(f"  [{i+1}/{len(df)}] {elapsed:.0f}s, ~{eta:.0f}s left, "
              f"errors: {errors}, tokens: {total_tokens}, ~{cost:.2f} rub")

    time.sleep(0.15)  # rate limit

total_time = time.time() - t0
cost_rub = total_tokens / 1000 * 1.2

print(f"\nTotal time: {total_time:.1f}s")
print(f"Total tokens: {total_tokens}")
print(f"Est. cost: {cost_rub:.2f} rub")
print(f"Errors: {errors}/{len(df)}")

# Evaluate
y_true = df['sentiment'].values
y_pred = [r['sentiment'] if r['sentiment'] in ['positive', 'negative', 'neutral']
          else 'neutral' for r in results]
valid = sum(1 for r in results if r['sentiment'] in ['positive', 'negative', 'neutral'])

labels = ['negative', 'neutral', 'positive']
acc = accuracy_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred, average='macro', labels=labels)
prec = precision_score(y_true, y_pred, average='macro', labels=labels)
rec = recall_score(y_true, y_pred, average='macro', labels=labels)

print("\n" + "=" * 60)
print("RESULTS: YandexGPT Pro")
print("=" * 60)
print(f"\nAccuracy:        {acc:.4f}")
print(f"Macro F1:        {f1:.4f}")
print(f"Macro Precision: {prec:.4f}")
print(f"Macro Recall:    {rec:.4f}")
print(f"Valid preds:     {valid}/{len(df)}")

print("\n--- Classification Report ---")
print(classification_report(y_true, y_pred, target_names=labels, digits=4))

# Save
summary = {
    'model': 'YandexGPT Pro',
    'accuracy': round(acc, 4),
    'macro_f1': round(f1, 4),
    'macro_precision': round(prec, 4),
    'macro_recall': round(rec, 4),
    'total_time_s': round(total_time, 1),
    'avg_time_per_review_s': round(total_time / len(df), 2),
    'total_tokens': total_tokens,
    'est_cost_rub': round(cost_rub, 2),
    'valid_predictions': valid,
    'total_reviews': len(df),
    'errors': errors,
}

report = classification_report(y_true, y_pred, target_names=labels, output_dict=True)
summary['per_class'] = {}
for cls in labels:
    summary['per_class'][cls] = {
        'precision': round(report[cls]['precision'], 4),
        'recall': round(report[cls]['recall'], 4),
        'f1': round(report[cls]['f1-score'], 4),
    }

with open('results_yandexgpt_pro.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"\nResults saved to results_yandexgpt_pro.json")

pred_df = df.copy()
pred_df['yandexgpt_pred'] = y_pred
pred_df['yandexgpt_topic'] = [r.get('topic', '') for r in results]
pred_df['yandexgpt_reason'] = [r.get('reason', '') for r in results]
pred_df.to_csv('predictions_yandexgpt_pro.csv', index=False)
print("Predictions saved to predictions_yandexgpt_pro.csv")
