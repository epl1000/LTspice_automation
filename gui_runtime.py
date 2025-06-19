import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
from datetime import datetime

from report import generate_pdf_report

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from matplotlib.ticker import FuncFormatter
from PIL import Image, ImageTk
from PIL.Image import Image as PilImage
import io
import schemdraw
import schemdraw.elements as elm
import math
import numpy as np

import pyltspicetest1

# Spinner constants
ONE_PF = 1e-12


def _format_value(value: float, unit: str) -> str:
    """Return *value* formatted using engineering prefixes."""

    if value == 0:
        return f"0 {unit}"

    exp = int(math.floor(math.log10(abs(value)) / 3) * 3)
    exp = max(min(exp, 12), -12)
    prefixes = {
        -12: "p",
        -9: "n",
        -6: "\u03bc",
        -3: "m",
        0: "",
        3: "k",
        6: "M",
        9: "G",
        12: "T",
    }
    scaled = value / (10 ** exp)
    prefix = prefixes.get(exp, "")
    return f"{scaled:g} {prefix}{unit}"


def generate_schematic_image(
    r9_value: float,
    r1_value: float,
    r3_value: float,
    c1_value: float,
    c2_value: float,
    c3_value: float,
    v1_amplitude: float,
    v1_frequency: float,
    opamp_model: str = "LM7171",
) -> PilImage:
    """Return a PIL Image of the op-amp test circuit.

    Parameters
    ----------
    opamp_model:
        Text to display on the op-amp symbol.
    """

    d = schemdraw.Drawing(unit=2.2, fontsize=12)

    # --- Op-amp ----------------------------------------------------
    op = d.add(elm.Opamp(w=3.6, h=2.6, label=opamp_model))
    noninv, inv, vout = op.in2, op.in1, op.out

    # --- Inverting input path -------------------------------------
    d.add(elm.Line().at(inv).left().length(1.6))
    tap1 = d.here
    d.add(
        elm.Resistor().label(f"R1\n{_format_value(r1_value, 'Ω')}")
    )
    d.add(elm.Ground())

    d.add(elm.Line().at(tap1).up(2.0))
    tap2 = d.here
    d.add(
        elm.Resistor().right().to(vout).label(f"R9\n{_format_value(r9_value, 'Ω')}")
    )
    d.add(elm.Line().down(2.6))
    d.add(elm.Line().at(tap2).up(2.0))
    d.add(
        elm.Capacitor().right().to(vout).label(
            f"C1\n{_format_value(c1_value, 'F')}", loc='bot'
        )
    )
    d.add(elm.Line().down(4.6))


    # --- Non-inverting input path ---------------------------------
    d.add(elm.Line().at(noninv).left().length(2.5))
    d.add(
        elm.SourceSin().down().label(
            f"V1\n{_format_value(v1_amplitude, 'V')}\n{_format_value(v1_frequency, 'Hz')}"
        )
    )
    d.add(elm.Ground())

    d.add(elm.Line().at(noninv).left().length(0.6))
    d.add(
        elm.Capacitor().down().label(f"C2\n{_format_value(c2_value, 'F')}")
    )
    d.add(elm.Ground())

    # --- Output network -------------------------------------------
    d.add(elm.Line().at(vout).right().length(1.2))
    tap = d.here                                         # save node
    d.add(elm.Dot().at(tap).label('Vout', loc='top'))  # <-- label!

    d.add(
        elm.Resistor().length(2.0).down().label(
            f"R3\n{_format_value(r3_value, 'Ω')}"
        )
    )
    d.add(elm.Ground())

    d.add(elm.Line().at(tap).right(2.0))
    d.add(
        elm.Capacitor().down().label(f"C3\n{_format_value(c3_value, 'F')}")
    )
    d.add(elm.Ground())

    # Draw the schematic without displaying a separate window so the
    # image can be embedded directly in the GUI.
    d.draw(show=False)
    # d.save('opamp_test.svg')  # optional export

    img_bytes = d.get_imagedata('png')
    return Image.open(io.BytesIO(img_bytes))


