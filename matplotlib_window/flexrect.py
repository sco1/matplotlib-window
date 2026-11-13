from collections import abc
from functools import partial

from matplotlib.axes import Axes
from matplotlib.lines import Line2D

from matplotlib_window.coordinates import to_native, to_native_span, transform_rect_params
from matplotlib_window.draggable import NUMERIC_T, UNIT_T
from matplotlib_window.dragline import DragLine
from matplotlib_window.dragrect import DragRect


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
