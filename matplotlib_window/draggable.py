import typing as t
from collections import abc
from enum import StrEnum

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import Event, FigureCanvasBase, MouseEvent
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

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
