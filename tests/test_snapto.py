import datetime as dt
import typing as t

import numpy as np
import pytest
from matplotlib.lines import Line2D

from matplotlib_window.base import (
    DragLine,
    DragRect,
    Orientation,
    _DraggableObject,
    get_native_data,
)
from tests.conftest import PLOTOBJ_T
from tests.helpers import drag


def test_dragobj_snapto_none_passthrough() -> None:
    do = _DraggableObject()
    assert do.validate_snap_to(None) is None


def test_dragline_snapto_none_passthrough(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax=ax, position=0)
    assert dl.validate_snap_to(None) is None


def test_dragrect_snapto_none_passthrough(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0, width=1)
    assert dr.validate_snap_to(None) is None


EMPTY_LINE = Line2D(xdata=np.array([]), ydata=np.array([]))


def test_dragobj_snapto_empty_data_raises() -> None:
    do = _DraggableObject()
    with pytest.raises(ValueError, match="empty"):
        do.validate_snap_to(EMPTY_LINE)


def test_dragline_snapto_empty_data_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax=ax, position=0)
    with pytest.raises(ValueError, match="empty"):
        dl.validate_snap_to(EMPTY_LINE)


def test_dragrect_snapto_empty_data_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0, width=1)
    with pytest.raises(ValueError, match="empty"):
        dr.validate_snap_to(EMPTY_LINE)


# Make sure x & y data are different so we're not masking issues
DUMMY_LINE = Line2D(xdata=np.array([0, 1, 2]), ydata=np.array([10, 11, 12]))


def test_vertical_dragline_snapto_out_of_bounds_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax, position=3, orientation=Orientation.VERTICAL)

    with pytest.raises(ValueError, match="bounds"):
        dl.validate_snap_to(DUMMY_LINE)


def test_horizontal_dragline_snapto_out_of_bounds_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax, position=3, orientation=Orientation.HORIZONTAL)

    with pytest.raises(ValueError, match="bounds"):
        dl.validate_snap_to(DUMMY_LINE)


def test_vertical_dragline_valid_snapto(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    _ = DragLine(ax, position=1, orientation=Orientation.VERTICAL, snap_to=DUMMY_LINE)


def test_horizontal_dragline_valid_snapto(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    _ = DragLine(ax, position=11, orientation=Orientation.HORIZONTAL, snap_to=DUMMY_LINE)


def test_vertical_dragline_snapto_oob_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax, position=101, orientation=Orientation.VERTICAL)

    with pytest.raises(ValueError, match="bounds"):
        dl.validate_snap_to(DUMMY_LINE)


def test_horizontal_dragline_snapto_oob_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax, position=1, orientation=Orientation.HORIZONTAL)

    with pytest.raises(ValueError, match="bounds"):
        dl.validate_snap_to(DUMMY_LINE)


RECT_BOUNDS_TEST_CASES = (
    (-1, 1),  # Left edge out
    (0, 3),  # Right edge out
    (-1, 4),  # Both edges out
)


@pytest.mark.parametrize(("position", "width"), RECT_BOUNDS_TEST_CASES)
def test_dragrect_snapto_out_of_bounds_raises(
    position: int, width: int, plotobj: PLOTOBJ_T
) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=position, width=width)

    with pytest.raises(ValueError, match="bounds"):
        dr.validate_snap_to(DUMMY_LINE)


