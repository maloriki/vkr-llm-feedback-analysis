"""
YandexGPT Classifier (zero-shot) + Embeddings + LogReg baseline.
Two experiments in one script.
"""
import pandas as pd
import numpy as np
import json
import time
import requests
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    classification_report
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

import os
FOLDER_ID = os.environ.get('YANDEX_FOLDER_ID', '')
API_KEY = os.environ.get('YANDEX_API_KEY', '')

if not FOLDER_ID or not API_KEY:
    raise SystemExit(
        'ERROR: Set YANDEX_FOLDER_ID and YANDEX_API_KEY environment variables'
    )
HEADERS = {
    'Authorization': f'Api-Key {API_KEY}',
    'Content-Type': 'application/json',
}

LABELS = ['negative', 'neutral', 'positive']


# ============================================================
# PART 1: Zero-shot classifier via YandexGPT classify endpoint
# ============================================================
def run_classifier_experiment():
    print("=" * 60)
    print("EXPERIMENT: YandexGPT Zero-Shot Classifier")
    print("=" * 60)

    url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/fewShotTextClassification'

    df = pd.read_csv('test_set_500.csv')
    print(f"Test set: {len(df)} reviews")

    results = []
    errors = 0
    t0 = time.time()

    for i, row in df.iterrows():
        review = row['review'][:400]

        body = {
            'modelUri': f'cls://{FOLDER_ID}/yandexgpt',
            'taskDescription': 'Определи тональность клиентского отзыва о товаре или доставке.',
            'labels': [
                {'name': 'negative', 'description': 'Негативный отзыв: жалоба, недовольство, проблема'},
                {'name': 'neutral', 'description': 'Нейтральный отзыв: констатация факта, без эмоций'},
                {'name': 'positive', 'description': 'Позитивный отзыв: благодарность, удовлетворение'},
            ],
            'text': review,
        }

        try:
            r = requests.post(url, headers=HEADERS, json=body, timeout=30)

            if r.status_code == 429:
                time.sleep(2)
                r = requests.post(url, headers=HEADERS, json=body, timeout=30)

            data = r.json()

            if 'predictions' in data:
                preds = data['predictions']
                # Find label with highest confidence
                best = max(preds, key=lambda x: float(x.get('confidence', 0)))
                results.append({
                    'sentiment': best['label'],
                    'confidence': float(best['confidence']),
                    'error': None,
                })
            else:
                results.append({
                    'sentiment': '',
                    'confidence': 0,
                    'error': data.get('error', {}).get('message', str(data)[:200]),
                })
                errors += 1

        except Exception as e:
            results.append({'sentiment': '', 'confidence': 0, 'error': str(e)})
            errors += 1

        if (i + 1) % 50 == 0:
            elapsed = time.time() - t0
            eta = (len(df) - i - 1) / ((i + 1) / elapsed)
            print(f"  [{i+1}/{len(df)}] {elapsed:.0f}s, ~{eta:.0f}s left, errors: {errors}")

        time.sleep(0.1)

    total_time = time.time() - t0
    y_true = df['sentiment'].values
    y_pred = [r['sentiment'] if r['sentiment'] in LABELS else 'neutral' for r in results]
    valid = sum(1 for r in results if r['sentiment'] in LABELS)

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average='macro', labels=LABELS)
    prec = precision_score(y_true, y_pred, average='macro', labels=LABELS)
    rec = recall_score(y_true, y_pred, average='macro', labels=LABELS)

    print(f"\n{'='*60}")
    print(f"RESULTS: YandexGPT Classifier (zero-shot)")
    print(f"{'='*60}")
    print(f"Accuracy:        {acc:.4f}")
    print(f"Macro F1:        {f1:.4f}")
    print(f"Macro Precision: {prec:.4f}")
    print(f"Macro Recall:    {rec:.4f}")
    print(f"Valid preds:     {valid}/{len(df)}")
    print(f"Time:            {total_time:.1f}s")
    print(classification_report(y_true, y_pred, target_names=LABELS, digits=4))

    summary = {
        'model': 'YandexGPT Classifier (zero-shot)',
        'accuracy': round(acc, 4),
        'macro_f1': round(f1, 4),
        'macro_precision': round(prec, 4),
        'macro_recall': round(rec, 4),
        'total_time_s': round(total_time, 1),
        'valid_predictions': valid,
        'total_reviews': len(df),
        'errors': errors,
    }
    report = classification_report(y_true, y_pred, target_names=LABELS, output_dict=True)
    summary['per_class'] = {c: {
        'precision': round(report[c]['precision'], 4),
        'recall': round(report[c]['recall'], 4),
        'f1': round(report[c]['f1-score'], 4),
    } for c in LABELS}

    with open('results_yandex_classifier.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("Saved to results_yandex_classifier.json")
    return summary


# ============================================================
# PART 2: Embeddings + Logistic Regression
# ============================================================
def get_embedding(text):
    url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding'
    body = {
        'modelUri': f'emb://{FOLDER_ID}/text-search-doc/latest',
        'text': text[:400],
    }
    try:
        r = requests.post(url, headers=HEADERS, json=body, timeout=30)
        if r.status_code == 429:
            time.sleep(2)
            r = requests.post(url, headers=HEADERS, json=body, timeout=30)
        data = r.json()
        if 'embedding' in data:
            return data['embedding']
        return None
    except:
        return None


def run_embeddings_experiment():
    print("\n" + "=" * 60)
    print("EXPERIMENT: YandexGPT Embeddings + Logistic Regression")
    print("=" * 60)

    # Load full dataset for train/test
    df_full = pd.read_csv('rureviews.csv', sep='\t')
    df_full['sentiment'] = df_full['sentiment'].replace({'neautral': 'neutral'})

    # Use 300 for training embeddings, 200 for test
    train_sample = df_full.sample(300, random_state=42)
    test_df = pd.read_csv('test_set_500.csv').head(200)  # subset for speed

    print(f"Train: {len(train_sample)}, Test: {len(test_df)}")
    print("Getting train embeddings...")

    # Get train embeddings
    train_embeddings = []
    train_labels = []
    t0 = time.time()

    for i, row in train_sample.iterrows():
        emb = get_embedding(row['review'])
        if emb:
            train_embeddings.append(emb)
            train_labels.append(row['sentiment'])
        if (len(train_embeddings)) % 50 == 0:
            print(f"  Train: {len(train_embeddings)}/{len(train_sample)}")
        time.sleep(0.1)

    print(f"Train embeddings: {len(train_embeddings)} ({time.time()-t0:.0f}s)")
    print("Getting test embeddings...")

    # Get test embeddings
    test_embeddings = []
    test_labels = []
    t1 = time.time()

    for i, row in test_df.iterrows():
        emb = get_embedding(row['review'])
        if emb:
            test_embeddings.append(emb)
            test_labels.append(row['sentiment'])
        if (len(test_embeddings)) % 50 == 0:
            print(f"  Test: {len(test_embeddings)}/{len(test_df)}")
        time.sleep(0.1)

    total_time = time.time() - t0
    print(f"Test embeddings: {len(test_embeddings)} ({time.time()-t1:.0f}s)")

    # Train LogReg
    X_train = np.array(train_embeddings)
    y_train = np.array(train_labels)
    X_test = np.array(test_embeddings)
    y_test = np.array(test_labels)

    print(f"Embedding dim: {X_train.shape[1]}")
    print("Training Logistic Regression...")

    clf = LogisticRegression(max_iter=1000, random_state=42, C=1.0)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='macro', labels=LABELS)
    prec = precision_score(y_test, y_pred, average='macro', labels=LABELS)
    rec = recall_score(y_test, y_pred, average='macro', labels=LABELS)

    print(f"\n{'='*60}")
    print(f"RESULTS: YandexGPT Embeddings + LogReg")
    print(f"{'='*60}")
    print(f"Accuracy:        {acc:.4f}")
    print(f"Macro F1:        {f1:.4f}")
    print(f"Macro Precision: {prec:.4f}")
    print(f"Macro Recall:    {rec:.4f}")
    print(f"Train size:      {len(train_embeddings)}")
    print(f"Test size:       {len(test_embeddings)}")
    print(f"Time:            {total_time:.1f}s")
    print(classification_report(y_test, y_pred, target_names=LABELS, digits=4))

    summary = {
        'model': 'YandexGPT Embeddings + LogReg',
        'accuracy': round(acc, 4),
        'macro_f1': round(f1, 4),
        'macro_precision': round(prec, 4),
        'macro_recall': round(rec, 4),
        'total_time_s': round(total_time, 1),
        'train_size': len(train_embeddings),
        'test_size': len(test_embeddings),
        'embedding_dim': X_train.shape[1],
    }
    report = classification_report(y_test, y_pred, target_names=LABELS, output_dict=True)
    summary['per_class'] = {c: {
        'precision': round(report[c]['precision'], 4),
        'recall': round(report[c]['recall'], 4),
        'f1': round(report[c]['f1-score'], 4),
    } for c in LABELS}

    with open('results_yandex_embeddings.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("Saved to results_yandex_embeddings.json")
    return summary


# ============================================================
# RUN BOTH
# ============================================================
if __name__ == '__main__':
    r1 = run_classifier_experiment()
    r2 = run_embeddings_experiment()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Model':<40} {'Acc':>7} {'F1':>7}")
    print("-" * 56)
    print(f"{'YandexGPT Classifier (zero-shot)':<40} {r1['accuracy']:>7.4f} {r1['macro_f1']:>7.4f}")
    print(f"{'YandexGPT Embeddings + LogReg':<40} {r2['accuracy']:>7.4f} {r2['macro_f1']:>7.4f}")
