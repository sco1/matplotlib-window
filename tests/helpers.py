import datetime as dt
import typing as t

import numpy as np
import pytest
from matplotlib.axes import Axes
from matplotlib.backend_bases import FigureCanvasBase, MouseButton, MouseEvent
from matplotlib.lines import Line2D

from matplotlib_window.base import get_native_data


def has_callback_to(
    parent_canvas: FigureCanvasBase, query_obj: str, event: str = "button_press_event"
) -> bool:
    """
    Check if any of the parent Canvas' callbacks for the provided `event` reference `query_obj`.

    This is a bit of a hack since it checks the weakref's `repr` output, but seems to work ok.
    """
    callbacks = parent_canvas.callbacks.callbacks.get(event, {})

    for ref in callbacks.values():
        if query_obj in repr(ref):
            return True

    return False


def fire_event(ax: Axes, name: str, xdata: float, ydata: float) -> None:
    """
    Dispatch a `MouseEvent` of the provided `name` to the axes' canvas.

    NOTE: `xdata` and `ydata` are expected in the axes' native float units.
    """
    if ax.figure is None:
        raise ValueError("Axes must belong to a figure.")

    canvas = ax.figure.canvas
    x, y = ax.transData.transform((xdata, ydata))
    event = MouseEvent(name, canvas, x, y, button=MouseButton.LEFT)
    canvas.callbacks.process(name, event)


def drag(ax: Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    """Simulate a click & drag from `start` to `end`, provided in the axes' native float units."""
    fire_event(ax, "button_press_event", *start)
    fire_event(ax, "motion_notify_event", *end)
    fire_event(ax, "button_release_event", *end)


EMPTY_LINE = Line2D(xdata=np.array([]), ydata=np.array([]))


ALL_NAN_LINE = Line2D(xdata=np.full(3, np.nan), ydata=np.full(3, np.nan))


# NaN gaps, including at the ends, are a common way to represent missing data
GAPPED_X = np.array([np.nan, 0, 1, np.nan, 3, 4, np.nan])
GAPPED_Y = np.array([np.nan, 10, 11, np.nan, 13, 14, np.nan])


# Make sure x & y data are different so we're not masking issues
DUMMY_LINE = Line2D(xdata=np.array([0, 1, 2]), ydata=np.array([10, 11, 12]))


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


def native_extents(line: Line2D, axis: t.Literal["x", "y"]) -> tuple[float, float, float]:
    """Return the min, max, & span of the line's data along `axis`, in native axes units."""
    native = get_native_data(line, axis)
    return native.min(), native.max(), (native.max() - native.min())
