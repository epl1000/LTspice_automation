from pathlib import Path
from typing import Optional, Tuple

from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from PIL.Image import Image as PilImage

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
    schematic_image: Optional[PilImage] = None,
    append: bool = False,
    freq_plot_title: str = "FFT Magnitude",
    time_xlim: Optional[Tuple[float, float]] = None,
    time_ylim: Optional[Tuple[float, float]] = None,
    freq_xlim: Optional[Tuple[float, float]] = None,
    freq_ylim: Optional[Tuple[float, float]] = None,
) -> None:
    """Generate a simple PDF report of the simulation results.

    Parameters
    ----------
    output_file:
        Destination PDF file.
    time_data, voltage_data:
        Data for the time-domain plot.
    freq_data, mag_data:
        Data for the frequency-domain plot.  The *freq_plot_title*
        parameter controls the title shown on this page.
    measurements:
        Iterable of strings to display on a separate page or alongside the
        schematic.
    schematic_image:
        ``PIL.Image`` containing the circuit diagram to embed on the first
        page. When provided, measurement text is shown on top of this image.
    append:
        If ``True`` and *output_file* already exists, append new pages instead of
        overwriting the file.
    freq_plot_title:
        Title to use for the frequency-domain plot when ``freq_data`` and
        ``mag_data`` are provided.
    time_xlim, time_ylim:
        Optional axis limits for the time-domain plot.
    freq_xlim, freq_ylim:
        Optional axis limits for the frequency-domain plot.
    """

    figs = []

    if schematic_image is not None:
        fig, ax = plt.subplots()
        ax.imshow(schematic_image)
        ax.axis("off")
        if measurements:
            text = "\n".join(measurements)
            fig.text(
                0.02,
                0.98,
                text,
                ha="left",
                va="top",
                bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
            )
        figs.append(fig)
        measurements = None
    if time_data is not None and voltage_data is not None:
        fig, ax = plt.subplots()
        ax.plot(time_data, voltage_data)
        ax.set_title("Output Voltage vs Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Voltage (V)")
        ax.grid(True)
        if time_xlim is not None:
            ax.set_xlim(time_xlim)
        if time_ylim is not None:
            ax.set_ylim(time_ylim)
        figs.append(fig)

    if freq_data is not None and mag_data is not None:
        fig, ax = plt.subplots()
        ax.plot(freq_data, mag_data)
        ax.set_xscale("log")
        ax.set_title(freq_plot_title)
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Magnitude (dB)")
        ax.grid(True)
        if freq_xlim is not None:
            ax.set_xlim(freq_xlim)
        if freq_ylim is not None:
            ax.set_ylim(freq_ylim)
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
