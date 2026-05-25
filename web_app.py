import os

from flask import Flask, render_template_string, request, url_for

from backend_utils import (
    authenticate_registered_user,
    get_attempt_history,
    get_dashboard_stats,
    get_user_overview,
    list_registered_users,
    log_auth_attempt,
    verify_user_password,
)


TARGET_TEXT = "secure123"
app = Flask(__name__)


HOME_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Keystroke Security Web</title>
    <style>
        body { font-family: Arial, sans-serif; background: #081420; color: #f1faee; margin: 0; }
        .wrap { max-width: 980px; margin: 0 auto; padding: 28px; }
        .card { background: #102235; border: 1px solid #264d73; border-radius: 14px; padding: 20px; margin-bottom: 20px; }
        input, select { width: 100%; padding: 10px; margin-top: 6px; margin-bottom: 14px; border-radius: 8px; border: none; }
        button { background: #00b4d8; color: white; border: none; padding: 12px 18px; border-radius: 10px; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; border-bottom: 1px solid #264d73; text-align: left; }
        .success { color: #52b788; font-weight: bold; }
        .error { color: #f94144; font-weight: bold; }
        .grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 18px; }
    </style>
</head>
<body>
    <div class="wrap">
        <h1>AI-Based Secure Authentication System</h1>
        <p>Web prototype for password + keystroke authentication</p>
        <div class="grid">
            <div class="card">
                <h2>Login</h2>
                <form method="post" action="{{ url_for('login') }}">
                    <label>User Profile</label>
                    <select name="username" required>
                        {% for user in users %}
                        <option value="{{ user }}">{{ user }}</option>
                        {% endfor %}
                    </select>
                    <label>Password</label>
                    <input type="password" name="password" required>
                    <label>Fixed Text</label>
                    <input type="text" name="typed_text" value="secure123" required>
                    <label>Hold Times</label>
                    <input type="text" name="hold_times" placeholder="Example: 0.12,0.10,0.11,0.09,0.13,0.10,0.12,0.11,0.09" required>
                    <button type="submit">Authenticate</button>
                </form>
                {% if result %}
                    <p class="{{ 'success' if result.prediction == 1 else 'error' }}">
                        {{ 'Access Granted' if result.prediction == 1 else 'Access Denied' }}
                    </p>
                    <p>Confidence: {{ '%.2f'|format(result.confidence * 100) }}%</p>
                    <p>Profile similarity: {{ '%.2f'|format(result.profile_similarity * 100) }}%</p>
                {% endif %}
                {% if error %}
                    <p class="error">{{ error }}</p>
                {% endif %}
            </div>
            <div class="card">
                <h2>Admin Snapshot</h2>
                <p>Total users: {{ stats.total_users }}</p>
                <p>Total attempts: {{ stats.total_attempts }}</p>
                <p>Granted: {{ stats.granted_attempts }}</p>
                <p>Denied: {{ stats.denied_attempts }}</p>
                <p>Decision threshold: {{ stats.decision_threshold }}</p>
                <p><a href="{{ url_for('admin') }}" style="color:#90e0ef;">Open detailed admin page</a></p>
            </div>
        </div>
    </div>
</body>
</html>
"""


ADMIN_TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>Keystroke Admin</title>
    <style>
        body { font-family: Arial, sans-serif; background: #081420; color: #f1faee; margin: 0; }
        .wrap { max-width: 1100px; margin: 0 auto; padding: 28px; }
        .card { background: #102235; border: 1px solid #264d73; border-radius: 14px; padding: 20px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; border-bottom: 1px solid #264d73; text-align: left; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
        a { color: #90e0ef; }
    </style>
</head>
<body>
    <div class="wrap">
        <h1>Admin Dashboard</h1>
        <p><a href="{{ url_for('home') }}">Back to login</a></p>
        <div class="grid">
            <div class="card">
                <h2>Users</h2>
                <table>
                    <tr><th>User</th><th>Samples</th><th>Threshold</th></tr>
                    {% for user in users %}
                    <tr>
                        <td>{{ user.username }}</td>
                        <td>{{ user.sample_count }}</td>
                        <td>{{ '%.2f'|format(user.threshold) }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            <div class="card">
                <h2>Recent Attempts</h2>
                <table>
                    <tr><th>Time</th><th>User</th><th>Result</th><th>Confidence</th></tr>
                    {% for attempt in attempts %}
                    <tr>
                        <td>{{ attempt.timestamp }}</td>
                        <td>{{ attempt.username }}</td>
                        <td>{{ attempt.result }}</td>
                        <td>{{ '%.2f'|format(attempt.confidence * 100) }}%</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(
        HOME_TEMPLATE,
        users=list_registered_users(),
        stats=get_dashboard_stats(),
        result=None,
        error=None,
    )


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    typed_text = request.form.get("typed_text", "").strip()
    hold_times_text = request.form.get("hold_times", "").strip()

    if typed_text != TARGET_TEXT:
        return render_template_string(
            HOME_TEMPLATE,
            users=list_registered_users(),
            stats=get_dashboard_stats(),
            result=None,
            error="Typed text must match secure123 exactly.",
        )
    if not verify_user_password(username, password):
        return render_template_string(
            HOME_TEMPLATE,
            users=list_registered_users(),
            stats=get_dashboard_stats(),
            result=None,
            error="Incorrect password for selected user.",
        )

    try:
        hold_times = [float(value.strip()) for value in hold_times_text.split(",") if value.strip()]
    except ValueError:
        return render_template_string(
            HOME_TEMPLATE,
            users=list_registered_users(),
            stats=get_dashboard_stats(),
            result=None,
            error="Hold times must be comma-separated numeric values.",
        )

    result = authenticate_registered_user(username, hold_times, adaptive_learning=True)
    outcome = "Access Granted" if result["prediction"] == 1 else "Access Denied"
    log_auth_attempt(outcome, result["confidence"], result["genuine_probability"], result["best_model"], username=username)
    return render_template_string(
        HOME_TEMPLATE,
        users=list_registered_users(),
        stats=get_dashboard_stats(),
        result=result,
        error=None,
    )


@app.route("/admin")
def admin():
    return render_template_string(
        ADMIN_TEMPLATE,
        users=get_user_overview(),
        attempts=get_attempt_history(limit=20),
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    app.run(host="0.0.0.0", port=port, debug=False)
