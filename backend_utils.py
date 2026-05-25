import csv
import hashlib
import json
import os
import sqlite3
from datetime import datetime
from typing import Any, List

import joblib
import numpy as np
import pandas as pd


TARGET_TEXT = "secure123"
MODEL_FILE = os.path.join("models", "model.pkl")
AUTH_LOG_FILE = os.path.join("data", "auth_log.csv")
USER_PROFILES_DIR = os.path.join("data", "user_profiles")
USER_SUMMARIES_DIR = os.path.join("models", "user_profiles")
DATABASE_FILE = os.path.join("data", "security_system.db")
DEFAULT_SETTINGS = {
    "decision_threshold": "0.55",
    "max_failed_attempts": "3",
    "cooldown_seconds": "10",
    "email_notifications": "disabled",
}


def raw_hold_columns() -> List[str]:
    return [f"hold_{index + 1}" for index in range(len(TARGET_TEXT))]


def engineered_feature_columns() -> List[str]:
    hold_cols = raw_hold_columns()
    flight_cols = [f"flight_{index + 1}" for index in range(len(TARGET_TEXT) - 1)]
    summary_cols = [
        "hold_mean",
        "hold_std",
        "hold_min",
        "hold_max",
        "hold_range",
        "hold_sum",
        "first_last_ratio",
        "stability_score",
    ]
    return hold_cols + flight_cols + summary_cols


def build_feature_vector(hold_times: List[float]) -> dict[str, float]:
    if len(hold_times) != len(TARGET_TEXT):
        raise ValueError("Hold time sample length does not match the target text.")

    holds = np.array(hold_times, dtype=float)
    flights = np.diff(holds)
    feature_map = {f"hold_{index + 1}": float(value) for index, value in enumerate(holds)}
    feature_map.update({f"flight_{index + 1}": float(value) for index, value in enumerate(flights)})

    hold_mean = float(np.mean(holds))
    hold_std = float(np.std(holds))
    hold_min = float(np.min(holds))
    hold_max = float(np.max(holds))
    hold_sum = float(np.sum(holds))
    feature_map.update(
        {
            "hold_mean": hold_mean,
            "hold_std": hold_std,
            "hold_min": hold_min,
            "hold_max": hold_max,
            "hold_range": hold_max - hold_min,
            "hold_sum": hold_sum,
            "first_last_ratio": float(holds[0] / (holds[-1] + 1e-6)),
            "stability_score": float(1 / (1 + hold_std)),
        }
    )
    return feature_map


def transform_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    records = [build_feature_vector(row[raw_hold_columns()].tolist()) for _, row in df.iterrows()]
    feature_df = pd.DataFrame(records)
    if "label" in df.columns:
        feature_df["label"] = df["label"].values
    return feature_df


def sanitize_username(username: str) -> str:
    sanitized = "".join(character.lower() for character in username if character.isalnum() or character in {"_", "-"})
    return sanitized.strip("_-")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT,
                sample_count INTEGER DEFAULT 0,
                threshold REAL DEFAULT 0.55,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                username TEXT,
                result TEXT,
                confidence REAL,
                genuine_probability REAL,
                model TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        for key, value in DEFAULT_SETTINGS.items():
            connection.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (key, value))
        connection.commit()


def get_setting(key: str, default: str | None = None) -> str:
    initialize_database()
    with get_db_connection() as connection:
        row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row:
        return str(row["value"])
    if default is not None:
        return default
    return DEFAULT_SETTINGS.get(key, "")


def set_setting(key: str, value: Any) -> None:
    initialize_database()
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO settings(key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, str(value)),
        )
        connection.commit()


def ensure_profile_directories() -> None:
    os.makedirs(USER_PROFILES_DIR, exist_ok=True)
    os.makedirs(USER_SUMMARIES_DIR, exist_ok=True)
    initialize_database()


