import matplotlib.dates as mdates
import numpy as np
import pytest

from matplotlib_window.base import (
    NUMERIC_T,
    RectParams,
    get_native_data,
    limit_drag,
    to_native,
    to_native_span,
    transform_rect_params,
)
from tests.conftest import PLOTOBJ_T

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


def test_limit_drag_unsorted_data() -> None:
    assert limit_drag(plotted_data=np.array([3, 5, 1, 4, 2]), query=7) == pytest.approx(5)


GAPPED_DATA = np.array([np.nan, 1, 2, np.nan, 4, 5, np.nan])


@pytest.mark.parametrize(("query", "truth_out"), LIMIT_DRAG_TEST_CASES)
def test_limit_drag_nan_gaps(query: NUMERIC_T, truth_out: NUMERIC_T) -> None:
    assert limit_drag(plotted_data=GAPPED_DATA, query=query) == pytest.approx(truth_out)


def test_get_native_data_numeric(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot([1, 2, 3], [4, 5, 6])[0]

    np.testing.assert_allclose(get_native_data(ls, "x"), [1, 2, 3])
    np.testing.assert_allclose(get_native_data(ls, "y"), [4, 5, 6])


def test_get_native_data_datetime(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dates = np.arange("2026-01-01", "2026-01-04", dtype="datetime64[D]")
    ls = ax.plot(dates, dates)[0]

    truth_data = mdates.date2num(dates)  # type: ignore[no-untyped-call]
    np.testing.assert_allclose(get_native_data(ls, "x"), truth_data)
    np.testing.assert_allclose(get_native_data(ls, "y"), truth_data)


def test_to_native_numeric(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    native = to_native(ax, 2, "x")

    assert isinstance(native, float)
    assert native == pytest.approx(2)
    assert to_native_span(ax, 2, 3, "x") == pytest.approx(3)


def test_to_native_datetime(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    start = np.datetime64("2026-01-02T00", "h")
    span = np.timedelta64(6, "h")

    truth_start = mdates.date2num(start)  # type: ignore[no-untyped-call]
    assert to_native(ax, start, "y") == pytest.approx(truth_start)
    assert to_native_span(ax, start, span, "y") == pytest.approx(0.25)  # Fraction of a day


def test_transform_rect(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ax.set(xlim=(-10, 10), ylim=(-10, 10))
    truth_params = RectParams(xy=(0, -10), height=20)

    assert transform_rect_params(ax, 0) == truth_params
