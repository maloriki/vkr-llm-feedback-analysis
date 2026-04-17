"""
Baseline: TF-IDF + XGBoost.

Обучается на ~89K отзывов из RuReviews, тестируется на 500.
Результаты метрик сохраняются в results_tfidf_xgboost.json,
предсказания — в predictions_tfidf_xgboost.csv.
"""
import json
import time

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    f1_score, precision_score, recall_score,
)
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

LABELS = ["negative", "neutral", "positive"]


def main():
    print("=== TF-IDF + XGBoost ===\n")

    # в датасете у neutral опечатка — "neautral"
    df = pd.read_csv("rureviews.csv", sep="\t")
    df["sentiment"] = df["sentiment"].replace({"neautral": "neutral"})
    label_map = {lab: i for i, lab in enumerate(LABELS)}
    df["label"] = df["sentiment"].map(label_map)

    print(f"Всего отзывов: {len(df)}")
    print(df["sentiment"].value_counts().to_string(), "\n")

    X_tr, X_te, y_tr, y_te = train_test_split(
        df["review"].values, df["label"].values,
        test_size=500, random_state=42, stratify=df["label"].values,
    )
    print(f"Train: {len(X_tr)} | Test: {len(X_te)}")

    # сохраняем тестовую выборку — её же прогоняем через LLM
    pd.DataFrame({
        "review": X_te,
        "label": y_te,
        "sentiment": [LABELS[i] for i in y_te],
    }).to_csv("test_set_500.csv", index=False)

    print("\n--- TF-IDF ---")
    t0 = time.time()
    tfidf = TfidfVectorizer(
        max_features=50000,
        ngram_range=(1, 2),
        min_df=3,
        max_df=0.95,
        sublinear_tf=True,
    )
    X_tr_v = tfidf.fit_transform(X_tr)
    X_te_v = tfidf.transform(X_te)
    print(f"Словарь: {len(tfidf.vocabulary_)} | {time.time()-t0:.1f}s")

    print("\n--- XGBoost ---")
    t0 = time.time()
    clf = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_tr_v, y_tr)
    train_time = time.time() - t0
    print(f"Обучение: {train_time:.1f}s")

    t0 = time.time()
    y_pred = clf.predict(X_te_v)
    infer_time = time.time() - t0

    # --- метрики ---
    acc = accuracy_score(y_te, y_pred)
    f1 = f1_score(y_te, y_pred, average="macro")
    prec = precision_score(y_te, y_pred, average="macro")
    rec = recall_score(y_te, y_pred, average="macro")

    print(f"\nAccuracy = {acc:.4f}  |  Macro F1 = {f1:.4f}")
    print(f"Precision = {prec:.4f}  |  Recall = {rec:.4f}")
    print(f"Inference: {infer_time:.3f}s на {len(X_te)} отзывов\n")

    print(classification_report(y_te, y_pred, target_names=LABELS, digits=4))

    cm = confusion_matrix(y_te, y_pred)
    print("Confusion matrix:")
    print(pd.DataFrame(cm, index=LABELS, columns=LABELS).to_string())

    # --- сохраняем результаты ---
    report = classification_report(y_te, y_pred, target_names=LABELS, output_dict=True)
    results = {
        "model": "TF-IDF + XGBoost",
        "accuracy": round(acc, 4),
        "macro_f1": round(f1, 4),
        "macro_precision": round(prec, 4),
        "macro_recall": round(rec, 4),
        "train_time_s": round(train_time, 1),
        "inference_time_s": round(infer_time, 3),
        "test_size": len(X_te),
        "per_class": {
            cls: {
                "precision": round(report[cls]["precision"], 4),
                "recall": round(report[cls]["recall"], 4),
                "f1": round(report[cls]["f1-score"], 4),
            }
            for cls in LABELS
        },
    }
    with open("results_tfidf_xgboost.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    pd.DataFrame({
        "review": X_te,
        "sentiment": [LABELS[i] for i in y_te],
        "tfidf_xgb_pred": [LABELS[i] for i in y_pred],
    }).to_csv("predictions_tfidf_xgboost.csv", index=False)

    print("\nСохранено: results_tfidf_xgboost.json, predictions_tfidf_xgboost.csv")


if __name__ == "__main__":
    main()