def test_dragrect_valid_snapto(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    _ = DragRect(ax=ax, position=0, width=1, snap_to=DUMMY_LINE)


# snap_to data should work for any type supported by matplotlib's unit conversion, so the tests
# below are run against a range of data types rather than special-casing each one
SNAP_TO_DATA: dict[str, t.Any] = {
    "numeric": np.arange(5),
    "datetime64[D]": np.arange("2026-01-01", "2026-01-06", dtype="datetime64[D]"),
    "datetime64[h]": np.arange("2026-01-01T00", "2026-01-01T05", dtype="datetime64[h]"),
    "datetime64[ns]": np.arange(5).astype("timedelta64[s]") + np.datetime64("2026-01-01", "ns"),
    "timedelta64[D]": np.arange(1, 6).astype("timedelta64[D]"),  # See: #8
    "timedelta64[s]": np.arange(1, 6).astype("timedelta64[s]"),
    "datetime": [dt.datetime(2026, 1, day) for day in range(1, 6)],
    "date": [dt.date(2026, 1, day) for day in range(1, 6)],
}
SNAP_TO_DATA_PARAMS = pytest.mark.parametrize(
    "data", SNAP_TO_DATA.values(), ids=SNAP_TO_DATA.keys()
)


def _native_extents(line: Line2D, axis: t.Literal["x", "y"]) -> tuple[float, float, float]:
    """Return the min, max, & span of the line's data along `axis`, in native axes units."""
    native = get_native_data(line, axis)
    return native.min(), native.max(), (native.max() - native.min())


@SNAP_TO_DATA_PARAMS
def test_vertical_dragline_snapto_data_types(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(data, range(5))[0]
    lo, hi, span = _native_extents(ls, "x")
    ax.set_xlim(lo - span, hi + span)  # Leave room to drag beyond the data inside the axes

    start = get_native_data(ls, "x")[1]
    dl = DragLine(ax, position=start, orientation=Orientation.VERTICAL, snap_to=ls)

    drag(ax, (start, 2), (hi + span / 2, 2))
    assert dl.location == pytest.approx(hi, abs=span * 1e-6)

    drag(ax, (hi, 2), (lo - span / 2, 2))
    assert dl.location == pytest.approx(lo, abs=span * 1e-6)


@SNAP_TO_DATA_PARAMS
def test_horizontal_dragline_snapto_data_types(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(range(5), data)[0]
    lo, hi, span = _native_extents(ls, "y")
    ax.set_ylim(lo - span, hi + span)  # Leave room to drag beyond the data inside the axes

    start = get_native_data(ls, "y")[1]
    dl = DragLine(ax, position=start, orientation=Orientation.HORIZONTAL, snap_to=ls)

    drag(ax, (2, start), (2, hi + span / 2))
    assert dl.location == pytest.approx(hi, abs=span * 1e-6)

    drag(ax, (2, hi), (2, lo - span / 2))
    assert dl.location == pytest.approx(lo, abs=span * 1e-6)


@SNAP_TO_DATA_PARAMS
def test_dragrect_snapto_data_types(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(data, range(5))[0]
    lo, hi, span = _native_extents(ls, "x")
    ax.set_xlim(lo - span, hi + span)  # Leave room to drag beyond the data inside the axes

    native = get_native_data(ls, "x")
    width = native[2] - native[1]
    dr = DragRect(ax, position=native[1], width=width, snap_to=ls)

    # Drag from the middle of the rectangle so the click lands on the patch; dragging by the full
    # data span pushes the leading edge beyond the data while keeping the cursor inside the axes
    mid = native[1] + width / 2
    drag(ax, (mid, 2), (mid + span, 2))
    assert dr.bounds == pytest.approx((hi - width, hi), abs=span * 1e-6)

    mid = hi - width / 2
    drag(ax, (mid, 2), (mid - span, 2))
    assert dr.bounds == pytest.approx((lo, lo + width), abs=span * 1e-6)


@SNAP_TO_DATA_PARAMS
def test_dragline_snapto_data_types_out_of_bounds_raises(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(data, range(5))[0]
    _, hi, span = _native_extents(ls, "x")

    with pytest.raises(ValueError, match="bounds"):
        _ = DragLine(ax, position=(hi + span), snap_to=ls)


@SNAP_TO_DATA_PARAMS
def test_dragrect_snapto_data_types_out_of_bounds_raises(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(data, range(5))[0]
    _, hi, span = _native_extents(ls, "x")

    with pytest.raises(ValueError, match="bounds"):
        _ = DragRect(ax, position=hi, width=span, snap_to=ls)
