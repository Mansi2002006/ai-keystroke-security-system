import tkinter as tk
from tkinter import messagebox, ttk

from backend_utils import compare_with_profile, list_registered_users
from capture_data import SampleCaptureWindow


class ProfileComparisonApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Profile Comparison")
        self.root.geometry("640x480")
        self.root.configure(bg="#081420")
        self.selected_user = tk.StringVar()

        self.build_gui()

    def build_gui(self) -> None:
        tk.Label(self.root, text="Profile Comparison", font=("Arial", 22, "bold"), fg="#f1faee", bg="#081420", pady=14).pack()
        selector = tk.Frame(self.root, bg="#081420")
        selector.pack(pady=10)
        tk.Label(selector, text="User", fg="#f1faee", bg="#081420", font=("Arial", 12, "bold")).pack(side="left", padx=(0, 10))
        self.user_combo = ttk.Combobox(selector, textvariable=self.selected_user, values=list_registered_users(), state="readonly", width=20)
        self.user_combo.pack(side="left")
        if self.user_combo["values"]:
            self.user_combo.current(0)

        tk.Button(self.root, text="Capture and Compare", command=self.capture_and_compare, bg="#00b4d8", fg="white", relief="flat", padx=14, pady=8).pack(pady=10)

        self.output = tk.Text(self.root, bg="#102235", fg="#caf0f8", insertbackground="white", wrap="word", font=("Consolas", 11))
        self.output.pack(fill="both", expand=True, padx=18, pady=12)

    def capture_and_compare(self) -> None:
        username = self.selected_user.get().strip()
        if not username:
            messagebox.showwarning("Missing User", "Please select a user first.")
            return
        capture_window = SampleCaptureWindow(1, 1, parent=self.root)
        sample = capture_window.run()
        if sample is None:
            return
        comparison = compare_with_profile(username, sample)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, f"User: {username}\n")
        self.output.insert(tk.END, f"Distance: {comparison['distance']:.4f}\n")
        self.output.insert(tk.END, f"Threshold: {comparison['threshold']:.4f}\n")
        self.output.insert(tk.END, f"Profile similarity: {comparison['profile_similarity'] * 100:.2f}%\n\n")
        self.output.insert(tk.END, "Top feature differences:\n")
        for item in comparison["top_differences"]:
            self.output.insert(tk.END, f"- {item['feature']}: {item['difference']:.4f}\n")


def main() -> None:
    root = tk.Tk()
    ProfileComparisonApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
