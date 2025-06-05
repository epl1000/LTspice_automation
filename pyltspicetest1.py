from PyLTSpice import SpiceEditor, SimRunner, RawRead
import os

# --- 1. Define the Netlist Content ---
netlist_content = """* Simple RC Circuit
V1 N001 0 SINE(0 1 1k) ; Voltage source: 1V amplitude, 1kHz
R1 N001 N002 1k         ; Resistor: 1k Ohm
C1 N002 0 1uF           ; Capacitor: 1uF
.tran 0 5m 0 1u         ; Transient analysis: 0 to 5ms, 1us step
.end
"""

# Define file names
netlist_file_name = "simple_rc.net"
output_folder = "temp_sim_output"   # PyLTspice will create this if it doesn't exist

# --- 2. Manually create and write the netlist file first ---
print(f"Creating and writing netlist content to file: {netlist_file_name}")
try:
    with open(netlist_file_name, 'w', encoding='utf-8') as f:
        f.write(netlist_content)
    print(f"Netlist file '{netlist_file_name}' created and written successfully.")
except IOError as e:
    print(f"FATAL ERROR: Could not write netlist file {netlist_file_name}: {e}")
    exit()

# --- 3. Initialize SpiceEditor with the NOW EXISTING file ---
print(f"Initializing SpiceEditor with existing file: {netlist_file_name}")
try:
    # Now that the file exists and has content, SpiceEditor should be able to open and parse it.
    netlist_editor_obj = SpiceEditor(netlist_file_name)
    print("SpiceEditor initialized successfully.")
    # There's no need to call .set_text() or .save() here if the file
    # already contains the complete and correct netlist and we don't
    # intend to modify it further with SpiceEditor methods at this stage.
except Exception as e:
    print(f"FATAL ERROR: Could not initialize SpiceEditor with file {netlist_file_name}: {e}")
    exit()

# --- 4. Run the LTSpice Simulation (modern API) ---
print(f"\nRunning simulation for {netlist_file_name}...")

runner = SimRunner(output_folder=output_folder)   # ←---------- this was missing

try:
    # run_now blocks until LTspice finishes and
    # returns (raw_path, log_path) as pathlib.Path objects
    raw_file_path, log_file_path = runner.run_now(netlist_editor_obj)
    print("LTSpice simulation completed successfully.")
except Exception as e:
    print(f"Error: LTSpice simulation failed – {e}")
    exit()

print(f"Simulation output (raw file): {raw_file_path}")

# --- 5. Read the Simulation Output File ---
print("\nReading simulation output...")
try:
    raw_data = RawRead(raw_file_path)
except Exception as e:
    print(f"Error reading raw file {raw_file_path}: {e}")
    exit()
print("Raw file read successfully.")


# --- 6. Get a Specific Trace ---
trace_name_capacitor_voltage = "V(N002)"

if trace_name_capacitor_voltage in raw_data.get_trace_names():
    print(f"\nGetting trace: {trace_name_capacitor_voltage}")
    v_cap = raw_data.get_trace(trace_name_capacitor_voltage)
    time_trace = raw_data.get_trace("time")

    print(f"\nData for {trace_name_capacitor_voltage}:")
    print("Time (s)       | Voltage (V)")
    print("----------------|---------------")
    for i in range(min(10, len(time_trace.get_wave()))):
        print(f"{time_trace.get_wave()[i]:<15.6e} | {v_cap.get_wave()[i]:<15.6e}")
else:
    print(f"\nError: Trace '{trace_name_capacitor_voltage}' not found in the raw file.")
    print("Available traces:", raw_data.get_trace_names())

print("\nBasic PyLTspice example finished.")