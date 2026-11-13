import typing as t

import numpy as np
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from numpy import typing as npt

from matplotlib_window.draggable import COORD_T, NUMERIC_T, UNIT_T


def get_native_data(line: Line2D, axis: t.Literal["x", "y"]) -> npt.NDArray[np.float64]:
    """
    Return the line's data along the specified axis, converted to the axes' native float units.

    Plotted data may be of any type supported by matplotlib's unit conversion (e.g. datetimes or
    timedeltas), but mouse event coordinates & axes limits are always provided in native units.
    """
    if axis == "x":
        data = line.get_xdata(orig=False)
    else:
        data = line.get_ydata(orig=False)

    return np.asarray(data, dtype=float)


def to_native(ax: Axes, value: UNIT_T, axis: t.Literal["x", "y"]) -> float:
    """
    Convert the provided value to the axes' native float units along the specified axis.

    This mirrors the conversion performed by matplotlib when plotting data, so `value` may be of any
    type supported by matplotlib's unit conversion (e.g. datetimes or timedeltas). Numeric values
    are returned as floats.
    """
    ax_obj = ax.xaxis if axis == "x" else ax.yaxis
    converted = ax_obj.convert_units(value)  # type: ignore[no-untyped-call]

    # Types without a registered converter (e.g. timedelta64) are cast to float by matplotlib
    return float(np.asarray(converted, dtype=np.float64))


def to_native_span(ax: Axes, start: UNIT_T, span: UNIT_T, axis: t.Literal["x", "y"]) -> float:
    """
    Convert the provided span to the axes' native float units along the specified axis.

    Spans may not be independently convertible (e.g. a timedelta on a datetime axis), so the span is
    converted using its endpoints relative to `start`.
    """
    return to_native(ax, (start + span), axis) - to_native(ax, start, axis)


def limit_drag(plotted_data: npt.ArrayLike, query: float) -> float:
    """
    Clamp the query value within the bounds of the provided dataset.

    NOTE: `plotted_data` is assumed to be numeric & of the same units as `query`; see
    `get_native_data` for converting plotted data to match event coordinates.
    """
    # Data series may not be sorted, so use min/max; NaN-aware since plotted data may contain gaps
    data = np.asarray(plotted_data, dtype=float)
    return float(np.clip(query, np.nanmin(data), np.nanmax(data)))


class RectParams(t.NamedTuple):  # noqa: D101
    xy: COORD_T
    height: float


def transform_rect_params(ax: Axes, position: NUMERIC_T) -> RectParams:
    """
    Transform the desired x position to full span rectangle parameters.

    An xy coordinate pair is calculated that places the lower left corner of the rectangle at the
    lower y-axis limit, along with a height value that will cause the rectangle to span the entire
    y-axis bounds.
    """
    y_lbound, y_ubound = ax.get_ylim()
    xy = (position, y_lbound)
    height = y_ubound - y_lbound

    return RectParams(xy=xy, height=height)
