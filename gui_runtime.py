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



    def run_simulation():
        """Run the LTspice simulation and plot the results."""
        try:
            time_wave, v_cap_wave = pyltspicetest1.run_simulation()
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

    run_button = tk.Button(controls, text="RUN", command=run_simulation)
    run_button.grid(row=0, column=0, padx=5, pady=0, sticky="w")

    root.mainloop()


if __name__ == "__main__":
    main()
