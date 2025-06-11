import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

import pyltspicetest1


def main():
    root = tk.Tk()
    root.title("LTspice Runtime")

    # Configure window size: keep full screen height but half the width
    try:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.geometry(f"{screen_width // 2}x{screen_height}")
    except tk.TclError:
        root.geometry("400x600")

    controls = tk.Frame(root)
    controls.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

    # --- Spinner controls for netlist values ---
    spinner_frame = tk.Frame(controls)
    spinner_frame.grid(row=0, column=0, sticky="w")

    r9_var = tk.DoubleVar(value=1000)
    r1_var = tk.DoubleVar(value=500)
    r3_var = tk.DoubleVar(value=1000)
    c1_var = tk.DoubleVar(value=5e-12)

    tk.Label(spinner_frame, text="R9 (Gain Ω)").grid(row=0, column=0, padx=5, pady=2, sticky="w")
    tk.Spinbox(spinner_frame, from_=1, to=1e6, increment=100, textvariable=r9_var, width=8).grid(row=0, column=1, padx=5, pady=2)
    tk.Label(spinner_frame, text="C1 (F)").grid(row=0, column=2, padx=5, pady=2, sticky="w")
    # Tk's Spinbox widget does not reliably support the "e" format specifier
    # across platforms.  Using it on some Tcl/Tk versions results in a
    # ``TclError: bad spinbox format specifier".  Simply omit the ``format``
    # argument and let Tk handle the numeric string representation so the GUI
    # works on all systems.
    tk.Spinbox(
        spinner_frame,
        from_=1e-12,
        to=1e-6,
        increment=1e-12,
        textvariable=c1_var,
        width=8,
    ).grid(row=0, column=3, padx=5, pady=2)

    tk.Label(spinner_frame, text="R1 (Input Ω)").grid(row=1, column=0, padx=5, pady=2, sticky="w")
    tk.Spinbox(spinner_frame, from_=1, to=1e6, increment=100, textvariable=r1_var, width=8).grid(row=1, column=1, padx=5, pady=2)
    tk.Label(spinner_frame, text="R3 (Load Ω)").grid(row=1, column=2, padx=5, pady=2, sticky="w")
    tk.Spinbox(spinner_frame, from_=1, to=1e6, increment=100, textvariable=r3_var, width=8).grid(row=1, column=3, padx=5, pady=2)

    figure = plt.Figure(figsize=(5, 4), dpi=100)
    ax = figure.add_subplot(111)
    canvas = FigureCanvasTkAgg(figure, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=True)

    last_model_file = "last_model.txt"

    try:
        with open(last_model_file, "r", encoding="utf-8") as f:
            current_model = f.read().strip()
    except FileNotFoundError:
        current_model = ""

    model_label_var = tk.StringVar()

    def update_model_label():
        """Refresh the displayed model name."""
        name = Path(current_model).name if current_model else "None"
        model_label_var.set(f"OP AMP MODEL: {name}")

    update_model_label()

    def load_model():
        """Prompt for an op-amp model file and remember the selection."""

        nonlocal current_model
        lib_path = filedialog.askopenfilename(
            title="Select op-amp model",
            filetypes=[("SPICE model", "*.lib"), ("All files", "*.*")],
        )
        if not lib_path:
            return

        current_model = lib_path
        try:
            with open(last_model_file, "w", encoding="utf-8") as f:
                f.write(current_model)
        except OSError:
            pass
        update_model_label()

    def run_simulation():
        """Run the simulation using the currently loaded model."""

        if not current_model:
            messagebox.showinfo(
                "No model loaded",
                "Please load an op-amp model before running the simulation.",
            )
            return

        try:
            time_wave, v_cap_wave = pyltspicetest1.run_simulation(
                current_model,
                r9_var.get(),
                r1_var.get(),
                r3_var.get(),
                c1_var.get(),
            )
        except Exception as exc:
            messagebox.showerror("Error", f"Simulation failed: {exc}")
            return

        ax.clear()
        ax.plot(time_wave, v_cap_wave)
        ax.set_title("Output Voltage vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Voltage (V)")
        ax.grid(True)
        canvas.draw()

    run_frame = tk.Frame(controls)
    run_frame.grid(row=0, column=1, padx=5, pady=0, sticky="w")

    run_button = tk.Button(
        run_frame,
        text="RUN",
        command=run_simulation,
        width=10,
    )
    run_button.grid(row=0, column=0, padx=5, pady=0, sticky="w")

    load_button = tk.Button(
        run_frame,
        text="Load Model",
        command=load_model,
        width=10,
    )
    load_button.grid(row=1, column=0, padx=5, pady=2, sticky="w")

    tk.Label(run_frame, textvariable=model_label_var).grid(
        row=1,
        column=1,
        padx=5,
        pady=2,
        sticky="w",
    )

    root.mainloop()


if __name__ == "__main__":
    main()
