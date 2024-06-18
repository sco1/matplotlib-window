import numpy as np
import pytest
from matplotlib.lines import Line2D

from matplotlib_window.base import DragLine, DragRect, Orientation, _DraggableObject
from tests.conftest import PLOTOBJ_T


def test_dragobj_snapto_none_passthrough() -> None:
    do = _DraggableObject()
    assert do.validate_snap_to(None) is None


def test_dragline_snapto_none_passthrough(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax=ax, position=0)
    assert dl.validate_snap_to(None) is None


def test_dragrect_snapto_none_passthrough(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0, width=1)
    assert dr.validate_snap_to(None) is None


EMPTY_LINE = Line2D(xdata=np.array([]), ydata=np.array([]))


def test_dragobj_snapto_empty_data_raises() -> None:
    do = _DraggableObject()
    with pytest.raises(ValueError, match="empty"):
        do.validate_snap_to(EMPTY_LINE)


def test_dragline_snapto_empty_data_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax=ax, position=0)
    with pytest.raises(ValueError, match="empty"):
        dl.validate_snap_to(EMPTY_LINE)


def test_dragrect_snapto_empty_data_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0, width=1)
    with pytest.raises(ValueError, match="empty"):
        dr.validate_snap_to(EMPTY_LINE)


DUMMY_LINE = Line2D(xdata=np.array([0, 1, 2]), ydata=np.array([0, 1, 2]))


def test_vertical_dragline_snapto_out_of_bounds_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax, position=3, orientation=Orientation.VERTICAL)

    with pytest.raises(ValueError, match="bounds"):
        dl.validate_snap_to(DUMMY_LINE)


def test_horizontal_dragline_snapto_out_of_bounds_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax, position=3, orientation=Orientation.HORIZONTAL)

    with pytest.raises(ValueError, match="bounds"):
        dl.validate_snap_to(DUMMY_LINE)


def test_vertical_dragline_valid_snapto(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    _ = DragLine(ax, position=1, orientation=Orientation.VERTICAL, snap_to=DUMMY_LINE)


def test_horizontal_dragline_valid_snapto(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    _ = DragLine(ax, position=1, orientation=Orientation.HORIZONTAL, snap_to=DUMMY_LINE)


RECT_BOUNDS_TEST_CASES = (
    (-1, 1),  # Left edge out
    (0, 3),  # Right edge out
    (-1, 4),  # Both edges out
)


@pytest.mark.parametrize(("position", "width"), RECT_BOUNDS_TEST_CASES)
def test_dragrect_snapto_out_of_bounds_raises(
    position: int, width: int, plotobj: PLOTOBJ_T
) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=position, width=width)

    with pytest.raises(ValueError, match="bounds"):
        dr.validate_snap_to(DUMMY_LINE)


def test_dragrect_valid_snapto(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    _ = DragRect(ax=ax, position=0, width=1, snap_to=DUMMY_LINE)
