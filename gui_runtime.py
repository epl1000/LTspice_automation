import tkinter as tk
from tkinter import messagebox

import pyltspicetest1


def run_simulation():
    """Run the LTspice simulation and show results."""
    try:
        pyltspicetest1.main()
    except Exception as exc:
        messagebox.showerror("Error", f"Simulation failed: {exc}")


def main():
    root = tk.Tk()
    root.title("LTspice Runtime")

    run_button = tk.Button(root, text="RUN", command=run_simulation)
    run_button.pack(padx=20, pady=20)

    root.mainloop()


if __name__ == "__main__":
    main()
