import json
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from backend_utils import engineered_feature_columns, transform_dataframe


DATA_FOLDER = "data"
MODEL_FOLDER = "models"
GENUINE_FILE = os.path.join(DATA_FOLDER, "genuine.csv")
IMPOSTOR_FILE = os.path.join(DATA_FOLDER, "impostor.csv")
MODEL_FILE = os.path.join(MODEL_FOLDER, "model.pkl")
METRICS_FILE = os.path.join(MODEL_FOLDER, "metrics.json")


def load_dataset() -> pd.DataFrame:
    if not os.path.exists(GENUINE_FILE):
        raise FileNotFoundError("genuine.csv not found. Run capture_data.py first.")
    if not os.path.exists(IMPOSTOR_FILE):
        raise FileNotFoundError("impostor.csv not found. Run capture_data.py first.")

    genuine_df = pd.read_csv(GENUINE_FILE)
    impostor_df = pd.read_csv(IMPOSTOR_FILE)
    return pd.concat([genuine_df, impostor_df], ignore_index=True)


def build_candidate_models() -> dict[str, object]:
    return {
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
        "Extra Trees": ExtraTreesClassifier(n_estimators=300, random_state=42),
        "SVM": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("classifier", SVC(kernel="rbf", probability=True, random_state=42)),
            ]
        ),
    }


def main() -> None:
    os.makedirs(MODEL_FOLDER, exist_ok=True)

    df = load_dataset()
    if len(df) < 10:
        raise ValueError("Dataset is too small. Record more samples before training.")

    feature_df = transform_dataframe(df)
    X = feature_df.drop(columns=["label"])
    y = feature_df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=y,
    )

    candidate_models = build_candidate_models()
    trained_models = {}
    model_scores = {}
    cv_scores = {}
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for model_name, model in candidate_models.items():
        scores = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
        cv_scores[model_name] = float(scores.mean())
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        model_scores[model_name] = accuracy_score(y_test, predictions)
        trained_models[model_name] = model

    best_model_name = max(cv_scores, key=cv_scores.get)
    model = trained_models[best_model_name]

    # Fit the selected model again on the full dataset for stronger final deployment.
    model.fit(X, y)

    evaluation_model = trained_models[best_model_name]
    predictions = evaluation_model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, zero_division=0)
    recall = recall_score(y_test, predictions, zero_division=0)
    f1 = f1_score(y_test, predictions, zero_division=0)

    metrics = {
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "best_model": best_model_name,
        "model_comparison": {name: round(float(score), 4) for name, score in model_scores.items()},
        "cross_validation_accuracy": {name: round(float(score), 4) for name, score in cv_scores.items()},
        "feature_count": len(engineered_feature_columns()),
        "decision_threshold": 0.5,
    }

    model_bundle = {
        "model": model,
        "feature_columns": engineered_feature_columns(),
        "best_model": best_model_name,
        "decision_threshold": 0.5,
        "target_text": "secure123",
    }

    joblib.dump(model_bundle, MODEL_FILE)
    with open(METRICS_FILE, "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=4)

    print("Model training completed successfully.")
    print(f"Model saved as: {MODEL_FILE}")
    print(f"Metrics saved as: {METRICS_FILE}")
    print(f"Best model selected: {best_model_name}")
    print(f"Total engineered features: {len(engineered_feature_columns())}")
    print("\nModel comparison:")
    for model_name, score in model_scores.items():
        print(f"- {model_name}: {score * 100:.2f}%")
    print("\nCross-validation accuracy:")
    for model_name, score in cv_scores.items():
        print(f"- {model_name}: {score * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, predictions, target_names=["Impostor", "Genuine"], zero_division=0))
    print(f"Accuracy: {metrics['accuracy'] * 100:.2f}%")


if __name__ == "__main__":
    main()
