import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

import pyltspicetest1

# Spinner constants
ONE_PF = 1e-12


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
    c2_var = tk.DoubleVar(value=2e-12)
    c3_var = tk.DoubleVar(value=2e-12)
    v1_amp_var = tk.DoubleVar(value=1.0)
    v1_freq_var = tk.DoubleVar(value=5e5)

    tk.Label(spinner_frame, text="R9 (FB)").grid(row=0, column=0, padx=5, pady=2, sticky="w")
    tk.Spinbox(spinner_frame, from_=1, to=1e6, increment=100, textvariable=r9_var, width=8).grid(row=0, column=1, padx=5, pady=2)
    tk.Label(spinner_frame, text="C1 (FB)").grid(row=0, column=2, padx=5, pady=2, sticky="w")
    # The default Spinbox ``format`` uses ``%f`` with six decimal digits.  With
    # the picofarad values used for C1 this results in all values being rendered
    # as ``0.000000`` so it appears as if the widget does not change when the
    # arrows are pressed.  Using ``%g`` preserves scientific notation without
    # relying on the ``%e`` specifier, which is known to cause ``TclError`` on
    # some Tcl/Tk versions.
    try:
        c1_spinbox = tk.Spinbox(
            spinner_frame,
            from_=ONE_PF,
            to=1e-6,
            increment=ONE_PF,
            format="%g",
            textvariable=c1_var,
            width=8,
        )
    except tk.TclError:
        # Older Tk versions do not recognise the "%g" format specifier.
        # Fallback to the default format which may display values as 0.000000
        # for very small numbers, but at least avoids raising an exception.
        c1_spinbox = tk.Spinbox(
            spinner_frame,
            from_=ONE_PF,
            to=1e-6,
            increment=ONE_PF,
            textvariable=c1_var,
            width=8,
        )
    c1_spinbox.grid(row=0, column=3, padx=5, pady=2)

    tk.Label(spinner_frame, text="C input").grid(row=0, column=4, padx=5, pady=2, sticky="w")
    try:
        c2_spinbox = tk.Spinbox(
            spinner_frame,
            from_=ONE_PF,
            to=1e-6,
            increment=ONE_PF,
            format="%g",
            textvariable=c2_var,
            width=8,
        )
    except tk.TclError:
        c2_spinbox = tk.Spinbox(
            spinner_frame,
            from_=ONE_PF,
            to=1e-6,
            increment=ONE_PF,
            textvariable=c2_var,
            width=8,
        )
    c2_spinbox.grid(row=0, column=5, padx=5, pady=2)

    tk.Label(spinner_frame, text="R1").grid(row=1, column=0, padx=5, pady=2, sticky="w")
    tk.Spinbox(spinner_frame, from_=1, to=1e6, increment=100, textvariable=r1_var, width=8).grid(row=1, column=1, padx=5, pady=2)
    tk.Label(spinner_frame, text="R3 (Load Ω)").grid(row=1, column=2, padx=5, pady=2, sticky="w")
    tk.Spinbox(spinner_frame, from_=1, to=1e6, increment=100, textvariable=r3_var, width=8).grid(row=1, column=3, padx=5, pady=2)

    tk.Label(spinner_frame, text="C load").grid(row=1, column=4, padx=5, pady=2, sticky="w")
    try:
        c3_spinbox = tk.Spinbox(
            spinner_frame,
            from_=ONE_PF,
            to=1e-6,
            increment=ONE_PF,
            format="%g",
            textvariable=c3_var,
            width=8,
        )
    except tk.TclError:
        c3_spinbox = tk.Spinbox(
            spinner_frame,
            from_=ONE_PF,
            to=1e-6,
            increment=ONE_PF,
            textvariable=c3_var,
            width=8,
        )
    c3_spinbox.grid(row=1, column=5, padx=5, pady=2)

    tk.Label(spinner_frame, text="V1 Amp").grid(row=0, column=6, padx=5, pady=2, sticky="w")
    tk.Spinbox(
        spinner_frame,
        from_=0.0,
        to=10.0,
        increment=0.1,
        textvariable=v1_amp_var,
        width=8,
    ).grid(row=0, column=7, padx=5, pady=2)

    tk.Label(spinner_frame, text="V1 Freq (Hz)").grid(row=1, column=6, padx=5, pady=2, sticky="w")
    tk.Spinbox(
        spinner_frame,
        from_=1.0,
        to=1e7,
        increment=1000.0,
        textvariable=v1_freq_var,
        width=8,
    ).grid(row=1, column=7, padx=5, pady=2)

    display_frame = tk.Frame(root)
    display_frame.pack(fill=tk.BOTH, expand=True)

    figure = plt.Figure(figsize=(5, 4), dpi=100)
    ax = figure.add_subplot(111)
    canvas = FigureCanvasTkAgg(figure, master=display_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    schematic_label = tk.Label(display_frame)
    schematic_label.pack(side=tk.LEFT, fill=tk.BOTH, padx=10)

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

    slew_label_var = tk.StringVar()
    slew80_label_var = tk.StringVar()
    settling_label_var = tk.StringVar()

    def run_simulation():
        """Run the simulation using the currently loaded model."""

        if not current_model:
            messagebox.showinfo(
                "No model loaded",
                "Please load an op-amp model before running the simulation.",
            )
            return

        try:
            time_wave, v_cap_wave, sr_90_10, sr_80_20, settling_time = pyltspicetest1.run_simulation(
                current_model,
                r9_var.get(),
                r1_var.get(),
                r3_var.get(),
                c1_var.get(),
                c2_var.get(),
                c3_var.get(),
                v1_amp_var.get(),
                v1_freq_var.get(),
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

        try:
            img_path = pyltspicetest1.create_placeholder_image("placeholder.png")
            img = tk.PhotoImage(file=str(img_path))
            schematic_label.configure(image=img)
            schematic_label.image = img
        except Exception:
            schematic_label.configure(text="Image unavailable")

        slew_label_var.set(f"90-10 Slew Rate: {sr_90_10/1e6:.3f} V/us")
        slew80_label_var.set(f"80-20 Slew Rate: {sr_80_20/1e6:.3f} V/us")
        settling_label_var.set(f"Settling Time: {settling_time * 1e6:.3f} us")

    run_frame = tk.Frame(controls)
    run_frame.grid(row=0, column=1, padx=5, pady=0, sticky="w")

    run_button = tk.Button(
        run_frame,
        text="RUN",
        command=run_simulation,
        width=10,
    )
    run_button.grid(row=0, column=0, padx=5, pady=0, sticky="w")

    tk.Label(run_frame, textvariable=slew_label_var).grid(
        row=0,
        column=2,
        padx=5,
        pady=2,
        sticky="w",
    )

    tk.Label(run_frame, textvariable=slew80_label_var).grid(
        row=1,
        column=2,
        padx=5,
        pady=2,
        sticky="w",
    )

    tk.Label(run_frame, textvariable=settling_label_var).grid(
        row=0,
        column=3,
        padx=5,
        pady=2,
        sticky="w",
    )

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