def main():
    root = tk.Tk()
    root.title("LTspice Runtime")

    # Configure window size: allocate at least half the screen width and at
    # least 1024 pixels so the results area has ample space at startup
    min_width = 1024
    try:
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        min_width = max(screen_width // 2, min_width)
        root.geometry(f"{min_width}x{screen_height}")
    except tk.TclError:
        root.geometry(f"{min_width}x600")

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
    use_sine_var = tk.BooleanVar(value=False)
    tran_var = tk.StringVar(value="5u")
    ac_var = tk.StringVar(value="dec 100 1K 20000K")

    last_schematic_img = None

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
    c1_spinbox.grid(row=0, column=3, padx=5, pady=2, sticky="w")

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
    tk.Spinbox(
        spinner_frame,
        from_=1,
        to=1e6,
        increment=100,
        textvariable=r3_var,
        width=8,
    ).grid(row=1, column=3, padx=5, pady=2, sticky="w")

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

    tk.Checkbutton(
        spinner_frame,
        text="Sine Source",
        variable=use_sine_var,
    ).grid(row=2, column=6, columnspan=2, padx=5, pady=2, sticky="w")

    tk.Label(spinner_frame, text="tran").grid(row=2, column=0, padx=5, pady=2, sticky="w")
    tk.Entry(spinner_frame, textvariable=tran_var, width=10).grid(row=2, column=1, padx=5, pady=2)
    tk.Label(spinner_frame, text="ac").grid(row=2, column=2, padx=5, pady=2, sticky="w")
    tk.Entry(spinner_frame, textvariable=ac_var, width=15).grid(
        row=2, column=3, padx=5, pady=2, sticky="w"
    )

    def show_fft():
        """Display the FFT of the current plot data."""

        nonlocal showing_fft, freq_data, mag_data

        if time_data is None or voltage_data is None:
            messagebox.showinfo("No data", "Run a simulation before performing an FFT.")
            return

        # Determine data range based on current zoom
        x_start, x_end = ax.get_xlim()
        if (
            orig_xlim[0] is not None
            and orig_xlim[1] is not None
            and (x_start != orig_xlim[0] or x_end != orig_xlim[1])
        ):
            mask = (time_data >= min(x_start, x_end)) & (time_data <= max(x_start, x_end))
            t_sel = time_data[mask]
            v_sel = voltage_data[mask]
        else:
            t_sel = time_data
            v_sel = voltage_data

        if len(t_sel) < 2:
            messagebox.showinfo("No data", "Not enough points in view for FFT.")
            return

        # Interpolate to a uniform grid for the FFT calculation
        uniform_t = np.linspace(t_sel[0], t_sel[-1], len(t_sel))
        v_interp = np.interp(uniform_t, t_sel, v_sel)
        dt = uniform_t[1] - uniform_t[0]

        # Apply a Hann window (the default in LTspice) prior to the FFT
        window = np.hanning(len(uniform_t))
        v_detrended = v_interp - np.mean(v_interp)

        # Zero pad to the next power-of-two length for consistent bin spacing
        fft_len = 1 << (len(uniform_t) - 1).bit_length()
        freq = np.fft.rfftfreq(fft_len, dt)
        v_windowed = v_detrended * window
        if fft_len > len(v_windowed):
            v_windowed = np.pad(v_windowed, (0, fft_len - len(v_windowed)))
        else:
            v_windowed = v_windowed[:fft_len]

        fft_vals = np.fft.rfft(v_windowed)
        # Normalize so a 1 Vrms sine equals 0 dBV
        fft_vals = (2 / fft_len) * fft_vals / np.sqrt(2)

        mag_db = 20 * np.log10(np.abs(fft_vals) + np.finfo(float).eps)
        freq = freq[1:]
        mag_db = mag_db[1:]

        # Limit frequency range from 1 kHz to 200 MHz
        min_freq = 1e3
        max_freq = 200e6
        freq_mask = (freq >= min_freq) & (freq <= max_freq)
        freq = freq[freq_mask]
        mag_db = mag_db[freq_mask]

        freq_data = freq
        mag_data = mag_db

        if len(freq) == 0:
            messagebox.showinfo(
                "No data",
                "No frequency components found between 1 kHz and 200 MHz.",
            )
            return

        ax.clear()
        ax.plot(freq, mag_db)
        ax.set_xscale("log")
        ax.set_xlim(min_freq, max_freq)
        ax.set_title("FFT Magnitude")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Magnitude (dB)")

        def fmt_freq(value, _pos):
            if value >= 1e6:
                return f"{value/1e6:g}M"
            if value >= 1e3:
                return f"{value/1e3:g}k"
            return f"{value:g}"

        ax.xaxis.set_major_formatter(FuncFormatter(fmt_freq))
        ax.grid(True)
        canvas.draw()

        showing_fft = True

    tk.Button(spinner_frame, text="FFT", command=show_fft).grid(row=2, column=4, padx=5, pady=2)

    display_frame = tk.Frame(root)
    display_frame.pack(fill=tk.BOTH, expand=True)

    figure = plt.Figure(figsize=(5, 4), dpi=100)
    ax = figure.add_subplot(111)
    canvas = FigureCanvasTkAgg(figure, master=display_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    canvas_widget.focus_set()

    # Store original limits for zoom reset
    orig_xlim = [None, None]
    orig_ylim = [None, None]

    time_data = None
    voltage_data = None
    freq_data = None
    mag_data = None
    showing_fft = False
    pan_start = None
    pan_transform = None

    def onselect(eclick, erelease):
        """Zoom the plot to the rectangle drawn with the left mouse button."""
        if (
            (eclick.key is not None and "control" in str(eclick.key).lower())
            or (
                erelease.key is not None
                and "control" in str(erelease.key).lower()
            )
        ):
            return
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        if None in (x1, y1, x2, y2):
            return
        ax.set_xlim(min(x1, x2), max(x1, x2))
        ax.set_ylim(min(y1, y2), max(y1, y2))
        canvas.draw()

    rect_selector = RectangleSelector(
        ax,
        onselect,
        button=[1],  # Left mouse button only
        useblit=True,
        props=dict(
            facecolor="none",
            edgecolor="black",
            linestyle=":",
            linewidth=1,
        ),
    )
    # Disable the built-in "center" mode which is toggled with CTRL. This
    # prevents the selector from interpreting the first click as the rectangle
    # center after panning with the CTRL key held down.
    try:
        rect_selector.remove_state("center")
    except (ValueError, KeyError):
        # Older Matplotlib versions may not support removing states or
        # the state might not exist in newer versions.
        pass

    ctrl_pressed = False
    grid_disabled = False

    def on_key_press(event) -> None:
        """Disable zoom rectangle when CTRL is pressed."""
        nonlocal ctrl_pressed
        if event.key is not None and "control" in str(event.key).lower():
            ctrl_pressed = True
            rect_selector.set_active(False)

    def on_key_release(event) -> None:
        """Re-enable zoom rectangle after CTRL release."""
        nonlocal ctrl_pressed, grid_disabled, pan_start
        if event.key is not None and "control" in str(event.key).lower():
            ctrl_pressed = False
            if pan_start is None:
                rect_selector.set_active(True)
            if grid_disabled:
                ax.grid(True)
                grid_disabled = False
                canvas.draw_idle()

    canvas.mpl_connect("key_press_event", on_key_press)
    canvas.mpl_connect("key_release_event", on_key_release)

    ctrl_pressed = False

    def key_press_event(event):
        nonlocal ctrl_pressed
        if event.key is not None and "control" in str(event.key).lower():
            ctrl_pressed = True
            rect_selector.set_active(False)

    def key_release_event(event):
        nonlocal ctrl_pressed
        if event.key is not None and "control" in str(event.key).lower():
            ctrl_pressed = False
            rect_selector.set_active(True)

    canvas.mpl_connect("key_press_event", key_press_event)
    canvas.mpl_connect("key_release_event", key_release_event)

    def plot_time_domain() -> None:
        """Plot the stored time-domain data."""

        nonlocal showing_fft, orig_xlim, orig_ylim

        if time_data is None or voltage_data is None:
            return

        ax.clear()
        ax.plot(time_data, voltage_data)
        ax.set_title("Output Voltage vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Voltage (V)")
        ax.grid(True)
        canvas.draw()

        orig_xlim[0], orig_xlim[1] = ax.get_xlim()
        orig_ylim[0], orig_ylim[1] = ax.get_ylim()
        showing_fft = False

    def reset_zoom(event):
        """Reset zoom or exit FFT on right-click."""
        if event.button != 3:
            return

        if showing_fft:
            plot_time_domain()
        elif orig_xlim[0] is not None:
            ax.set_xlim(orig_xlim)
            ax.set_ylim(orig_ylim)
            canvas.draw()

    canvas.mpl_connect("button_press_event", reset_zoom)

    def pan_start_event(event):
        """Begin panning when CTRL + left mouse button is pressed."""
        nonlocal pan_start, pan_transform, grid_disabled
        if event.button != 1 or not ctrl_pressed:
            return

        if orig_xlim[0] is None:
            return

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        if (
            cur_xlim[0] == orig_xlim[0]
            and cur_xlim[1] == orig_xlim[1]
            and cur_ylim[0] == orig_ylim[0]
            and cur_ylim[1] == orig_ylim[1]
        ):
            return

        if event.x is None or event.y is None:
            return

        pan_start = (event.x, event.y, cur_xlim, cur_ylim)
        pan_transform = ax.transData.frozen()
        rect_selector.set_active(False)
        ax.grid(False)
        grid_disabled = True
        canvas.draw_idle()

    def pan_move_event(event):
        """Update the axes limits while panning."""
        nonlocal pan_start, pan_transform
        if pan_start is None or event.x is None or event.y is None:
            return

        dx_pix = event.x - pan_start[0]
        dy_pix = event.y - pan_start[1]
        start_xlim, start_ylim = pan_start[2], pan_start[3]

        inv = pan_transform.inverted()
        start_pt = inv.transform((0, 0))
        cur_pt = inv.transform((dx_pix, dy_pix))
        dx = start_pt[0] - cur_pt[0]
        dy = start_pt[1] - cur_pt[1]

        ax.set_xlim(start_xlim[0] + dx, start_xlim[1] + dx)
        ax.set_ylim(start_ylim[0] + dy, start_ylim[1] + dy)
        canvas.draw_idle()

    def pan_end_event(event):
        """End the panning interaction."""
        nonlocal pan_start, pan_transform, grid_disabled
        if event.button == 1 and pan_start is not None:
            pan_start = None
            pan_transform = None
            if not ctrl_pressed:
                rect_selector.set_active(True)
                ax.grid(True)
                grid_disabled = False
                canvas.draw_idle()

    canvas.mpl_connect("button_press_event", pan_start_event)
    canvas.mpl_connect("motion_notify_event", pan_move_event)
    canvas.mpl_connect("button_release_event", pan_end_event)

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

    # Display the schemdraw circuit diagram at startup using initial values
    schematic_img = generate_schematic_image(
        r9_var.get(),
        r1_var.get(),
        r3_var.get(),
        c1_var.get(),
        c2_var.get(),
        c3_var.get(),
        v1_amp_var.get(),
        v1_freq_var.get(),
        Path(current_model).stem if current_model else "LM7171",
    )
    img_width, img_height = schematic_img.size
    tk_img = ImageTk.PhotoImage(schematic_img)
    schematic_label.configure(image=tk_img)
    schematic_label.image = tk_img

    last_schematic_img = schematic_img

    # Resize the window so the image is shown at its natural size
    root.update_idletasks()
    canvas_width = canvas_widget.winfo_width() or int(
        figure.get_figwidth() * figure.get_dpi()
    )
    new_width = max(canvas_width + img_width + 20, min_width)
    current_height = root.winfo_height()
    root.geometry(f"{new_width}x{current_height}")

    def load_model():
        """Prompt for an op-amp model file and remember the selection."""

        nonlocal current_model
        lib_path = filedialog.askopenfilename(
            title="Select op-amp model",
            filetypes=[("SPICE model", "*.lib *.txt"), ("All files", "*.*")],
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

        nonlocal orig_xlim, orig_ylim, time_data, voltage_data, freq_data, mag_data, showing_fft, last_schematic_img

        if not current_model:
            messagebox.showinfo(
                "No model loaded",
                "Please load an op-amp model before running the simulation.",
            )
            return

        # Update the schematic diagram with the current spinner values
        schematic_img = generate_schematic_image(
            r9_var.get(),
            r1_var.get(),
            r3_var.get(),
            c1_var.get(),
            c2_var.get(),
            c3_var.get(),
            v1_amp_var.get(),
            v1_freq_var.get(),
            Path(current_model).stem,
        )
        tk_img_local = ImageTk.PhotoImage(schematic_img)
        schematic_label.configure(image=tk_img_local)
        schematic_label.image = tk_img_local
        last_schematic_img = schematic_img

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
                use_sine_var.get(),
                tran_var.get(),
            )
        except Exception as exc:
            messagebox.showerror("Error", f"Simulation failed: {exc}")
            return

        time_data = np.array(time_wave)
        voltage_data = np.array(v_cap_wave)
        freq_data = None
        mag_data = None

        plot_time_domain()

        slew_label_var.set(f"90-10 Slew Rate: {sr_90_10/1e6:.3f} V/us")
        slew80_label_var.set(f"80-20 Slew Rate: {sr_80_20/1e6:.3f} V/us")
        settling_label_var.set(f"Settling Time: {settling_time * 1e6:.3f} us")

    run_frame = tk.Frame(controls)
    run_frame.grid(row=0, column=1, padx=5, pady=0, sticky="w")

    append_var = tk.BooleanVar(value=False)
    current_report_file: str | None = None

    def save_pdf() -> None:
        """Save a PDF report of the current results."""

        nonlocal current_report_file

        meas = [
            s
            for s in (
                slew_label_var.get(),
                slew80_label_var.get(),
                settling_label_var.get(),
            )
            if s
        ]

        if current_report_file is None or not append_var.get():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_report_file = f"simulation_report_{timestamp}.pdf"

        try:
            cur_xlim = ax.get_xlim()
            cur_ylim = ax.get_ylim()
            is_log = ax.get_xscale() == "log"
            time_xlim = cur_xlim if not is_log and time_data is not None else None
            time_ylim = cur_ylim if not is_log and time_data is not None else None
            freq_xlim = cur_xlim if is_log and freq_data is not None else None
            freq_ylim = cur_ylim if is_log and freq_data is not None else None

            generate_pdf_report(
                current_report_file,
                time_data=time_data,
                voltage_data=voltage_data,
                freq_data=freq_data,
                mag_data=mag_data,
                measurements=meas,
                schematic_image=last_schematic_img,
                append=append_var.get(),
                freq_plot_title="FFT Magnitude" if showing_fft else "AC Magnitude",
                time_xlim=time_xlim,
                time_ylim=time_ylim,
                freq_xlim=freq_xlim,
                freq_ylim=freq_ylim,
            )
            messagebox.showinfo(
                "PDF Saved", f"Report written to {current_report_file}"
            )
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to generate PDF: {exc}")

    run_button = tk.Button(
        run_frame,
        text="RUN",
        command=run_simulation,
        width=10,
    )
    run_button.grid(row=0, column=0, padx=5, pady=0, sticky="w")

    save_button = tk.Button(
        run_frame,
        text="Save PDF",
        command=save_pdf,
        width=10,
    )
    save_button.grid(row=0, column=1, padx=5, pady=0, sticky="w")

    def run_ac():
        """Run an AC simulation and plot the frequency response."""

        nonlocal orig_xlim, orig_ylim, time_data, voltage_data, freq_data, mag_data, showing_fft, last_schematic_img

        if not current_model:
            messagebox.showinfo(
                "No model loaded",
                "Please load an op-amp model before running the simulation.",
            )
            return

        schematic_img = generate_schematic_image(
            r9_var.get(),
            r1_var.get(),
            r3_var.get(),
            c1_var.get(),
            c2_var.get(),
            c3_var.get(),
            v1_amp_var.get(),
            v1_freq_var.get(),
            Path(current_model).stem,
        )
        tk_img_local = ImageTk.PhotoImage(schematic_img)
        schematic_label.configure(image=tk_img_local)
        schematic_label.image = tk_img_local
        last_schematic_img = schematic_img

        try:
            freq_wave, mag_db = pyltspicetest1.run_ac_simulation(
                current_model,
                r9_var.get(),
                r1_var.get(),
                r3_var.get(),
                c1_var.get(),
                c2_var.get(),
                c3_var.get(),
                ac_var.get(),
            )
        except Exception as exc:
            messagebox.showerror("Error", f"AC simulation failed: {exc}")
            return

        ax.clear()
        ax.plot(np.array(freq_wave), np.array(mag_db))
        ax.set_xscale("log")
        ax.set_title("AC Magnitude")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Magnitude (dB)")
        ax.grid(True)
        canvas.draw()

        time_data = None
        voltage_data = None
        freq_data = np.array(freq_wave)
        mag_data = np.array(mag_db)
        orig_xlim[0], orig_xlim[1] = ax.get_xlim()
        orig_ylim[0], orig_ylim[1] = ax.get_ylim()
        showing_fft = False

        slew_label_var.set("")
        slew80_label_var.set("")
        settling_label_var.set("")

    run_ac_button = tk.Button(
        run_frame,
        text="RUN AC",
        command=run_ac,
        width=10,
    )
    run_ac_button.grid(row=1, column=0, padx=5, pady=2, sticky="w")

    tk.Checkbutton(
        run_frame,
        text="Append to report",
        variable=append_var,
    ).grid(row=1, column=1, padx=5, pady=2, sticky="w")

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
    load_button.grid(row=2, column=0, padx=5, pady=2, sticky="w")

    tk.Label(run_frame, textvariable=model_label_var).grid(
        row=2,
        column=1,
        padx=5,
        pady=2,
        sticky="w",
    )

    root.mainloop()


if __name__ == "__main__":
    main()
