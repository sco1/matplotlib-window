import typing as t
from collections import abc

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import Event, MouseEvent
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from matplotlib_window.coordinates import (
    get_native_data,
    limit_drag,
    to_native,
    to_native_span,
    transform_rect_params,
)
from matplotlib_window.draggable import NUMERIC_T, UNIT_T, _DraggableObject


class DragRect(_DraggableObject):
    """
    Draggable `Rectangle` instance.

    `position` specifies the x-coordinate of the left edge of the rectangle.

    `snap_to` may be optionally specified as an instance of a `Line2D` object to prevent dragging of
    the rectangle beyond the extent of the plotted data.

    `redraw_callback` may be optionally specified as a callable which gets called whenever the
    location of the line has been changed. This callable is expected to take no arguments and has no
    return.

    All kwargs not explicitly named by `__init__` are passed through to the `Rectangle` constructor,
    allowing the user to specify custom line formatting in a form expected by `Rectangle`.

    `position` and `width` may be of any type supported by matplotlib's unit conversion (e.g. a
    datetime & timedelta), but are converted to the axes' native float units on instantiation;
    `bounds` is always provided in native units.

    NOTE: Motion is constrained to the x-axis only.
    """

    myobj: Rectangle

    # Left edge location when the current drag started, used for drag deltas so the object doesn't
    # jump to the cursor
    drag_start_x: float

    def __init__(
        self,
        ax: Axes,
        position: UNIT_T,
        width: UNIT_T,
        snap_to: Line2D | None = None,
        redraw_callback: abc.Callable[[], None] | None = None,
        edgecolor: str | None = "limegreen",
        facecolor: str = "limegreen",
        alpha: NUMERIC_T = 0.4,
        **kwargs: t.Any,
    ) -> None:
        # Work in native units internally so positions are directly comparable to event coordinates
        native_width = to_native_span(ax, position, width, "x")
        if native_width <= 0:
            raise ValueError(f"Width value must be greater than 0. Received: {width}")

        position = to_native(ax, position, "x")
        width = native_width

        self.redraw_callback = redraw_callback

        # Rectangle patches are located from their bottom left corner; because we want to span the
        # full y range, we need to translate the y position to the bottom of the axes
        rect_params = transform_rect_params(ax, position)

        obj = Rectangle(
            xy=rect_params.xy,
            width=width,
            height=rect_params.height,
            edgecolor=edgecolor,
            facecolor=facecolor,
            alpha=alpha,
            **kwargs,
        )

        self.register_plot_object(obj, ax)
        self.axes_limit_change = ax.callbacks.connect("ylim_changed", self.limit_change)

        self.snap_to = self.validate_snap_to(snap_to)

    def on_click(self, event: Event) -> t.Any:
        """
        Mouse click callback.

        In addition to the common click handling, cache the location of the left edge if a drag is
        started. This is cached at the start of every drag, rather than at the end of the previous
        one, so it remains correct if the rectangle is moved by other means between drags (e.g. by
        a `FlexibleRect`'s edges).
        """
        super().on_click(event)

        if self.clicked:
            self.drag_start_x = self.myobj.get_x()

    def on_motion(self, event: Event) -> t.Any:
        """
        On motion callback.

        Update the position of the rectangle to follow the position of the mouse at the time the
        event is fired. If `self.snap_to` is not `None`, motion of the rectangle will be limited to
        the extent of the data plotted by the specified `Line2D`.
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

        # Calculate the new xy position based on the movement of the cursor relative to the location
        # of the bottom left corner when the object was clicked on. Because we can click anywhere on
        # the patch to begin motion, the patch will jump to the mouse if just using the location of
        # the MouseEvent.
        old_x = self.drag_start_x
        dx = event.xdata - self.click_x
        if self.snap_to:
            if dx < 0:
                # Moving left, check left edge
                query = old_x + dx
                new_x = limit_drag(get_native_data(self.snap_to, "x"), query)
            else:
                # Moving right, check right edge
                width = self.myobj.get_width()
                query = old_x + width + dx
                new_x = limit_drag(get_native_data(self.snap_to, "x"), query) - width
        else:
            new_x = old_x + dx

        rect_params = transform_rect_params(self.parent_axes, new_x)
        self.myobj.xy = rect_params.xy

        self._redraw()

    def limit_change(self, ax: Axes) -> None:
        """
        Axes limit change callback.

        Resize the rectangle to span the entirety of the y-axis if the axis limit is changed.
        """
        rect_params = transform_rect_params(ax, self.myobj.get_x())
        self.myobj.set_xy(rect_params.xy)
        self.myobj.set_height(rect_params.height)
        self._redraw()

    def validate_snap_to(self, snap_to: Line2D | None) -> Line2D | None:
        """
        Validate that the `snap_to` object, if provided, actually contains x data.

        If `snap_to` is `None`, or is a plot object that contains x data, it is returned unchanged.
        Otherwise an exception is raised.

        NOTE: This should be called after the draggable object is registered so the object is
        instantiated & references are set.
        """
        if snap_to is None:
            return None

        # Superclass implementation handles checking that the lineseries contains data
        super().validate_snap_to(snap_to)

        # Check that the draggable rectangle is within the bounds of the snap_to lineseries
        l_pos, r_pos = self.bounds
        plotted_data = get_native_data(snap_to, "x")
        min_val, max_val = np.nanmin(plotted_data), np.nanmax(plotted_data)
        if not (min_val <= l_pos <= max_val) or not (min_val <= r_pos <= max_val):
            raise ValueError("DragRect must be within the bounds of the provided snapto line")

        return snap_to

    @property
    def bounds(self) -> tuple[NUMERIC_T, NUMERIC_T]:
        """Return the x-axis locations of the left & right edges."""
        l_pos = self.myobj.get_x()
        return l_pos, (l_pos + self.myobj.get_width())
