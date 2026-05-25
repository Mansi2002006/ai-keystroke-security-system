import csv
import os
import time
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional


TARGET_TEXT = "secure123"
DATA_FOLDER = "data"


def ensure_data_folder() -> None:
    os.makedirs(DATA_FOLDER, exist_ok=True)


def get_output_file(user_type: str) -> str:
    if user_type == "genuine":
        return os.path.join(DATA_FOLDER, "genuine.csv")
    return os.path.join(DATA_FOLDER, "impostor.csv")


def create_header() -> List[str]:
    return [f"hold_{index + 1}" for index in range(len(TARGET_TEXT))] + ["label"]


def initialize_csv(file_path: str) -> None:
    if not os.path.exists(file_path):
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(create_header())


class SampleCaptureWindow:
    def __init__(self, sample_number: int, total_samples: int, parent: tk.Misc | None = None) -> None:
        self.parent = parent
        self.root = tk.Toplevel(parent) if parent is not None else tk.Tk()
        self.root.title("Keystroke Sample Capture")
        self.root.geometry("520x320")
        self.root.resizable(False, False)
        self.root.transient(parent) if parent is not None else None
        self.root.grab_set() if parent is not None else None

        self.sample_number = sample_number
        self.total_samples = total_samples
        self.press_times = {}
        self.hold_times: List[float] = []
        self.result: Optional[List[float]] = None

        self.build_gui()

    def build_gui(self) -> None:
        tk.Label(
            self.root,
            text="Keystroke Data Capture",
            font=("Arial", 16, "bold"),
            pady=10,
        ).pack()

        tk.Label(
            self.root,
            text=f"Sample {self.sample_number} of {self.total_samples}",
            font=("Arial", 12),
        ).pack()

        tk.Label(
            self.root,
            text=f"Type this text exactly: {TARGET_TEXT}",
            font=("Arial", 13, "bold"),
            pady=10,
        ).pack()

        tk.Label(
            self.root,
            text="Type normally and then click Save Sample",
            font=("Arial", 11),
        ).pack()

        self.entry = tk.Entry(self.root, font=("Arial", 16), width=25)
        self.entry.pack(pady=20)
        self.entry.focus_set()
        self.entry.bind("<KeyPress>", self.on_key_press)
        self.entry.bind("<KeyRelease>", self.on_key_release)

        tk.Button(
            self.root,
            text="Save Sample",
            command=self.save_sample,
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

        self.status_label = tk.Label(self.root, text="", font=("Arial", 11), fg="blue", pady=15)
        self.status_label.pack()

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
        self.status_label.config(text="Entry cleared. Type again.")

    def save_sample(self) -> None:
        typed_text = self.entry.get()
        if typed_text != TARGET_TEXT:
            messagebox.showwarning("Invalid Text", "Please type the fixed text exactly as shown.")
            self.clear_entry()
            return

        if len(self.hold_times) < len(TARGET_TEXT):
            messagebox.showwarning("Incomplete Sample", "Please type the full text normally without skipping keys.")
            self.clear_entry()
            return

        self.result = self.hold_times[: len(TARGET_TEXT)]
        self.root.destroy()

    def run(self) -> Optional[List[float]]:
        if self.parent is not None:
            self.root.wait_window()
        else:
            self.root.mainloop()
        return self.result


def append_sample(file_path: str, hold_times: List[float], label: int) -> None:
    with open(file_path, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(hold_times + [label])


def main() -> None:
    ensure_data_folder()

    print("AI-Based Secure Authentication System Using Keystroke Dynamics")
    print("Dataset Collection Tool")
    print("-" * 60)
    print("1. Genuine User Data")
    print("2. Impostor Data")

    choice = input("Enter your choice (1 or 2): ").strip()
    if choice == "1":
        user_type = "genuine"
        label = 1
    elif choice == "2":
        user_type = "impostor"
        label = 0
    else:
        print("Invalid choice. Run the program again.")
        return

    try:
        sample_count = int(input("How many samples do you want to record? ").strip())
    except ValueError:
        print("Please enter a valid number.")
        return

    file_path = get_output_file(user_type)
    initialize_csv(file_path)

    saved_samples = 0
    while saved_samples < sample_count:
        capture_window = SampleCaptureWindow(saved_samples + 1, sample_count)
        sample = capture_window.run()
        if sample is None:
            print("Sample window closed before saving. Stopping capture.")
            break

        append_sample(file_path, sample, label)
        saved_samples += 1
        print(f"Sample {saved_samples} saved successfully.")

    print(f"\nSaved {saved_samples} sample(s) in: {file_path}")
    if saved_samples > 0:
        print("Next step: run train_model.py")


if __name__ == "__main__":
    main()
