import os
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import List, Optional, Tuple

from backend_utils import authenticate_registered_user, list_registered_users, log_auth_attempt


TARGET_TEXT = "secure123"


class AuthenticationCaptureWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Authentication Capture")
        self.root.geometry("520x320")
        self.root.resizable(False, False)

        self.press_times = {}
        self.hold_times: List[float] = []
        self.result: Optional[List[float]] = None
        self.selected_user = tk.StringVar()

        self.build_gui()

    def build_gui(self) -> None:
        tk.Label(
            self.root,
            text="Authentication Window",
            font=("Arial", 16, "bold"),
            pady=10,
        ).pack()

        tk.Label(
            self.root,
            text=f"Type this text exactly: {TARGET_TEXT}",
            font=("Arial", 13, "bold"),
            pady=12,
        ).pack()

        users = list_registered_users()
        tk.Label(self.root, text="Select user profile", font=("Arial", 11, "bold")).pack()
        self.user_combo = ttk.Combobox(self.root, textvariable=self.selected_user, values=users, state="readonly", width=22)
        self.user_combo.pack(pady=(4, 14))
        if users:
            self.user_combo.current(0)

        self.entry = tk.Entry(self.root, font=("Arial", 16), width=25)
        self.entry.pack(pady=18)
        self.entry.focus_set()
        self.entry.bind("<KeyPress>", self.on_key_press)
        self.entry.bind("<KeyRelease>", self.on_key_release)

        tk.Button(
            self.root,
            text="Authenticate",
            command=self.submit_sample,
            font=("Arial", 12, "bold"),
            width=18,
            bg="#2e8b57",
            fg="white",
        ).pack(pady=8)

        tk.Button(
            self.root,
            text="Clear",
            command=self.clear_entry,
            font=("Arial", 11),
            width=18,
        ).pack()

    def on_key_press(self, event) -> None:
        if event.keysym in {"BackSpace", "Delete"}:
            self.clear_entry()
            return
        self.press_times[event.keysym] = time.time()

    def on_key_release(self, event) -> None:
        if event.keysym not in self.press_times:
            return

        hold_time = time.time() - self.press_times[event.keysym]
        self.hold_times.append(round(hold_time, 6))

    def clear_entry(self) -> None:
        self.entry.delete(0, tk.END)
        self.press_times.clear()
        self.hold_times.clear()

    def submit_sample(self) -> None:
        typed_text = self.entry.get()
        if typed_text != TARGET_TEXT:
            messagebox.showwarning("Invalid Text", "Please type the fixed text exactly.")
            self.clear_entry()
            return

        if len(self.hold_times) < len(TARGET_TEXT):
            messagebox.showwarning("Incomplete Sample", "Please type the full text normally.")
            self.clear_entry()
            return

        self.result = self.hold_times[: len(TARGET_TEXT)]
        self.root.destroy()

    def run(self) -> Optional[List[float]]:
        self.root.mainloop()
        return self.result


def predict_authentication(hold_times: List[float]) -> Tuple[str, float]:
    users = list_registered_users()
    if not users:
        raise FileNotFoundError("No registered user profiles found. Run register_user.py first.")

    prediction_result = authenticate_registered_user(users[0], hold_times)
    prediction = prediction_result["prediction"]
    confidence = float(prediction_result["confidence"])

    if prediction == 1:
        return "Access Granted", confidence
    return "Access Denied", confidence


def main() -> None:
    users = list_registered_users()
    if not users:
        print("No registered user profiles found. Run register_user.py first.")
        return

    window = AuthenticationCaptureWindow()
    hold_times = window.run()
    if hold_times is None:
        print("Authentication cancelled.")
        return

    username = window.selected_user.get().strip()
    if not username:
        print("No user selected.")
        return

    prediction_result = authenticate_registered_user(username, hold_times)
    result = "Access Granted" if prediction_result["prediction"] == 1 else "Access Denied"
    confidence = prediction_result["confidence"]
    log_auth_attempt(result, confidence, prediction_result["genuine_probability"], prediction_result["best_model"], username=username)
    print(f"\nResult: {result}")
    print(f"Confidence: {confidence * 100:.2f}%")
    print(f"Best model used: {prediction_result['best_model']}")
    print(f"Genuine probability: {prediction_result['genuine_probability'] * 100:.2f}%")
    print(f"Profile similarity: {prediction_result['profile_similarity'] * 100:.2f}%")
    print(f"Selected user: {username}")
    if result == "Access Granted":
        print("System decision: Typing pattern matches the genuine user.")
    else:
        print("System decision: Typing pattern does not match the genuine user.")


if __name__ == "__main__":
    main()
