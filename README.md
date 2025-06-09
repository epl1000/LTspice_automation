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

## Running the example

The `pyltspicetest1.py` script creates a small op-amp test netlist using the
LM7171 model, runs LTspice, and displays a matplotlib plot of the output
voltage over time. Execute it with Python:

```bash
python pyltspicetest1.py [path/to/LM7171.lib]
```
If the path to the model is omitted, the script looks for ``LM7171.lib`` in the
current working directory.

### Using the GUI

Run the `gui_runtime.py` script to open a small window with a **RUN** button.
Press **RUN** and you will be prompted to select the `LM7171.lib` model file
used in the example. After selecting the file, LTspice will run and the
simulation result will be plotted.

```bash
python gui_runtime.py
```

Upon completion, the script generates:

- `opamp_test.net` – the generated netlist file
- `temp_sim_output/` – directory containing the `.raw` and `.log` simulation output files

## Cleaning up

To remove the generated files after running the example, delete the netlist and output directory:

```bash
rm opamp_test.net
rm -r temp_sim_output
```
