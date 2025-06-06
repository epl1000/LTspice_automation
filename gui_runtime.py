import tkinter as tk
from tkinter import messagebox

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

    figure = plt.Figure(figsize=(5, 4), dpi=100)
    ax = figure.add_subplot(111)
    canvas = FigureCanvasTkAgg(figure, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=True)

    freq_var = tk.DoubleVar(value=1000)
    tk.Label(controls, text="Frequency (Hz)").grid(row=0, column=0, sticky="e")
    freq_spin = tk.Spinbox(controls, from_=10, to=100000, increment=10,
                           textvariable=freq_var, width=10)
    freq_spin.grid(row=0, column=1, sticky="w")

    res_var = tk.DoubleVar(value=1000)
    tk.Label(controls, text="Resistor (Ohm)").grid(row=0, column=2, sticky="e")
    res_spin = tk.Spinbox(controls, from_=100, to=10000, increment=100,
                          textvariable=res_var, width=10)
    res_spin.grid(row=0, column=3, sticky="w")

    cap_var = tk.DoubleVar(value=1.0)
    tk.Label(controls, text="Capacitor (uF)").grid(row=1, column=0, sticky="e")
    cap_spin = tk.Spinbox(controls, from_=0.1, to=10.0, increment=0.1,
                          textvariable=cap_var, width=10)
    cap_spin.grid(row=1, column=1, sticky="w")

    time_var = tk.DoubleVar(value=5.0)
    tk.Label(controls, text="Stop Time (ms)").grid(row=1, column=2, sticky="e")
    time_spin = tk.Spinbox(controls, from_=1.0, to=100.0, increment=1.0,
                           textvariable=time_var, width=10)
    time_spin.grid(row=1, column=3, sticky="w")

    def run_simulation():
        """Run the LTspice simulation and plot the results using current settings."""
        freq = freq_var.get()
        res = res_var.get()
        cap = cap_var.get() * 1e-6  # convert uF to F
        stop_t = time_var.get() * 1e-3  # convert ms to s
        try:
            time_wave, v_cap_wave = pyltspicetest1.run_simulation(
                freq_hz=freq,
                resistor_ohm=res,
                capacitor_f=cap,
                stop_time_s=stop_t,
            )
        except Exception as exc:
            messagebox.showerror("Error", f"Simulation failed: {exc}")
            return

        ax.clear()
        ax.plot(time_wave, v_cap_wave)
        ax.set_title("Capacitor Voltage vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Voltage (V)")
        ax.grid(True)
        canvas.draw()

    run_button = tk.Button(controls, text="RUN", command=run_simulation)
    run_button.grid(row=0, column=4, rowspan=2, padx=(10, 0), pady=0, sticky="ns")

    root.mainloop()


if __name__ == "__main__":
    main()
