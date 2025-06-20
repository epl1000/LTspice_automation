from __future__ import annotations
import numpy as np


def compute_vpp(
    x_data: np.ndarray, xlim: tuple[float, float], y_data: np.ndarray
) -> tuple[float, float, float, float, float]:
    """Return Vpp and max/min points within *xlim*."""

    start, end = xlim
    if start > end:
        start, end = end, start
    mask = (x_data >= start) & (x_data <= end)
    if not np.any(mask):
        raise ValueError("No points in range")

    x_sel = x_data[mask]
    y_sel = y_data[mask]

    idx_max = int(np.argmax(y_sel))
    idx_min = int(np.argmin(y_sel))

    v_max = float(y_sel[idx_max])
    v_min = float(y_sel[idx_min])
    t_max = float(x_sel[idx_max])
    t_min = float(x_sel[idx_min])

    return v_max - v_min, t_max, v_max, t_min, v_min
