import typing as t
from enum import StrEnum

from matplotlib.axes import Axes
from matplotlib.backend_bases import Event, FigureCanvasBase, MouseEvent
from matplotlib.lines import Line2D
from numpy import typing as npt

COORD_T: t.TypeAlias = tuple[float, float]
CALLBACK_T: t.TypeAlias = t.Callable[[Event], t.Any]
PLOT_OBJ_T: t.TypeAlias = Line2D
NUMERIC_T: t.TypeAlias = float | int

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
    snap_to: PLOT_OBJ_T | None

    # Defined on registration
    myobj: Line2D
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

        if not self.should_move(event):
            return

        if (event.xdata is None) or (event.ydata is None):
            return

        self.click_x, self.click_y = (event.xdata, event.ydata)
        self.clicked = True

        self.mouse_motion = self.parent_canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.click_release = self.parent_canvas.mpl_connect("button_release_event", self.on_release)

    def on_release(self, event: Event) -> t.Any:
        """
        Mouse button release callback.

        When the mouse button is released, disconnect the callbacks connected by `self.on_click`.
        """
        if not isinstance(event, MouseEvent):
            # Type narrowing, matplotlib dispatches a MouseEvent here so shouldn't ever trip this
            return

        self.clicked = False
        self.parent_canvas.mpl_disconnect(self.mouse_motion)
        self.parent_canvas.mpl_disconnect(self.click_release)
        self.parent_canvas.draw()


class DragLine(_DraggableObject):
    """
    Draggable `Line2D` instance.

    `snap_to` may be optionally specified as an instance of another `Line2D` object to prevent
    dragging of the line beyond the extent of the plotted data.

    All kwargs not explicitly named by `__init__` are passed through to the `Line2D` constructor,
    allowing the user to specify custom line formatting in a form expected by `Line2D`.
    """

    def __init__(
        self,
        ax: Axes,
        position: float | int,
        orientation: Orientation = Orientation.VERTICAL,
        snap_to: Line2D | None = None,
        color: str = "limegreen",
        **kwargs: t.Any,
    ) -> None:
        self.orientation = orientation

        line_pos = (position, position)  # matplotlib expectes a coordinate pair
        if orientation == Orientation.HORIZONTAL:
            obj = Line2D(xdata=ax.get_xlim(), ydata=line_pos, color=color, **kwargs)
        elif orientation == Orientation.VERTICAL:
            obj = Line2D(xdata=line_pos, ydata=ax.get_ylim(), color=color, **kwargs)
        else:
            raise ValueError(f"Unsupported orientation provided: '{orientation}'")

        self.register_plot_object(obj, ax)

        # If provided, check if snap_to is a valid lineseries with data in it
        if snap_to is not None:
            try:
                snap_to.get_xdata()
            except AttributeError as e:
                raise ValueError("Cannot provide an empty lineseries to snapto") from e

        self.snap_to = snap_to

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

        if self.orientation == Orientation.VERTICAL:
            if self.snap_to:
                new_pos = limit_drag(self.snap_to.get_xdata(), event.xdata)
            else:
                new_pos = event.xdata

            self.myobj.set_xdata((new_pos, new_pos))
            self.myobj.set_ydata(self.parent_axes.get_ylim())
        elif self.orientation == Orientation.HORIZONTAL:
            if self.snap_to:
                new_pos = limit_drag(self.snap_to.get_ydata(), event.ydata)
            else:
                new_pos = event.xdata

            self.myobj.set_xdata(self.parent_axes.get_xlim())
            self.myobj.set_ydata((new_pos, new_pos))

        self.parent_canvas.draw()


def limit_drag(plotted_data: npt.ArrayLike, query: float) -> float:
    """Clamp the query value within the bounds of the provided dataset."""
    # Data series may not be sorted, so use min/max
    # I'm not sure how to properly type annotate this right now
    min_val, max_val = plotted_data.min(), plotted_data.max()  # type: ignore[union-attr]
    if query > max_val:
        return max_val  # type: ignore[no-any-return]
    elif query < min_val:
        return min_val  # type: ignore[no-any-return]
    else:
        return query
