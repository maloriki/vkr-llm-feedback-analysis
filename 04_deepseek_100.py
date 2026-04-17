"""DeepSeek R1 7B on 100 reviews subset."""
import pandas as pd, json, time, requests
from sklearn.metrics import accuracy_score, f1_score, classification_report

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "deepseek-r1:7b"
SYSTEM = """Ты — аналитик клиентской обратной связи. Определи тональность отзыва.
Ответ СТРОГО в формате JSON: {"sentiment": "positive|negative|neutral", "topic": "тема", "reason": "причина"}
Ничего кроме JSON не пиши. Не пиши рассуждения."""

df = pd.read_csv('test_set_100.csv')
print(f"DeepSeek R1 7B | {len(df)} reviews")

results = []
t0 = time.time()

for i, row in df.iterrows():
    review = row['review'][:300]
    try:
        r = requests.post(OLLAMA_URL, json={
            'model': MODEL, 'stream': False,
            'system': SYSTEM,
            'prompt': f'Определи тональность: "{review}"',
            'options': {'temperature': 0.1, 'num_predict': 300}
        }, timeout=300)
        text = r.json().get('response', '')
        # Remove <think> blocks
        if '</think>' in text:
            text = text.split('</think>')[-1].strip()
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            parsed = json.loads(text[start:end])
            s = parsed.get('sentiment', '').lower().strip()
            norm = {'positive':'positive','позитивный':'positive','положительный':'positive',
                    'negative':'negative','негативный':'negative','отрицательный':'negative',
                    'neutral':'neutral','нейтральный':'neutral'}
            results.append({'sentiment': norm.get(s, s), 'topic': parsed.get('topic',''),
                           'reason': parsed.get('reason','')})
        else:
            results.append({'sentiment': '', 'topic': '', 'reason': ''})
    except Exception as e:
        results.append({'sentiment': '', 'topic': '', 'reason': ''})

    if (i+1) % 10 == 0:
        elapsed = time.time() - t0
        print(f"  [{i+1}/{len(df)}] {elapsed:.0f}s, ~{(len(df)-i-1)/(i+1)*elapsed:.0f}s left")

total = time.time() - t0
y_true = df['sentiment'].values
y_pred = [r['sentiment'] if r['sentiment'] in ['positive','negative','neutral'] else 'neutral' for r in results]
valid = sum(1 for r in results if r['sentiment'] in ['positive','negative','neutral'])
labels = ['negative','neutral','positive']

acc = accuracy_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred, average='macro', labels=labels)

print(f"\nRESULTS: {MODEL}")
print(f"Accuracy: {acc:.4f} | Macro F1: {f1:.4f} | Valid: {valid}/{len(df)} | Time: {total:.0f}s")
print(classification_report(y_true, y_pred, target_names=labels, digits=4))

summary = {'model': MODEL, 'accuracy': round(acc,4), 'macro_f1': round(f1,4),
           'total_time_s': round(total,1), 'valid_predictions': valid,
           'total_reviews': len(df), 'test_subset': 100}
report = classification_report(y_true, y_pred, target_names=labels, output_dict=True)
summary['per_class'] = {c: {'precision': round(report[c]['precision'],4),
    'recall': round(report[c]['recall'],4), 'f1': round(report[c]['f1-score'],4)} for c in labels}

with open('results_deepseek-r1_7b.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"Saved to results_deepseek-r1_7b.json")
