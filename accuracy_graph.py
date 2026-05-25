import json
import os

import matplotlib.pyplot as plt
from backend_utils import get_attempt_history, get_user_overview


METRICS_FILE = os.path.join("models", "metrics.json")


def main() -> None:
    if not os.path.exists(METRICS_FILE):
        raise FileNotFoundError("metrics.json not found. Run train_model.py first.")

    with open(METRICS_FILE, "r", encoding="utf-8") as file:
        metrics = json.load(file)

    metric_names = ["accuracy", "precision", "recall", "f1_score"]
    metric_values = [metrics[name] * 100 for name in metric_names]
    model_names = list(metrics.get("cross_validation_accuracy", {}).keys())
    model_scores = [metrics["cross_validation_accuracy"][name] * 100 for name in model_names]

    attempts = get_attempt_history()
    user_overview = get_user_overview()
    granted_count = sum(1 for attempt in attempts if attempt["result"] == "Access Granted")
    denied_count = sum(1 for attempt in attempts if attempt["result"] != "Access Granted")
    user_names = [user["username"] for user in user_overview]
    sample_counts = [user["sample_count"] for user in user_overview]

    plt.style.use("dark_background")
    figure, axes = plt.subplots(2, 2, figsize=(15, 10), constrained_layout=True)
    figure.patch.set_facecolor("#081420")

    performance_bars = axes[0, 0].bar(metric_names, metric_values, color=["#52b788", "#4ea8de", "#ff9f1c", "#c77dff"])
    axes[0, 0].set_ylim(0, 100)
    axes[0, 0].set_ylabel("Percentage")
    axes[0, 0].set_title("Model Performance Metrics")
    axes[0, 0].set_facecolor("#102235")
    axes[0, 0].tick_params(axis="x", labelrotation=0, pad=8)

    for bar, value in zip(performance_bars, metric_values):
        axes[0, 0].text(bar.get_x() + bar.get_width() / 2, value + 1, f"{value:.2f}%", ha="center")

    if model_names:
        comparison_bars = axes[0, 1].bar(model_names, model_scores, color=["#00b4d8", "#90be6d", "#f94144"])
        axes[0, 1].set_ylim(0, 100)
        axes[0, 1].set_ylabel("CV Accuracy")
        axes[0, 1].set_title("Model Comparison")
        axes[0, 1].set_facecolor("#102235")
        axes[0, 1].tick_params(axis="x", labelrotation=12, pad=8)
        for bar, value in zip(comparison_bars, model_scores):
            axes[0, 1].text(bar.get_x() + bar.get_width() / 2, value + 1, f"{value:.2f}%", ha="center")
    else:
        axes[0, 1].text(0.5, 0.5, "No comparison data", ha="center", va="center")
        axes[0, 1].set_facecolor("#102235")
        axes[0, 1].set_xticks([])
        axes[0, 1].set_yticks([])

    axes[1, 0].set_facecolor("#102235")
    if granted_count or denied_count:
        axes[1, 0].pie(
            [max(granted_count, 0.001), max(denied_count, 0.001)],
            labels=["Granted", "Denied"],
            autopct="%1.1f%%",
            colors=["#52b788", "#f94144"],
            startangle=110,
        )
        axes[1, 0].set_title("Authentication Outcomes")
    else:
        axes[1, 0].text(0.5, 0.5, "No attempt history", ha="center", va="center")
        axes[1, 0].set_xticks([])
        axes[1, 0].set_yticks([])

    axes[1, 1].set_facecolor("#102235")
    if user_names:
        user_bars = axes[1, 1].bar(user_names, sample_counts, color=["#00b4d8", "#90be6d", "#ffd166", "#c77dff"][: len(user_names)])
        axes[1, 1].set_title("User Sample Counts")
        axes[1, 1].set_ylabel("Samples")
        axes[1, 1].tick_params(axis="x", labelrotation=12, pad=8)
        for bar, value in zip(user_bars, sample_counts):
            axes[1, 1].text(bar.get_x() + bar.get_width() / 2, value + 0.2, str(value), ha="center")
    else:
        axes[1, 1].text(0.5, 0.5, "No user profiles", ha="center", va="center")
        axes[1, 1].set_xticks([])
        axes[1, 1].set_yticks([])

    plt.show()


if __name__ == "__main__":
    main()
