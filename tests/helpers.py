from matplotlib.axes import Axes
from matplotlib.backend_bases import FigureCanvasBase, MouseButton, MouseEvent


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
