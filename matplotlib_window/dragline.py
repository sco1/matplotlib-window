import typing as t
from collections import abc

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import Event, MouseEvent
from matplotlib.lines import Line2D

from matplotlib_window.coordinates import get_native_data, limit_drag, to_native
from matplotlib_window.draggable import NUMERIC_T, Orientation, UNIT_T, _DraggableObject


class DragLine(_DraggableObject):
    """
    Draggable `Line2D` instance.

    `snap_to` may be optionally specified as an instance of another `Line2D` object to prevent
    dragging of the line beyond the extent of the plotted data.

    `redraw_callback` may be optionally specified as a callable which gets called whenever the
    location of the line has been changed. This callable is expected to take no arguments and has no
    return.

    All kwargs not explicitly named by `__init__` are passed through to the `Line2D` constructor,
    allowing the user to specify custom line formatting in a form expected by `Line2D`.

    `position` may be of any type supported by matplotlib's unit conversion (e.g. datetimes), but is
    converted to the axes' native float units on instantiation; `location` is always provided in
    native units.
    """

    myobj: Line2D

    def __init__(
        self,
        ax: Axes,
        position: UNIT_T,
        orientation: Orientation = Orientation.VERTICAL,
        snap_to: Line2D | None = None,
        redraw_callback: abc.Callable[[], None] | None = None,
        color: str = "limegreen",
        **kwargs: t.Any,
    ) -> None:
        self.orientation = orientation
        self.redraw_callback = redraw_callback

        # Work in native units internally so positions are directly comparable to event coordinates
        if orientation == Orientation.HORIZONTAL:
            position = to_native(ax, position, "y")
        else:
            position = to_native(ax, position, "x")

        line_pos = (position, position)  # matplotlib expectes a coordinate pair
        if orientation == Orientation.HORIZONTAL:
            obj = Line2D(xdata=ax.get_xlim(), ydata=line_pos, color=color, **kwargs)
        elif orientation == Orientation.VERTICAL:
            obj = Line2D(xdata=line_pos, ydata=ax.get_ylim(), color=color, **kwargs)
        else:
            raise ValueError(f"Unsupported orientation provided: '{orientation}'")

        self.register_plot_object(obj, ax)
        if orientation == Orientation.HORIZONTAL:
            self.axes_limit_change = ax.callbacks.connect("xlim_changed", self.limit_change)
        else:
            self.axes_limit_change = ax.callbacks.connect("ylim_changed", self.limit_change)

        self.snap_to = self.validate_snap_to(snap_to)

    def on_motion(self, event: Event) -> t.Any:
        """
        On motion callback.

        Update the position of the line to follow the position of the mouse at the time the event is
        fired. If `self.snap_to` is not `None`, motion of the line will be limited to the extent of
        the data plotted by the specified `Line2D`.
        """
        if not isinstance(event, MouseEvent):
            # Type narrowing, matplotlib dispatches a MouseEvent here so shouldn't ever trip this
            return
        if not self.clicked:
            return
        if event.inaxes != self.parent_axes:
            return
        if (event.xdata is None) or (event.ydata is None):
            return

        if self.orientation == Orientation.HORIZONTAL:
            if self.snap_to:
                new_pos = limit_drag(get_native_data(self.snap_to, "y"), event.ydata)
            else:
                new_pos = event.ydata

            self.myobj.set_ydata((new_pos, new_pos))
        elif self.orientation == Orientation.VERTICAL:
            if self.snap_to:
                new_pos = limit_drag(get_native_data(self.snap_to, "x"), event.xdata)
            else:
                new_pos = event.xdata

            self.myobj.set_xdata((new_pos, new_pos))

        self._redraw()

    def limit_change(self, ax: Axes) -> None:
        """
        Axes limit change callback.

        Resize the dragline to span the entirety of its relevant axis if the limit is changed.
        """
        if self.orientation == Orientation.HORIZONTAL:
            self.myobj.set_xdata(ax.get_xlim())
        else:
            self.myobj.set_ydata(ax.get_ylim())

        self._redraw()

    def validate_snap_to(self, snap_to: Line2D | None) -> Line2D | None:
        """
        Validate that the `snap_to` object, if provided, bounds the line being created.

        If `snap_to` is `None`, or is a plot object whose data along the line's axis of motion
        contains the line's location, it is returned unchanged. Otherwise an exception is raised.

        NOTE: This should be called after the draggable object is registered so the object is
        instantiated & references are set.
        """
        if snap_to is None:
            return None

        # Superclass implementation handles checking that the lineseries contains data
        super().validate_snap_to(snap_to)

        # Check that the draggable line is within the bounds of the snap_to lineseries along its
        # axis of motion
        if self.orientation == Orientation.HORIZONTAL:
            plotted_data = get_native_data(snap_to, "y")
        else:
            plotted_data = get_native_data(snap_to, "x")

        min_val, max_val = np.nanmin(plotted_data), np.nanmax(plotted_data)
        if not (min_val <= self.location <= max_val):
            raise ValueError("DragLine must be within the bounds of the provided snapto line")

        return snap_to

    @property
    def location(self) -> NUMERIC_T:
        """Return the location of the `DragLine` along its relevant axis."""
        pos: t.Sequence[NUMERIC_T]
        if self.orientation == Orientation.VERTICAL:
            pos = self.myobj.get_xdata()  # type: ignore[assignment]
        else:
            pos = self.myobj.get_ydata()  # type: ignore[assignment]

        return pos[0]  # Should be a (location, location) tuple

    def set_location(self, position: NUMERIC_T) -> None:
        """
        Set the location of the `DragLine` along its relevant axis, in native axes units.

        NOTE: The canvas is not redrawn & `redraw_callback` is not called; the caller is responsible
        for redrawing as needed.
        """
        if self.orientation == Orientation.VERTICAL:
            self.myobj.set_xdata((position, position))
        else:
            self.myobj.set_ydata((position, position))