def get_user_profile_csv(username: str) -> str:
    return os.path.join(USER_PROFILES_DIR, f"{sanitize_username(username)}.csv")


def get_user_summary_file(username: str) -> str:
    return os.path.join(USER_SUMMARIES_DIR, f"{sanitize_username(username)}.json")


def initialize_user_profile_csv(username: str) -> str:
    ensure_profile_directories()
    file_path = get_user_profile_csv(username)
    if not os.path.exists(file_path):
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(raw_hold_columns())
    return file_path


def register_user_account(username: str, password: str = "") -> None:
    ensure_profile_directories()
    username = sanitize_username(username)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    password_hash = hash_password(password) if password else ""
    with get_db_connection() as connection:
        existing = connection.execute("SELECT username FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            if password_hash:
                connection.execute(
                    "UPDATE users SET password_hash = ?, updated_at = ? WHERE username = ?",
                    (password_hash, now, username),
                )
        else:
            connection.execute(
                """
                INSERT INTO users(username, password_hash, sample_count, threshold, created_at, updated_at)
                VALUES (?, ?, 0, ?, ?, ?)
                """,
                (username, password_hash, float(get_setting("decision_threshold", "0.55")), now, now),
            )
        connection.commit()


def verify_user_password(username: str, password: str) -> bool:
    initialize_database()
    username = sanitize_username(username)
    with get_db_connection() as connection:
        row = connection.execute("SELECT password_hash FROM users WHERE username = ?", (username,)).fetchone()
    if not row:
        return False
    stored = row["password_hash"] or ""
    if not stored:
        return True
    return stored == hash_password(password)


def save_user_sample(username: str, hold_times: List[float]) -> str:
    file_path = initialize_user_profile_csv(username)
    with open(file_path, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(hold_times)
    return file_path


def list_registered_users() -> List[str]:
    ensure_profile_directories()
    with get_db_connection() as connection:
        rows = connection.execute("SELECT username FROM users ORDER BY username").fetchall()
    if rows:
        return [str(row["username"]) for row in rows]

    users = []
    for file_name in os.listdir(USER_SUMMARIES_DIR):
        if file_name.endswith(".json"):
            users.append(os.path.splitext(file_name)[0])
    return sorted(users)


def build_user_profile_summary(username: str) -> dict:
    file_path = get_user_profile_csv(username)
    if not os.path.exists(file_path):
        raise FileNotFoundError("User profile data not found. Register the user first.")

    df = pd.read_csv(file_path)
    if len(df) < 5:
        raise ValueError("At least 5 samples are required to build a user profile.")

    feature_df = transform_dataframe(df)
    features_only = feature_df[engineered_feature_columns()]
    mean_vector = features_only.mean()
    distances = np.sqrt(((features_only - mean_vector) ** 2).sum(axis=1))
    threshold = float(distances.mean() + 2 * distances.std())
    threshold = max(threshold, 0.01)

    summary = {
        "username": sanitize_username(username),
        "sample_count": int(len(df)),
        "feature_columns": engineered_feature_columns(),
        "mean_vector": {column: float(mean_vector[column]) for column in engineered_feature_columns()},
        "threshold": threshold,
    }

    ensure_profile_directories()
    with open(get_user_summary_file(username), "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection() as connection:
        existing = connection.execute("SELECT username, password_hash, created_at FROM users WHERE username = ?", (summary["username"],)).fetchone()
        password_hash = existing["password_hash"] if existing else ""
        created_at = existing["created_at"] if existing and existing["created_at"] else now
        connection.execute(
            """
            INSERT INTO users(username, password_hash, sample_count, threshold, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                sample_count = excluded.sample_count,
                threshold = excluded.threshold,
                updated_at = excluded.updated_at
            """,
            (summary["username"], password_hash, summary["sample_count"], threshold, created_at, now),
        )
        connection.commit()

    return summary


def load_user_profile_summary(username: str) -> dict:
    file_path = get_user_summary_file(username)
    if not os.path.exists(file_path):
        raise FileNotFoundError("User profile summary not found. Register the user first.")
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def delete_user_profile(username: str) -> None:
    username = sanitize_username(username)
    csv_path = get_user_profile_csv(username)
    summary_path = get_user_summary_file(username)
    if os.path.exists(csv_path):
        os.remove(csv_path)
    if os.path.exists(summary_path):
        os.remove(summary_path)
    initialize_database()
    with get_db_connection() as connection:
        connection.execute("DELETE FROM users WHERE username = ?", (username,))
        connection.commit()


def get_user_overview() -> List[dict]:
    initialize_database()
    rows = []
    with get_db_connection() as connection:
        for row in connection.execute("SELECT username, sample_count, threshold, created_at, updated_at FROM users ORDER BY username"):
            rows.append(dict(row))
    return rows


def compare_with_profile(username: str, hold_times: List[float]) -> dict:
    profile_summary = load_user_profile_summary(username)
    feature_vector = build_feature_vector(hold_times)
    differences = []
    distance = 0.0
    for column in profile_summary["feature_columns"]:
        difference = feature_vector[column] - profile_summary["mean_vector"][column]
        distance += difference * difference
        differences.append({"feature": column, "difference": float(difference)})
    distance = float(distance ** 0.5)
    threshold = float(profile_summary["threshold"])
    profile_similarity = max(0.0, 1.0 - (distance / (threshold + 1e-6)))
    top_differences = sorted(differences, key=lambda item: abs(item["difference"]), reverse=True)[:5]
    return {
        "distance": distance,
        "threshold": threshold,
        "profile_similarity": profile_similarity,
        "top_differences": top_differences,
    }


def load_model_bundle() -> dict:
    if not os.path.exists(MODEL_FILE):
        raise FileNotFoundError("model.pkl not found. Run train_model.py first.")
    return joblib.load(MODEL_FILE)


def predict_sample(hold_times: List[float]) -> dict:
    bundle = load_model_bundle()
    feature_df = pd.DataFrame([build_feature_vector(hold_times)], columns=bundle["feature_columns"])
    probabilities = bundle["model"].predict_proba(feature_df)[0]
    genuine_probability = float(probabilities[1])
    impostor_probability = float(probabilities[0])
    prediction = 1 if genuine_probability >= float(bundle["decision_threshold"]) else 0

    return {
        "prediction": prediction,
        "genuine_probability": genuine_probability,
        "impostor_probability": impostor_probability,
        "confidence": max(genuine_probability, impostor_probability),
        "best_model": bundle["best_model"],
        "decision_threshold": float(bundle["decision_threshold"]),
    }


def authenticate_registered_user(username: str, hold_times: List[float], adaptive_learning: bool = False) -> dict:
    ml_result = predict_sample(hold_times)
    profile_result = compare_with_profile(username, hold_times)
    final_threshold = float(get_setting("decision_threshold", "0.55"))
    final_score = (0.65 * profile_result["profile_similarity"]) + (0.35 * ml_result["genuine_probability"])
    prediction = 1 if final_score >= final_threshold else 0

    result = {
        "username": sanitize_username(username),
        "prediction": prediction,
        "confidence": final_score,
        "profile_similarity": profile_result["profile_similarity"],
        "distance": profile_result["distance"],
        "threshold": profile_result["threshold"],
        "genuine_probability": ml_result["genuine_probability"],
        "impostor_probability": ml_result["impostor_probability"],
        "best_model": ml_result["best_model"],
        "decision_threshold": final_threshold,
        "top_differences": profile_result["top_differences"],
    }

    if adaptive_learning and prediction == 1:
        save_user_sample(username, hold_times)
        build_user_profile_summary(username)

    return result


def initialize_auth_log() -> None:
    os.makedirs(os.path.dirname(AUTH_LOG_FILE), exist_ok=True)
    if not os.path.exists(AUTH_LOG_FILE):
        with open(AUTH_LOG_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "username", "result", "confidence", "genuine_probability", "model"])
    initialize_database()


def log_auth_attempt(result: str, confidence: float, genuine_probability: float, model_name: str, username: str = "general") -> None:
    initialize_auth_log()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_username = sanitize_username(username) or "general"
    with open(AUTH_LOG_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                timestamp,
                clean_username,
                result,
                f"{confidence * 100:.2f}%",
                f"{genuine_probability * 100:.2f}%",
                model_name,
            ]
        )
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO attempts(timestamp, username, result, confidence, genuine_probability, model)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (timestamp, clean_username, result, float(confidence), float(genuine_probability), model_name),
        )
        connection.commit()


