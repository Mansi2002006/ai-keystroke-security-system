import tkinter as tk
from tkinter import messagebox

from backend_utils import build_user_profile_summary, register_user_account, sanitize_username, save_user_sample
from capture_data import SampleCaptureWindow


class UserRegistrationApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Register Typing Profile")
        self.root.geometry("520x320")
        self.root.resizable(False, False)
        self.root.configure(bg="#102235")

        self.build_gui()

    def build_gui(self) -> None:
        tk.Label(
            self.root,
            text="User Registration",
            font=("Arial", 20, "bold"),
            fg="#f1faee",
            bg="#102235",
            pady=16,
        ).pack()

        tk.Label(
            self.root,
            text="Create a typing profile by entering a username and recording samples.",
            font=("Arial", 11),
            fg="#caf0f8",
            bg="#102235",
        ).pack()

        form = tk.Frame(self.root, bg="#102235")
        form.pack(pady=24)

        tk.Label(form, text="Username", font=("Arial", 12, "bold"), fg="#f1faee", bg="#102235").grid(row=0, column=0, sticky="w", pady=8)
        self.username_entry = tk.Entry(form, font=("Arial", 12), width=24)
        self.username_entry.grid(row=0, column=1, padx=12, pady=8)

        tk.Label(form, text="Samples", font=("Arial", 12, "bold"), fg="#f1faee", bg="#102235").grid(row=1, column=0, sticky="w", pady=8)
        self.samples_entry = tk.Entry(form, font=("Arial", 12), width=24)
        self.samples_entry.insert(0, "10")
        self.samples_entry.grid(row=1, column=1, padx=12, pady=8)

        tk.Label(form, text="Password", font=("Arial", 12, "bold"), fg="#f1faee", bg="#102235").grid(row=2, column=0, sticky="w", pady=8)
        self.password_entry = tk.Entry(form, font=("Arial", 12), width=24, show="*")
        self.password_entry.grid(row=2, column=1, padx=12, pady=8)

        tk.Button(
            self.root,
            text="Register User",
            font=("Arial", 13, "bold"),
            bg="#1f8a70",
            fg="white",
            relief="flat",
            padx=20,
            pady=10,
            command=self.register_user,
        ).pack(pady=12)

        self.status_label = tk.Label(
            self.root,
            text="Recommended: record at least 10 samples in your natural style.",
            font=("Arial", 10),
            fg="#98c1d9",
            bg="#102235",
        )
        self.status_label.pack(pady=8)

    def register_user(self) -> None:
        username = sanitize_username(self.username_entry.get())
        if not username:
            messagebox.showwarning("Invalid Username", "Please enter a valid username.")
            return

        try:
            sample_count = int(self.samples_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Invalid Samples", "Please enter a valid number of samples.")
            return

        if sample_count < 5:
            messagebox.showwarning("Too Few Samples", "Please record at least 5 samples.")
            return

        password = self.password_entry.get().strip()
        if len(password) < 4:
            messagebox.showwarning("Weak Password", "Please enter a password with at least 4 characters.")
            return

        register_user_account(username, password)

        saved = 0
        while saved < sample_count:
            capture_window = SampleCaptureWindow(saved + 1, sample_count)
            sample = capture_window.run()
            if sample is None:
                break
            save_user_sample(username, sample)
            saved += 1

        if saved < 5:
            messagebox.showwarning("Registration Incomplete", "At least 5 samples are needed to create a profile.")
            return

        summary = build_user_profile_summary(username)
        if self.status_label.winfo_exists():
            self.status_label.config(text=f"Registered user: {summary['username']} with {summary['sample_count']} samples.")
        messagebox.showinfo(
            "Registration Complete",
            f"User '{summary['username']}' registered successfully with {summary['sample_count']} samples.",
        )


def main() -> None:
    root = tk.Tk()
    app = UserRegistrationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
