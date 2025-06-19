import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backend_bases import MouseEvent
from matplotlib.widgets import RectangleSelector
import pytest

def test_ctrl_pan_then_zoom():
    fig, ax = plt.subplots()
    ax.plot(np.arange(10))
    fig.canvas.draw()

    orig_xlim = ax.get_xlim()
    orig_ylim = ax.get_ylim()

    # Zoom to enable panning
    ax.set_xlim(2, 6)
    ax.set_ylim(0, 6)
    fig.canvas.draw()

    ctrl_pressed = True
    pan_start = None
    pan_transform = None

    def pan_start_event(event):
        nonlocal pan_start, pan_transform
        if event.button != 1 or not ctrl_pressed:
            return
        if orig_xlim[0] is None:
            return
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        if (
            cur_xlim[0] == orig_xlim[0]
            and cur_xlim[1] == orig_xlim[1]
            and cur_ylim[0] == orig_ylim[0]
            and cur_ylim[1] == orig_ylim[1]
        ):
            return
        if event.x is None or event.y is None:
            return
        pan_start = (event.x, event.y, cur_xlim, cur_ylim)
        pan_transform = ax.transData.frozen()

    def pan_move_event(event):
        nonlocal pan_start, pan_transform
        if pan_start is None or event.x is None or event.y is None:
            return
        dx_pix = event.x - pan_start[0]
        dy_pix = event.y - pan_start[1]
        start_xlim, start_ylim = pan_start[2], pan_start[3]
        inv = pan_transform.inverted()
        start_pt = inv.transform((0, 0))
        cur_pt = inv.transform((dx_pix, dy_pix))
        dx = start_pt[0] - cur_pt[0]
        dy = start_pt[1] - cur_pt[1]
        ax.set_xlim(start_xlim[0] + dx, start_xlim[1] + dx)
        ax.set_ylim(start_ylim[0] + dy, start_ylim[1] + dy)

    def pan_end_event(event):
        nonlocal pan_start, pan_transform
        if event.button == 1 and pan_start is not None:
            pan_start = None
            pan_transform = None

    start_x, start_y = ax.transData.transform((3, 1))
    end_x, end_y = ax.transData.transform((4, 1))
    press = MouseEvent("button_press_event", fig.canvas, start_x, start_y, button=1)
    move = MouseEvent("motion_notify_event", fig.canvas, end_x, end_y, button=1)
    release = MouseEvent("button_release_event", fig.canvas, end_x, end_y, button=1)

    pan_start_event(press)
    pan_move_event(move)
    pan_end_event(release)

    pan_xlim = ax.get_xlim()
    pan_ylim = ax.get_ylim()

    assert pan_xlim != (2, 6)

    def onselect(eclick, erelease):
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata
        if None in (x1, y1, x2, y2):
            return
        ax.set_xlim(min(x1, x2), max(x1, x2))
        ax.set_ylim(min(y1, y2), max(y1, y2))

    RectangleSelector(ax, onselect, button=[1], useblit=True)

    eclick = type("E", (object,), {"xdata": pan_xlim[0] + 0.2, "ydata": pan_ylim[0] + 0.2})
    erelease = type("E", (object,), {"xdata": pan_xlim[0] + 1.2, "ydata": pan_ylim[0] + 1.2})
    onselect(eclick, erelease)

    zoom_xlim = ax.get_xlim()
    zoom_ylim = ax.get_ylim()

    assert zoom_xlim == pytest.approx((min(eclick.xdata, erelease.xdata), max(eclick.xdata, erelease.xdata)))
    assert zoom_ylim == pytest.approx((min(eclick.ydata, erelease.ydata), max(eclick.ydata, erelease.ydata)))
    plt.close(fig)
