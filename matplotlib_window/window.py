import typing as t
from collections import abc

import matplotlib.pyplot as plt

from matplotlib_window.base import DragRect, FlexibleRect, NUMERIC_T

DEFAULT_AXES_KWARGS: dict[str, t.Any] = {
    "title": "Close window to return selected window bounds",
}

DEFAULT_PLOT_KWARGS: dict[str, t.Any] = {}


def fixed_window(
    x_data: abc.Sequence[NUMERIC_T],
    y_data: abc.Sequence[NUMERIC_T],
    position: NUMERIC_T,
    window_width: NUMERIC_T,
    snap_to_data: bool = True,
    axes_kwargs: dict[str, t.Any] = DEFAULT_AXES_KWARGS,
    plot_kwargs: dict[str, t.Any] = DEFAULT_PLOT_KWARGS,
) -> tuple[NUMERIC_T, NUMERIC_T]:
    """
    Plot the provided data & build a draggable fixed-width window to select bounds of interest.

    The x-locations of the edges of the window are returned once the figure window is closed.

    `position` specifies the x-coordinate of the left edge of the window.

    If `snap_to_data` is `True`, the window is prevented from being dragged beyond the bounds of the
    plotted data.

    `axes_kwargs` and `plot_kwargs` may be optionally specified to control the appearance of the
    resulting `Axes` and `Line2D` objects, respectively, and are passed straight through to their
    respective objects. Consult their respective documentation for available parameters.
    """
    _, ax = plt.subplots()
    ax.set(**axes_kwargs)
    ls = ax.plot(x_data, y_data, **plot_kwargs)

    if snap_to_data:
        snap_to = ls[0]
    else:
        snap_to = None

    dr = DragRect(ax=ax, position=position, width=window_width, snap_to=snap_to)
    plt.show()

    return dr.bounds


def flexible_window(
    x_data: abc.Sequence[NUMERIC_T],
    y_data: abc.Sequence[NUMERIC_T],
    position: NUMERIC_T,
    window_width: NUMERIC_T,
    snap_to_data: bool = True,
    allow_face_drag: bool = False,
    axes_kwargs: dict[str, t.Any] = DEFAULT_AXES_KWARGS,
    plot_kwargs: dict[str, t.Any] = DEFAULT_PLOT_KWARGS,
) -> tuple[NUMERIC_T, NUMERIC_T]:
    """
    Plot the provided data & build a flexible-width window to select bounds of interest.

    The x-locations of the edges of the window are returned once the figure window is closed.

    `position` specifies the x-coordinate of the left edge of the window.

    If `snap_to_data` is `True`, the window is prevented from being dragged beyond the bounds of the
    plotted data.

    If `allow_face_drag` is `True`, the entire window may be dragged using its face. NOTE: This is
    currently not implemented.

    `axes_kwargs` and `plot_kwargs` may be optionally specified to control the appearance of the
    resulting `Axes` and `Line2D` objects, respectively, and are passed straight through to their
    respective objects. Consult their respective documentation for available parameters.
    """
    _, ax = plt.subplots()
    ax.set(**axes_kwargs)
    ls = ax.plot(x_data, y_data, **plot_kwargs)

    if snap_to_data:
        snap_to = ls[0]
    else:
        snap_to = None

    dr = FlexibleRect(
        ax=ax,
        position=position,
        width=window_width,
        snap_to=snap_to,
        allow_face_drag=allow_face_drag,
    )
    plt.show()

    return dr.bounds
