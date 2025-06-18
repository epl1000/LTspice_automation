from pathlib import Path
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

try:  # Use PyPDF2 when available, fall back to pypdf
    from PyPDF2 import PdfReader, PdfWriter
except ModuleNotFoundError:  # pragma: no cover - environment may vary
    try:
        from pypdf import PdfReader, PdfWriter
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "PyPDF2 or pypdf is required for PDF report generation"
        ) from exc


def generate_pdf_report(
    output_file: str,
    time_data=None,
    voltage_data=None,
    freq_data=None,
    mag_data=None,
    measurements=None,
    append: bool = False,
) -> None:
    """Generate a simple PDF report of the simulation results."""

    figs = []
    if time_data is not None and voltage_data is not None:
        fig, ax = plt.subplots()
        ax.plot(time_data, voltage_data)
        ax.set_title("Output Voltage vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Voltage (V)")
        ax.grid(True)
        figs.append(fig)

    if freq_data is not None and mag_data is not None:
        fig, ax = plt.subplots()
        ax.plot(freq_data, mag_data)
        ax.set_xscale("log")
        ax.set_title("AC / FFT Magnitude")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Magnitude (dB)")
        ax.grid(True)
        figs.append(fig)

    if measurements:
        fig, ax = plt.subplots(figsize=(6, 2))
        ax.axis("off")
        text = "\n".join(measurements)
        ax.text(0.01, 0.95, text, va="top")
        figs.append(fig)

    temp_pdf = Path(output_file).with_suffix(".tmp.pdf")
    with PdfPages(temp_pdf) as pdf:
        for fig in figs:
            pdf.savefig(fig)
        plt.close('all')

    if append and Path(output_file).exists():
        writer = PdfWriter()
        for page in PdfReader(output_file).pages:
            writer.add_page(page)
        for page in PdfReader(temp_pdf).pages:
            writer.add_page(page)
        with open(output_file, "wb") as f:
            writer.write(f)
        temp_pdf.unlink()
    else:
        temp_pdf.replace(output_file)
