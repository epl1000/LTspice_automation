"""Simple wrapper around PyLTSpice to run an op-amp test netlist."""

from PyLTSpice import SpiceEditor, SimRunner, RawRead
from pathlib import Path
import sys
import textwrap
import matplotlib.pyplot as plt
import numpy as np

# Pillow is used to create a placeholder image
from PIL import Image, ImageDraw


def _first_subckt_name(lib_path: Path) -> str:
    """Return the name of the first subcircuit defined in a SPICE library."""

    try:
        with lib_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_stripped = line.strip().lower()
                if line_stripped.startswith(".subckt"):
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
    except OSError:
        pass

    raise ValueError(f"Could not determine subcircuit name from {lib_path}")


def create_placeholder_image(image_path: str | Path) -> Path:
    """Create a PNG with a large red circle and return its path."""

    image_path = Path(image_path).with_suffix(".png")

    size = 200
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)
    radius = size // 2 - 10
    center = (size // 2, size // 2)
    bbox = [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius]
    draw.ellipse(bbox, fill="red")
    img.save(image_path)

    return image_path


def run_simulation(
    lib_path: str | None = None,
    r9_value: str | float = "1k",
    r1_value: str | float = "1k",
    r3_value: str | float = "1k",
    c1_value: str | float = "5p",
    c2_value: str | float = "2p",
    c3_value: str | float = "2p",
    v1_amplitude: str | float = 1.0,
    v1_frequency: str | float = 5e5,
):
    """Run the LTspice simulation using a fixed op-amp test netlist.

    Parameters
    ----------
    lib_path:
        Optional path to an op-amp ``.lib`` model file. When provided, the
        ``.include`` statement in the generated netlist will reference this
        absolute path. Otherwise the short file name ``lm7171.lib`` is used and
        the model is assumed to define the ``LM7171`` subcircuit.
    r9_value:
        Value of the gain resistor ``R9``.
    r1_value:
        Value of the input resistor ``R1``.
    r3_value:
        Value of the load resistor ``R3``.
    c1_value:
        Value of the feedback capacitor ``C1``.
    c2_value:
        Value of the input capacitor ``C2``.
    c3_value:
        Value of the load capacitor ``C3``.
    v1_amplitude:
        Peak value of the input pulse source ``V1`` in volts.
    v1_frequency:
        Frequency of the input pulse source ``V1`` in hertz.

    Returns
    -------
    tuple
        ``(time_wave, v_cap_wave, slew_rate_90_10, slew_rate_80_20, settling_time)``
        where the slew rates are in V/s and settling time is in seconds.
    """

    # --- 1. Define the Netlist Content ---
    # Use a raw string so backslashes in the Windows path are not interpreted as
    # escape sequences.  This avoids a ``SyntaxWarning: invalid escape sequence``
    # when the file is executed on Windows.
    include_path = Path(lib_path) if lib_path is not None else Path("lm7171.lib")
    include_line = (
        f'.include "{include_path.as_posix()}"'
        if include_path.is_absolute()
        else f".include {include_path.as_posix()}"
    )
    try:
        subckt_name = _first_subckt_name(include_path)
    except Exception:
        subckt_name = "LM7171"

    period = 1 / float(v1_frequency)
    ton = period / 2

    netlist_lines = [
        "* E:\\LTSpice_Models\\activeBP2 - Copy\\opamptest1.asc",
        "V4 VCC 0 12",
        "V5 -VCC 0 -12",
        f"R9 Vout N001 {r9_value}",
        f"XU2 N002 N001 VCC -VCC Vout {subckt_name}",
        f"R3 Vout 0 {r3_value}",
        f"V1 N002 0 PULSE(0 {v1_amplitude} 0 1n 1n {ton} {period})",
        f"R1 N001 0 {r1_value}",
        f"C1 Vout N001 {c1_value}",
        f"C2 N002 0 {c2_value}",
        f"C3 Vout 0 {c3_value}",
        include_line,
        "* .ac dec 100 1K 20000K",
        ".tran 5u",
        ".backanno",
        ".end",
    ]
    netlist_content = "\n".join(netlist_lines)

    # Define file names
    netlist_file_name = "opamp_test.net"
    output_folder = "temp_sim_output"  # PyLTspice will create this if it doesn't exist

    # --- 2. Manually create and write the netlist file first ---
    print(f"Creating and writing netlist content to file: {netlist_file_name}")
    try:
        with open(netlist_file_name, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(netlist_content))
        print(f"Netlist file '{netlist_file_name}' created and written successfully.")
    except IOError as e:
        print(f"FATAL ERROR: Could not write netlist file {netlist_file_name}: {e}")
        raise

    # --- 3. Initialize SpiceEditor with the NOW EXISTING file ---
    print(f"Initializing SpiceEditor with existing file: {netlist_file_name}")
    try:
        netlist_editor_obj = SpiceEditor(netlist_file_name)
        # The netlist file has already been written to disk so simply
        # initialize the editor with it. Some PyLTSpice versions expose a
        # ``save`` or ``save_netlist`` method while others do not. Since we do
        # not modify the netlist contents here, saving is optional and skipped
        # if the method is unavailable.
        save_fn = getattr(netlist_editor_obj, "save", None)
        if callable(save_fn):
            save_fn()
        else:
            # ``save_netlist`` has changed signatures across PyLTSpice
            # versions.  Prefer calling it without arguments first and,
            # if that fails, retry passing the current netlist file name.
            save_netlist_fn = getattr(netlist_editor_obj, "save_netlist", None)
            if callable(save_netlist_fn):
                try:
                    save_netlist_fn()
                except TypeError:
                    save_netlist_fn(netlist_file_name)
        print("SpiceEditor initialized.")
    except Exception as e:
        print(
            f"FATAL ERROR: Could not initialize SpiceEditor with file {netlist_file_name}: {e}"
        )
        raise

    # --- 4. Run the LTSpice Simulation (modern API) ---
    print(f"\nRunning simulation for {netlist_file_name}...")

    runner = SimRunner(output_folder=output_folder)

    try:
        # run_now blocks until LTspice finishes and
        # returns (raw_path, log_path) as pathlib.Path objects
        raw_file_path, log_file_path = runner.run_now(netlist_editor_obj)
        print("LTSpice simulation completed successfully.")
    except Exception as e:
        print(f"Error: LTSpice simulation failed – {e}")
        raise

    if raw_file_path is None:
        raise RuntimeError("LTspice did not generate a raw output file")

    print(f"Simulation output (raw file): {raw_file_path}")

    # --- 5. Read the Simulation Output File ---
    print("\nReading simulation output...")
    try:
        raw_data = RawRead(str(raw_file_path))
    except Exception as e:
        print(f"Error reading raw file {raw_file_path}: {e}")
        raise
    print("Raw file read successfully.")

    # --- 6. Get a Specific Trace ---
    trace_name_capacitor_voltage = "V(vout)"

    available_traces = raw_data.get_trace_names()
    trace_name_lower = trace_name_capacitor_voltage.lower()
    available_traces_lower = [name.lower() for name in available_traces]

    if trace_name_lower in available_traces_lower:
        actual_trace_name = available_traces[
            available_traces_lower.index(trace_name_lower)
        ]
        print(f"\nGetting trace: {actual_trace_name}")
        v_cap = raw_data.get_trace(actual_trace_name)
        time_trace = raw_data.get_trace("time")

        print(f"\nData for {trace_name_capacitor_voltage}:")
        print("Time (s)       | Voltage (V)")
        print("----------------|---------------")
        for i in range(min(10, len(time_trace.get_wave()))):
            print(f"{time_trace.get_wave()[i]:<15.6e} | {v_cap.get_wave()[i]:<15.6e}")

        time_wave = time_trace.get_wave()
        v_cap_wave = v_cap.get_wave()

        # --- 7. Calculate slew rate and settling time ---
        time_arr = np.array(time_wave)
        v_arr = np.array(v_cap_wave)

        v_low = float(v_arr.min())
        v_high = float(v_arr.max())
        swing = v_high - v_low
        v_10 = v_low + 0.1 * swing
        v_90 = v_low + 0.9 * swing
        v_20 = v_low + 0.2 * swing
        v_80 = v_low + 0.8 * swing

        # Find 10% and 90% crossing using linear interpolation
        t_10 = None
        t_20 = None
        for i in range(len(v_arr) - 1):
            if t_10 is None and v_arr[i] <= v_10 and v_arr[i + 1] >= v_10:
                t_10 = np.interp(v_10, v_arr[i : i + 2], time_arr[i : i + 2])
                start_idx_10 = i
            if t_20 is None and v_arr[i] <= v_20 and v_arr[i + 1] >= v_20:
                t_20 = np.interp(v_20, v_arr[i : i + 2], time_arr[i : i + 2])
                start_idx_20 = i
            if t_10 is not None and t_20 is not None:
                break

        t_90 = None
        if t_10 is not None:
            for j in range(start_idx_10, len(v_arr) - 1):
                if v_arr[j] <= v_90 and v_arr[j + 1] >= v_90:
                    t_90 = np.interp(v_90, v_arr[j : j + 2], time_arr[j : j + 2])
                    break
        t_80 = None
        if t_20 is not None:
            for j in range(start_idx_20, len(v_arr) - 1):
                if v_arr[j] <= v_80 and v_arr[j + 1] >= v_80:
                    t_80 = np.interp(v_80, v_arr[j : j + 2], time_arr[j : j + 2])
                    break

        if t_10 is not None and t_90 is not None and t_90 > t_10:
            slew_rate_90_10 = (v_90 - v_10) / (t_90 - t_10)
        else:
            slew_rate_90_10 = float("nan")

        if t_20 is not None and t_80 is not None and t_80 > t_20:
            slew_rate_80_20 = (v_80 - v_20) / (t_80 - t_20)
        else:
            slew_rate_80_20 = float("nan")

        # Settling time estimation using derivative threshold
        settling_time = float("nan")
        if t_90 is not None:
            grad = np.gradient(v_arr, time_arr)
            max_grad = np.max(np.abs(grad))
            if max_grad > 0:
                thresh = 0.01 * max_grad
                for k in range(len(time_arr)):
                    if time_arr[k] >= t_90 and np.all(np.abs(grad[k:k+5]) < thresh):
                        settling_time = time_arr[k] - t_90
                        break

        return (
            time_wave,
            v_cap_wave,
            slew_rate_90_10,
            slew_rate_80_20,
            settling_time,
        )
    else:
        print(
            f"\nError: Trace '{trace_name_capacitor_voltage}' not found in the raw file."
        )
        print("Available traces:", available_traces)
        raise ValueError(f"Trace '{trace_name_capacitor_voltage}' not found")


def main():
    """Run the simulation and display a matplotlib plot."""

    lib_path = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        time_wave, v_cap_wave, sr_90_10, sr_80_20, settling_time = run_simulation(lib_path)
    except Exception:
        sys.exit(1)

    # Plot voltage vs time using matplotlib
    plt.figure()
    plt.plot(time_wave, v_cap_wave)
    plt.title("Output Voltage vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.grid(True)
    plt.show()

    print(f"90-10 Slew Rate: {sr_90_10 / 1e6:.3f} V/us")
    print(f"80-20 Slew Rate: {sr_80_20 / 1e6:.3f} V/us")
    print(f"Settling Time: {settling_time * 1e6:.3f} us")

    print("\nBasic PyLTspice example finished.")


if __name__ == "__main__":
    main()
