# LTspice_automation

This repository contains a small example using the [PyLTSpice](https://pypi.org/project/PyLTSpice/) library to automate LTspice simulations.

## Prerequisites

- [LTspice](https://www.analog.com/en/design-center/design-tools-and-calculators/ltspice-simulator.html) must be installed and available on your system.
- Install the required Python packages using `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Running the example

The `pyltspicetest1.py` script creates a simple RC circuit netlist, runs LTspice,
and displays a matplotlib plot of the capacitor voltage over time. It also computes
an FFT of the capacitor voltage and shows the spectrum on a log-scale frequency axis
ranging from 1&nbsp;kHz to 200&nbsp;MHz. Execute it with Python:

```bash
python pyltspicetest1.py
```

### Using the GUI

Run the `gui_runtime.py` script to open a small window with controls for the
simulation. Spin boxes allow you to set the source frequency, resistor and
capacitor values and the stop time of the transient analysis. After selecting
the desired values, click **RUN** to launch LTspice and plot the result.

```bash
python gui_runtime.py
```

Upon completion, the script generates:

- `simple_rc.net` – the generated netlist file
- `temp_sim_output/` – directory containing the `.raw` and `.log` simulation output files

## Cleaning up

To remove the generated files after running the example, delete the netlist and output directory:

```bash
rm simple_rc.net
rm -r temp_sim_output
```
