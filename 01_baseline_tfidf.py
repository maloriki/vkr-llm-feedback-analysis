"""
Baseline 1: TF-IDF + XGBoost для классификации тональности.
Запускается без API ключей, полностью локально.
"""
import pandas as pd
import numpy as np
import json
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    classification_report, confusion_matrix
)
from xgboost import XGBClassifier

# ===== 1. Load data =====
print("=" * 60)
print("BASELINE 1: TF-IDF + XGBoost")
print("=" * 60)

df = pd.read_csv('rureviews.csv', sep='\t')
df['sentiment'] = df['sentiment'].replace({'neautral': 'neutral'})  # fix typo

label_map = {'negative': 0, 'neutral': 1, 'positive': 2}
label_names = ['negative', 'neutral', 'positive']
df['label'] = df['sentiment'].map(label_map)

print(f"\nTotal reviews: {len(df)}")
print(f"Class distribution:\n{df['sentiment'].value_counts().to_string()}")

# ===== 2. Train/Test split =====
# Use 500 for test (same as LLM experiment), rest for train
X = df['review'].values
y = df['label'].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=500, random_state=42, stratify=y
)
print(f"\nTrain size: {len(X_train)}")
print(f"Test size: {len(X_test)}")

# Save test set for LLM experiments
test_df = pd.DataFrame({'review': X_test, 'label': y_test})
test_df['sentiment'] = test_df['label'].map({v: k for k, v in label_map.items()})
test_df.to_csv('test_set_500.csv', index=False)
print("Test set saved to test_set_500.csv")

# ===== 3. TF-IDF vectorization =====
print("\n--- TF-IDF Vectorization ---")
t0 = time.time()

tfidf = TfidfVectorizer(
    max_features=50000,
    ngram_range=(1, 2),
    min_df=3,
    max_df=0.95,
    sublinear_tf=True
)

X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf = tfidf.transform(X_test)

print(f"Vocabulary size: {len(tfidf.vocabulary_)}")
print(f"TF-IDF time: {time.time() - t0:.1f}s")

# ===== 4. XGBoost training =====
print("\n--- XGBoost Training ---")
t0 = time.time()

xgb = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.1,
    eval_metric='mlogloss',
    random_state=42,
    n_jobs=-1
)

xgb.fit(X_train_tfidf, y_train)
train_time = time.time() - t0
print(f"Training time: {train_time:.1f}s")

# ===== 5. Prediction =====
t0 = time.time()
y_pred = xgb.predict(X_test_tfidf)
predict_time = time.time() - t0

# ===== 6. Evaluation =====
print("\n" + "=" * 60)
print("RESULTS: TF-IDF + XGBoost")
print("=" * 60)

accuracy = accuracy_score(y_test, y_pred)
macro_f1 = f1_score(y_test, y_pred, average='macro')
macro_precision = precision_score(y_test, y_pred, average='macro')
macro_recall = recall_score(y_test, y_pred, average='macro')

print(f"\nAccuracy:        {accuracy:.4f}")
print(f"Macro F1:        {macro_f1:.4f}")
print(f"Macro Precision: {macro_precision:.4f}")
print(f"Macro Recall:    {macro_recall:.4f}")

print(f"\nTraining time:   {train_time:.1f}s")
print(f"Inference time:  {predict_time:.3f}s (for {len(X_test)} reviews)")

print("\n--- Classification Report ---")
print(classification_report(y_test, y_pred, target_names=label_names, digits=4))

print("--- Confusion Matrix ---")
cm = confusion_matrix(y_test, y_pred)
print(pd.DataFrame(cm, index=label_names, columns=label_names).to_string())

# ===== 7. Save results =====
results = {
    'model': 'TF-IDF + XGBoost',
    'accuracy': round(accuracy, 4),
    'macro_f1': round(macro_f1, 4),
    'macro_precision': round(macro_precision, 4),
    'macro_recall': round(macro_recall, 4),
    'train_time_s': round(train_time, 1),
    'inference_time_s': round(predict_time, 3),
    'test_size': len(X_test),
    'per_class': {}
}

report = classification_report(y_test, y_pred, target_names=label_names,
                                output_dict=True)
for cls in label_names:
    results['per_class'][cls] = {
        'precision': round(report[cls]['precision'], 4),
        'recall': round(report[cls]['recall'], 4),
        'f1': round(report[cls]['f1-score'], 4),
    }

with open('results_tfidf_xgboost.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\nResults saved to results_tfidf_xgboost.json")

# Save predictions for comparison
pred_df = test_df.copy()
pred_df['tfidf_xgb_pred'] = [label_names[p] for p in y_pred]
pred_df.to_csv('predictions_tfidf_xgboost.csv', index=False)
print("Predictions saved to predictions_tfidf_xgboost.csv")
