import os
import tkinter as tk
from tkinter import messagebox, ttk

from backend_utils import (
    delete_user_profile,
    export_attempt_history,
    get_attempt_history,
    get_dashboard_stats,
    get_user_overview,
    set_setting,
)


EXPORT_FILE = os.path.join("data", "exported_attempt_history.csv")


class AdminDashboard:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Admin Dashboard")
        self.root.geometry("920x620")
        self.root.configure(bg="#081420")

        self.threshold_var = tk.StringVar()
        self.failed_attempts_var = tk.StringVar()
        self.cooldown_var = tk.StringVar()

        self.build_gui()
        self.refresh_all()

    def build_gui(self) -> None:
        tk.Label(
            self.root,
            text="Admin Dashboard",
            font=("Arial", 24, "bold"),
            fg="#f1faee",
            bg="#081420",
            pady=14,
        ).pack()

        summary_frame = tk.Frame(self.root, bg="#102235")
        summary_frame.pack(fill="x", padx=18, pady=10)
        self.summary_label = tk.Label(summary_frame, text="", font=("Arial", 12), fg="#caf0f8", bg="#102235", justify="left", pady=12)
        self.summary_label.pack(anchor="w", padx=16)

        settings_frame = tk.Frame(self.root, bg="#102235")
        settings_frame.pack(fill="x", padx=18, pady=6)
        tk.Label(settings_frame, text="Decision Threshold", fg="#f1faee", bg="#102235", font=("Arial", 11, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        tk.Entry(settings_frame, textvariable=self.threshold_var, width=8).grid(row=0, column=1, padx=6)
        tk.Label(settings_frame, text="Max Failed Attempts", fg="#f1faee", bg="#102235", font=("Arial", 11, "bold")).grid(row=0, column=2, padx=10, pady=10, sticky="w")
        tk.Entry(settings_frame, textvariable=self.failed_attempts_var, width=8).grid(row=0, column=3, padx=6)
        tk.Label(settings_frame, text="Cooldown Seconds", fg="#f1faee", bg="#102235", font=("Arial", 11, "bold")).grid(row=0, column=4, padx=10, pady=10, sticky="w")
        tk.Entry(settings_frame, textvariable=self.cooldown_var, width=8).grid(row=0, column=5, padx=6)
        tk.Button(settings_frame, text="Save Security Settings", command=self.save_settings, bg="#00b4d8", fg="white", relief="flat", padx=12).grid(row=0, column=6, padx=12)
        tk.Button(settings_frame, text="Export Attempt Report", command=self.export_report, bg="#1f8a70", fg="white", relief="flat", padx=12).grid(row=0, column=7, padx=12)

        content = tk.Frame(self.root, bg="#081420")
        content.pack(fill="both", expand=True, padx=18, pady=10)

        users_frame = tk.Frame(content, bg="#102235")
        users_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(users_frame, text="Registered Users", font=("Arial", 14, "bold"), fg="#f1faee", bg="#102235").pack(pady=10)
        self.users_tree = ttk.Treeview(users_frame, columns=("samples", "threshold", "updated"), show="headings", height=16)
        self.users_tree.heading("samples", text="Samples")
        self.users_tree.heading("threshold", text="Threshold")
        self.users_tree.heading("updated", text="Updated")
        self.users_tree.column("samples", width=80, anchor="center")
        self.users_tree.column("threshold", width=90, anchor="center")
        self.users_tree.column("updated", width=180, anchor="center")
        self.users_tree.pack(fill="both", expand=True, padx=12, pady=8)
        tk.Button(users_frame, text="Delete Selected User", command=self.delete_selected_user, bg="#c1121f", fg="white", relief="flat", padx=12).pack(pady=(0, 12))

        attempts_frame = tk.Frame(content, bg="#102235")
        attempts_frame.pack(side="right", fill="both", expand=True, padx=(8, 0))
        tk.Label(attempts_frame, text="Attempt History", font=("Arial", 14, "bold"), fg="#f1faee", bg="#102235").pack(pady=10)
        self.attempts_tree = ttk.Treeview(attempts_frame, columns=("time", "user", "result", "confidence"), show="headings", height=16)
        self.attempts_tree.heading("time", text="Timestamp")
        self.attempts_tree.heading("user", text="User")
        self.attempts_tree.heading("result", text="Result")
        self.attempts_tree.heading("confidence", text="Confidence")
        self.attempts_tree.column("time", width=170)
        self.attempts_tree.column("user", width=90, anchor="center")
        self.attempts_tree.column("result", width=110, anchor="center")
        self.attempts_tree.column("confidence", width=90, anchor="center")
        self.attempts_tree.pack(fill="both", expand=True, padx=12, pady=8)

    def refresh_all(self) -> None:
        stats = get_dashboard_stats()
        self.summary_label.config(
            text=(
                f"Total Users: {stats['total_users']}    "
                f"Total Attempts: {stats['total_attempts']}    "
                f"Granted: {stats['granted_attempts']}    "
                f"Denied: {stats['denied_attempts']}    "
                f"Avg Confidence: {stats['average_confidence'] * 100:.2f}%"
            )
        )
        self.threshold_var.set(str(stats["decision_threshold"]))
        self.failed_attempts_var.set(str(stats["max_failed_attempts"]))
        self.cooldown_var.set(str(stats["cooldown_seconds"]))

        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        for user in get_user_overview():
            self.users_tree.insert("", "end", iid=user["username"], values=(user["sample_count"], f"{user['threshold']:.2f}", user["updated_at"] or "-"))

        for item in self.attempts_tree.get_children():
            self.attempts_tree.delete(item)
        for attempt in get_attempt_history(limit=20):
            self.attempts_tree.insert(
                "",
                "end",
                values=(
                    attempt["timestamp"],
                    attempt["username"],
                    attempt["result"],
                    f"{float(attempt['confidence']) * 100:.2f}%",
                ),
            )

    def save_settings(self) -> None:
        try:
            threshold = float(self.threshold_var.get())
            max_attempts = int(self.failed_attempts_var.get())
            cooldown = int(self.cooldown_var.get())
        except ValueError:
            messagebox.showwarning("Invalid Values", "Please enter valid numeric security settings.")
            return

        set_setting("decision_threshold", threshold)
        set_setting("max_failed_attempts", max_attempts)
        set_setting("cooldown_seconds", cooldown)
        self.refresh_all()
        messagebox.showinfo("Saved", "Security settings updated successfully.")

    def export_report(self) -> None:
        path = export_attempt_history(EXPORT_FILE)
        messagebox.showinfo("Exported", f"Attempt history exported to:\n{os.path.abspath(path)}")

    def delete_selected_user(self) -> None:
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a user first.")
            return
        username = selected[0]
        if not messagebox.askyesno("Confirm Delete", f"Delete user '{username}' and all typing samples?"):
            return
        delete_user_profile(username)
        self.refresh_all()


def main() -> None:
    root = tk.Tk()
    AdminDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
