import typing as t
from collections import abc
from enum import StrEnum
from functools import partial

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import Event, FigureCanvasBase, MouseEvent
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from numpy import typing as npt

COORD_T: t.TypeAlias = tuple[float, float]
CALLBACK_T: t.TypeAlias = abc.Callable[[Event], t.Any]
PLOT_OBJ_T: t.TypeAlias = Line2D | Rectangle
NUMERIC_T: t.TypeAlias = float | int
# Any value supported by matplotlib's unit conversion (e.g. numeric, datetime, timedelta)
UNIT_T: t.TypeAlias = t.Any

COMMON_OBJ_ID = "dragobj"  # Label created object(s) URL for downstream event filtering


class Orientation(StrEnum):  # noqa: D101
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"


class _DraggableObject:
    """
    Common draggable plot object base class.

    This should not be instantiated directly, child classes are responsible for setting the
    necessary class variables for proper functionality prior to calling `register_plot_object`,
    which attaches common callbacks to the figure.

    Child classes must define:
        * `on_motion` callable
        * `snap_to` plot object, if desired

    Common callbacks registered by this base class are:
        * `on_click`
        * `on_release`
    """

    clicked: bool
    click_x: float
    click_y: float

    # Defined by child classes prior to registration
    on_motion: CALLBACK_T
    snap_to: Line2D | None
    redraw_callback: abc.Callable[[], None] | None

    # Defined on registration
    myobj: PLOT_OBJ_T
    parent_axes: Axes
    parent_canvas: FigureCanvasBase
    # The canvas retains only weak references so retain just in case
    click_press: int
    mouse_motion: int
    click_release: int

    def register_plot_object(self, plot_object: PLOT_OBJ_T, ax: Axes) -> None:
        """
        Attach the provided draggable plot object to the figure & connect callbacks.

        This must be called by any child class, which is responsible for instantiating the relevant
        plot object, and, if desired, setting the desired `snap_to` plot object.

        All draggable objects have their `url` set to a common string, defined by the module-level
        `COMMON_OBJ_ID`, to aid with downstream filtering.
        """
        self.parent_axes = ax

        if ax.figure is not None:
            self.parent_canvas = ax.figure.canvas
        else:
            raise ValueError("I don't know how we got here, but there's no figure.")

        self.myobj = plot_object
        self.myobj.set_url(COMMON_OBJ_ID)
        ax.add_artist(self.myobj)

        self.click_press = self.parent_canvas.mpl_connect("button_press_event", self.on_click)
        self.clicked = False

    def should_move(self, event: MouseEvent) -> bool:
        """
        Determine whether this instance is the topmost object that fired the event.

        If multiple draggable objects overlap, it is possible that more than one object will fire
        events. This method can be used to limit movement to the topmost rendered object that fired
        the event.

        Draggable objects are assumed to be tagged with a common `url` string, and the topmost
        rendered object is assumed to be closest matching object to the end when iterating through
        the parent axes' children.
        """
        contains, _ = self.myobj.contains(event)
        if not contains:
            return False

        firing_objs = []
        for c in self.parent_axes.get_children():
            if c.get_url() == COMMON_OBJ_ID:
                contains, _ = c.contains(event)
                if contains:
                    firing_objs.append(c)

        if firing_objs[-1] is self.myobj:
            return True
        else:
            return False

    def on_click(self, event: Event) -> t.Any:
        """
        Mouse click callback.

        When clicking on a draggable object, connect the relevant callbacks:
            * `"motion_notify_event"` -> `self.on_motion` (defined by child class)
            * `"button_release_event"` -> `self.on_release`
        """
        if not isinstance(event, MouseEvent):
            # Type narrowing, matplotlib dispatches a MouseEvent here so shouldn't ever trip this
            return

        if event.inaxes != self.parent_axes:
            return

        # Return early if we aren't able to obtain a widgetlock
        # Obtaining a lock allows us to prevent dragging when zoom/pan is active
        if not self.parent_canvas.widgetlock.available(self):
            return

        if not self.should_move(event):
            return

        if (event.xdata is None) or (event.ydata is None):
            return

        self.click_x, self.click_y = (event.xdata, event.ydata)
        self.clicked = True

        self.mouse_motion = self.parent_canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.click_release = self.parent_canvas.mpl_connect("button_release_event", self.on_release)

        # Obtaining a lock allows us to prevent dragging when zoom/pan is active
        self.parent_canvas.widgetlock(self)

    def on_release(self, event: Event) -> t.Any:
        """
        Mouse button release callback.

        When the mouse button is released, disconnect the callbacks connected by `self.on_click`.
        """
        if not isinstance(event, MouseEvent):
            # Type narrowing, matplotlib dispatches a MouseEvent here so shouldn't ever trip this
            return

        self.disconnect()

    def disconnect(self) -> None:
        """Disconnect the callbacks connected by `self.on_click`."""
        self.clicked = False
        self.parent_canvas.mpl_disconnect(self.mouse_motion)
        self.parent_canvas.mpl_disconnect(self.click_release)

        # Release any widgetlock when drag is finished
        self.parent_canvas.widgetlock.release(self)

        self._redraw()

    def validate_snap_to(self, snap_to: Line2D | None) -> Line2D | None:
        """
        Validate that the `snap_to` object, if provided, actually contains lineseries xy data.

        If `snap_to` is `None`, or is a plot object that contains at least one finite xy data point,
        it is returned unchanged. Otherwise an exception is raised.
        """
        if snap_to is None:
            return None

        try:
            xydata = np.asarray(snap_to.get_xydata())
        except AttributeError as e:
            raise ValueError("Cannot provide an empty lineseries to snapto") from e

        if len(xydata) == 0:
            raise ValueError("Cannot provide an empty lineseries to snapto")

        # NaN gaps are fine, but there needs to be at least one plotted point to snap to
        if not np.isfinite(xydata).all(axis=1).any():
            raise ValueError("Cannot provide a lineseries without any finite data to snapto")

        return snap_to

    def _disable_click(self) -> None:
        """Disconnect the button press event for the current instance."""
        self.parent_canvas.mpl_disconnect(self.click_press)
        self.click_press = -1

    def _redraw(self) -> None:
        if self.redraw_callback is not None:
            self.redraw_callback()

        self.parent_canvas.draw()


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
        self.myobj: Line2D
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
        self.myobj: Rectangle
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


