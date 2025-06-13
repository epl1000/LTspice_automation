# LTspice_automation

This repository contains a small example using the [PyLTSpice](https://pypi.org/project/PyLTSpice/) library to automate LTspice simulations.

## Prerequisites

- [LTspice](https://www.analog.com/en/design-center/design-tools-and-calculators/ltspice-simulator.html) must be installed and available on your system.
  Ensure the LTspice executable is accessible from the command line. If it is
  installed in a non-standard location you can specify the path explicitly with
  `SimRunner.create_from("/path/to/LTspice")`.
- Install the Python package `PyLTSpice`:

```bash
pip install PyLTSpice
```
- Install the Python package `matplotlib` for plotting:

```bash
pip install matplotlib
```
- The optional package `schemdraw` is required to generate a simple circuit
  diagram from the netlist:

```bash
pip install schemdraw
```

## Running the example

The `pyltspicetest1.py` script creates a small op-amp test netlist. By default
it expects the `LM7171.lib` file in the current directory, but you can pass the
path to any compatible op-amp model file. The script reads the first `.SUBCKT`
definition from the library and instantiates that subcircuit in the netlist.
Run it with Python:

```bash
python pyltspicetest1.py [path/to/opamp.lib]
```
If the model path is omitted, `LM7171.lib` is used.

### Using the GUI

Run the `gui_runtime.py` script to open a small window with a **RUN** button
and a **Load Model** button. Eight spin boxes allow you to set the values of the
gain resistor (`R9`), input resistor (`R1`), load resistor (`R3`), feedback
capacitor (`C1`), input capacitor (`C2`), load capacitor (`C3`), and the
amplitude and frequency of the input source `V1`. The capacitor spin boxes
increment in 1&nbsp;pF steps. The `C2` and `C3` controls appear to the right of
the `C1` and `R3` pair, stacked vertically. The new `V1` controls are positioned
to their right, leaving the **RUN** and **Load Model** buttons on the far right.

Click **Load Model** to select the op-amp model file. The selected file is
remembered across runs and its name is displayed to the right of the **RUN**
button. Press **RUN** to run the simulation using the currently loaded model.
The netlist is updated with the spinner values and the simulation result is
plotted. After each run a simple schematic derived from the netlist is shown to
the right of the plot.

```bash
python gui_runtime.py
```

Upon completion, the script generates:

- `opamp_test.net` – the generated netlist file
- `temp_sim_output/` – directory containing the `.raw` and `.log` simulation output files
- `opamp_test.svg` – simple schematic created from the netlist

## Cleaning up

To remove the generated files after running the example, delete the netlist and output directory:

```bash
rm opamp_test.net
rm -r temp_sim_output
```
