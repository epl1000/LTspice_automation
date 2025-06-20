import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from measurements import compute_vpp


def test_compute_vpp_full_range():
    t = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    v = np.array([0.0, 1.0, 0.0, -1.0, 0.5])
    vpp, t_max, v_max, t_min, v_min = compute_vpp(t, (0.0, 4.0), v)
    assert vpp == pytest.approx(2.0)
    assert t_max == pytest.approx(1.0)
    assert v_max == pytest.approx(1.0)
    assert t_min == pytest.approx(3.0)
    assert v_min == pytest.approx(-1.0)


def test_compute_vpp_zoom_range():
    t = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    v = np.array([0.0, 1.0, 0.0, -1.0, 0.5])
    vpp, t_max, v_max, t_min, v_min = compute_vpp(t, (0.5, 2.5), v)
    assert vpp == pytest.approx(1.0)
    assert t_max == pytest.approx(1.0)
    assert v_max == pytest.approx(1.0)
    assert t_min == pytest.approx(2.0)
    assert v_min == pytest.approx(0.0)
