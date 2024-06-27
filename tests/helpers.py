from matplotlib.backend_bases import FigureCanvasBase


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
