import matplotlib.pyplot as plt
import numpy as np
import pytest

from matplotlib_window.base import NUMERIC_T, RectParams, limit_drag, transform_rect_params

PLOTTED_DATA = np.array([1, 2, 3, 4, 5])
LIMIT_DRAG_TEST_CASES = (
    (-1, 1),
    (-1.0, 1),
    (1, 1),
    (1.0, 1.0),
    (3, 3),
    (3.0, 3),
    (5, 5),
    (5.0, 5),
    (7, 5),
    (7.0, 5),
)


@pytest.mark.parametrize(("query", "truth_out"), LIMIT_DRAG_TEST_CASES)
def test_limit_drag(query: NUMERIC_T, truth_out: NUMERIC_T) -> None:
    assert limit_drag(plotted_data=PLOTTED_DATA, query=query) == pytest.approx(truth_out)


PLOTTED_TIMEDELTA = np.array([np.timedelta64(i) for i in range(1, 6)])
NP_TIMEDELTA_LIMIT_DRAG_TEST_CASES = (
    (-1, 1),
    (-1.0, 1),
    (1, 1),
    (1.0, 1.0),
    (3, 3),
    (3.0, 3),
    (5, 5),
    (5.0, 5),
    (7, 5),
    (7.0, 5),
)


@pytest.mark.parametrize(("query", "truth_out"), NP_TIMEDELTA_LIMIT_DRAG_TEST_CASES)
def test_limit_np_timedelta_drag(query: NUMERIC_T, truth_out: NUMERIC_T) -> None:
    assert limit_drag(plotted_data=PLOTTED_TIMEDELTA, query=query) == pytest.approx(truth_out)


def test_transform_rect() -> None:
    _, ax = plt.subplots()
    ax.set(xlim=(-10, 10), ylim=(-10, 10))
    truth_params = RectParams(xy=(0, -10), height=20)

    assert transform_rect_params(ax, 0) == truth_params
