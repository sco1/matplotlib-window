import pytest

from matplotlib_window.base import DragLine, DragRect, FlexibleRect, Orientation
from tests.conftest import PLOTOBJ_T
from tests.helpers import has_callback_to


def test_dragline_invalid_orientation_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    with pytest.raises(ValueError, match="orientation"):
        _ = DragLine(ax=ax, position=0, orientation="beans")  # type: ignore[arg-type]


DRAGLINE_LOCATION_TEST_CASES = (
    (Orientation.VERTICAL, 1),
    (Orientation.VERTICAL, 1),
)


@pytest.mark.parametrize(("orientation", "truth_location"), DRAGLINE_LOCATION_TEST_CASES)
def test_dragline_get_location(
    orientation: Orientation, truth_location: int, plotobj: PLOTOBJ_T
) -> None:
    _, ax = plotobj
    dl = DragLine(ax=ax, position=1, orientation=orientation)
    assert dl.location == truth_location


def test_dragrect_invalid_width_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    with pytest.raises(ValueError, match="greater than"):
        _ = DragRect(ax=ax, position=0, width=0)


def test_dragrect_get_bounds(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0, width=1)
    assert dr.bounds == (0, 1)


def test_dragrect_click_disable(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0, width=1)

    parent_canvas = dr.parent_canvas
    assert has_callback_to(parent_canvas, "DragRect")

    dr._disable_click()
    assert dr.click_press == -1
    assert not has_callback_to(parent_canvas, "DragRect")


def test_flexrect_invalid_width_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    with pytest.raises(ValueError, match="greater than"):
        _ = FlexibleRect(ax=ax, position=0, width=0)


def test_flexrect_get_bounds(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = FlexibleRect(ax=ax, position=0, width=1)
    assert dr.bounds == (0, 1)


def test_flexrect_disables_click(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = FlexibleRect(ax=ax, position=0, width=1, allow_face_drag=False)

    parent_canvas = dr.face.parent_canvas
    assert not has_callback_to(parent_canvas, "DragRect")