def _normalize_attempt_row(row: list[str]) -> dict | None:
    if len(row) == 5:
        timestamp, result, confidence, genuine_probability, model = row
        username = "general"
    elif len(row) >= 6:
        timestamp, username, result, confidence, genuine_probability, model = row[:6]
    else:
        return None
    return {
        "timestamp": timestamp,
        "username": username,
        "result": result,
        "confidence": confidence,
        "genuine_probability": genuine_probability,
        "model": model,
    }


def get_recent_attempts(limit: int = 5) -> List[dict]:
    initialize_auth_log()
    rows: List[dict] = []
    with get_db_connection() as connection:
        db_rows = connection.execute(
            """
            SELECT timestamp, username, result,
                   printf('%.2f%%', confidence * 100.0) AS confidence,
                   printf('%.2f%%', genuine_probability * 100.0) AS genuine_probability,
                   model
            FROM attempts
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    if db_rows:
        return [dict(row) for row in db_rows]

    if not os.path.exists(AUTH_LOG_FILE):
        return []

    with open(AUTH_LOG_FILE, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)
        for row in reader:
            if not row:
                continue
            normalized = _normalize_attempt_row(row)
            if normalized:
                rows.append(normalized)
    return list(reversed(rows[-limit:]))


def get_attempt_history(limit: int | None = None) -> List[dict]:
    initialize_auth_log()
    query = """
        SELECT timestamp, username, result, confidence, genuine_probability, model
        FROM attempts
        ORDER BY id DESC
    """
    parameters: tuple[Any, ...] = ()
    if limit:
        query += " LIMIT ?"
        parameters = (limit,)
    with get_db_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()
    return [dict(row) for row in rows]


def export_attempt_history(output_path: str) -> str:
    history = get_attempt_history()
    df = pd.DataFrame(history)
    if df.empty:
        df = pd.DataFrame(columns=["timestamp", "username", "result", "confidence", "genuine_probability", "model"])
    df["confidence"] = df["confidence"].apply(lambda value: round(float(value) * 100, 2) if value != "" else value)
    df["genuine_probability"] = df["genuine_probability"].apply(lambda value: round(float(value) * 100, 2) if value != "" else value)
    df.to_csv(output_path, index=False)
    return output_path


def get_dashboard_stats() -> dict:
    initialize_database()
    attempts = get_attempt_history()
    users = get_user_overview()
    granted = sum(1 for attempt in attempts if attempt["result"] == "Access Granted")
    denied = sum(1 for attempt in attempts if attempt["result"] != "Access Granted")
    average_confidence = 0.0
    if attempts:
        average_confidence = sum(float(attempt["confidence"]) for attempt in attempts) / len(attempts)
    return {
        "total_users": len(users),
        "total_attempts": len(attempts),
        "granted_attempts": granted,
        "denied_attempts": denied,
        "average_confidence": average_confidence,
        "decision_threshold": float(get_setting("decision_threshold", "0.55")),
        "max_failed_attempts": int(get_setting("max_failed_attempts", "3")),
        "cooldown_seconds": int(get_setting("cooldown_seconds", "10")),
    }
