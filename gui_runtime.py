import tkinter as tk
from tkinter import messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

import pyltspicetest1


def main():
    root = tk.Tk()
    root.title("LTspice Runtime")
    # Attempt to launch the window maximized
    try:
        root.state("zoomed")
    except tk.TclError:
        root.geometry("800x600")

    figure = plt.Figure(figsize=(5, 4), dpi=100)
    ax = figure.add_subplot(111)
    canvas = FigureCanvasTkAgg(figure, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=True)

    def run_simulation():
        """Run the LTspice simulation and plot the results."""
        try:
            time_wave, v_cap_wave = pyltspicetest1.run_simulation()
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

    run_button = tk.Button(root, text="RUN", command=run_simulation)
    run_button.pack(padx=20, pady=20)

    root.mainloop()


if __name__ == "__main__":
    main()
