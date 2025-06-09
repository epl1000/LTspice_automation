"""Simple wrapper around PyLTSpice to run an op-amp test netlist."""

from PyLTSpice import SpiceEditor, SimRunner, RawRead
import sys
import textwrap
import matplotlib.pyplot as plt


def run_simulation():
    """Run the LTspice simulation using a fixed op-amp test netlist."""

    # --- 1. Define the Netlist Content ---
    netlist_content = textwrap.dedent("""* E:\LTSpice_Models\activeBP2 - Copy\opamptest1.asc
V4 VCC 0 12
V5 -VCC 0 -12
R9 Vout N001 1k
XU2 N003 N001 VCC -VCC Vout LM7171
R3 Vout 0 1K
V1 N002 0 PULSE(0 1 0 1n 1n 1u 2u)
R1 N003 N002 500
C1 Vout N001 5p
.include lm7171.lib
* .ac dec 100 1K 20000K
.tran 5u
.backanno
.end
""").lstrip()

    # Define file names
    netlist_file_name = "opamp_test.net"
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
    trace_name_capacitor_voltage = "V(vout)"

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
    plt.title("Output Voltage vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.grid(True)
    plt.show()

    print("\nBasic PyLTspice example finished.")

if __name__ == "__main__":
    main()