class FlexibleRect:
    """
    A flexible-width rectangle.

    `position` specifies the x-coordinate of the left edge of the rectangle.

    `snap_to` may be optionally specified as an instance of a `Line2D` object to prevent dragging of
    the rectangle beyond the extent of the plotted data.

    `redraw_callback` may be optionally specified as a callable which gets called whenever the
    location of the line has been changed. This callable is expected to take no arguments and has no
    return.

    `position` and `width` may be of any type supported by matplotlib's unit conversion (e.g. a
    datetime & timedelta), but are converted to the axes' native float units on instantiation;
    `bounds` is always provided in native units.

    If `allow_face_drag` is `True`, the entire rectangle may also be dragged using its face.

    NOTE: Motion is constrained to the x-axis only.
    """

    def __init__(
        self,
        ax: Axes,
        position: UNIT_T,
        width: UNIT_T,
        snap_to: Line2D | None = None,
        redraw_callback: abc.Callable[[], None] | None = None,
        allow_face_drag: bool = False,
        edgecolor: str = "limegreen",
        facecolor: str = "limegreen",
        alpha: NUMERIC_T = 0.4,
    ) -> None:
        # Work in native units internally so the edge positions can be calculated directly
        native_width = to_native_span(ax, position, width, "x")
        if native_width <= 0:
            raise ValueError(f"Width value must be greater than 0. Received: {width}")

        position = to_native(ax, position, "x")
        width = native_width

        self.parent_axes = ax
        if ax.figure is not None:
            self.parent_canvas = ax.figure.canvas
        else:
            raise ValueError("I don't know how we got here, but there's no figure.")

        self.redraw_callback = redraw_callback

        # snap_to validation handled by DragRect & DragLine
        # Create edges after face so they're topmost & take click priority
        # If the face is draggable, it snaps as a whole & drags the edges along with it
        self.face = DragRect(
            ax=ax,
            position=position,
            width=width,
            snap_to=(snap_to if allow_face_drag else None),
            redraw_callback=(self._move_edges if allow_face_drag else None),
            facecolor=facecolor,
            edgecolor=None,
            alpha=alpha,
        )

        line_p = partial(
            DragLine,
            ax=ax,
            color=edgecolor,
            snap_to=snap_to,
            redraw_callback=self._respan_face,
        )
        self.edges = [line_p(position=position), line_p(position=(position + width))]

        if not allow_face_drag:
            self.face._disable_click()

    def _move_edges(self) -> None:
        """Move the edges to the bounds of the face, called when the face has been dragged."""
        left, right = self.face.bounds

        # Edges may have been dragged past each other, so match them to the face by location
        left_edge, right_edge = sorted(self.edges, key=lambda edge: edge.location)
        left_edge.set_location(left)
        right_edge.set_location(right)

        if self.redraw_callback is not None:
            self.redraw_callback()

    def _respan_face(self) -> None:
        """Update face dimensions to span the entirety of the y-axes between the two edges."""
        left = min(edge.location for edge in self.edges)
        right = max(edge.location for edge in self.edges)

        rect_params = transform_rect_params(self.parent_axes, left)
        width = right - left

        self.face.myobj.set_xy(rect_params.xy)
        self.face.myobj.set_width(width)

        if self.redraw_callback is not None:
            self.redraw_callback()

        self.parent_canvas.draw()  # Call directly to avoid infinitely spamming the callback

    @property
    def bounds(self) -> tuple[NUMERIC_T, NUMERIC_T]:
        """Return the x-axis locations of the left & right edges."""
        return tuple(sorted(edge.location for edge in self.edges))  # type: ignore[return-value]
