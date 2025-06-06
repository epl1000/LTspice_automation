from PyLTSpice import SpiceEditor, SimRunner, RawRead
import sys
import textwrap
import matplotlib.pyplot as plt


def run_simulation(freq_hz=1e3, resistor_ohm=1e3, capacitor_f=1e-6, stop_time_s=5e-3):
    """Run the LTspice simulation with the provided values.

    Parameters
    ----------
    freq_hz : float, optional
        Sine source frequency in Hertz.
    resistor_ohm : float, optional
        Resistance value in Ohms.
    capacitor_f : float, optional
        Capacitance value in Farads.
    stop_time_s : float, optional
        Transient analysis stop time in seconds.
    """

    # --- 1. Define the Netlist Content ---
    step_time = stop_time_s / 1000 if stop_time_s > 0 else 1e-6
    netlist_content = f"""* Simple RC Circuit
    V1 N001 0 SINE(0 1 {freq_hz}) ; Voltage source: 1V amplitude
    R1 N001 N002 {resistor_ohm}
    C1 N002 0 {capacitor_f}
    .tran 0 {stop_time_s} 0 {step_time}
    .end
    """

    # Define file names
    netlist_file_name = "simple_rc.net"
    output_folder = "temp_sim_output"   # PyLTspice will create this if it doesn't exist

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
        # Older PyLTSpice versions don't implement ``set_text``. Since the
        # netlist has already been written to disk above, simply load the file
        # with ``SpiceEditor`` and keep it unchanged.
        netlist_editor_obj.save()
        print("SpiceEditor initialized.")
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize SpiceEditor with file {netlist_file_name}: {e}")
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

    print(f"Simulation output (raw file): {raw_file_path}")

    # --- 5. Read the Simulation Output File ---
    print("\nReading simulation output...")
    try:
        raw_data = RawRead(raw_file_path)
    except Exception as e:
        print(f"Error reading raw file {raw_file_path}: {e}")
        raise
    print("Raw file read successfully.")

    # --- 6. Get a Specific Trace ---
    trace_name_capacitor_voltage = "V(N002)"

    available_traces = raw_data.get_trace_names()
    trace_name_lower = trace_name_capacitor_voltage.lower()
    available_traces_lower = [name.lower() for name in available_traces]

    if trace_name_lower in available_traces_lower:
        actual_trace_name = available_traces[available_traces_lower.index(trace_name_lower)]
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
        return time_wave, v_cap_wave
    else:
        print(f"\nError: Trace '{trace_name_capacitor_voltage}' not found in the raw file.")
        print("Available traces:", available_traces)
        raise ValueError(f"Trace '{trace_name_capacitor_voltage}' not found")


def main():
    """Run the simulation and display a matplotlib plot."""

    try:
        time_wave, v_cap_wave = run_simulation()
    except Exception:
        sys.exit(1)

    # Plot voltage vs time using matplotlib
    plt.figure()
    plt.plot(time_wave, v_cap_wave)
    plt.title("Capacitor Voltage vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.grid(True)
    plt.show()

    print("\nBasic PyLTspice example finished.")

if __name__ == "__main__":
    main()
