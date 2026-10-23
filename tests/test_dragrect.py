import typing as t

import pytest
from pytest_mock import MockerFixture

from matplotlib_window.base import DragRect, get_native_data
from tests.conftest import PLOTOBJ_T
from tests.helpers import (
    ALL_NAN_LINE,
    DUMMY_LINE,
    EMPTY_LINE,
    GAPPED_X,
    GAPPED_Y,
    SNAP_TO_DATA_PARAMS,
    drag,
    has_callback_to,
    native_extents,
)


def test_dragrect_invalid_width_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    with pytest.raises(ValueError, match="greater than"):
        _ = DragRect(ax=ax, position=0, width=0)


def test_dragrect_get_bounds(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0, width=1)
    assert dr.bounds == (0, 1)


def test_dragrect_limit_change_respans(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0.2, width=0.3)

    ax.set_ylim(5, 15)

    assert dr.myobj.get_xy() == pytest.approx((0.2, 5))
    assert dr.myobj.get_height() == pytest.approx(10)


def test_dragrect_click_disable(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0, width=1)

    parent_canvas = dr.parent_canvas
    assert has_callback_to(parent_canvas, "DragRect")

    dr._disable_click()
    assert dr.click_press == -1
    assert not has_callback_to(parent_canvas, "DragRect")


def test_dragrect_redraw_callback(plotobj: PLOTOBJ_T, mocker: MockerFixture) -> None:
    _, ax = plotobj
    callback = mocker.Mock()
    dr = DragRect(ax=ax, position=0, width=1, redraw_callback=callback)

    ax.set_ylim(0, 10)  # Limit change triggers a redraw
    callback.assert_called()
    assert dr.redraw_callback is callback


def test_dragrect_drag_after_external_move(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0.2, width=0.3)

    # Drag deltas should be relative to the rectangle's location when the drag starts, even if it
    # was moved by something other than a previous drag
    dr.myobj.set_x(0.4)
    drag(ax, (0.55, 0.5), (0.65, 0.5))
    assert dr.bounds == pytest.approx((0.5, 0.8))


def test_dragrect_snapto_none_passthrough(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0, width=1)
    assert dr.validate_snap_to(None) is None


def test_dragrect_snapto_empty_data_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0, width=1)
    with pytest.raises(ValueError, match="empty"):
        dr.validate_snap_to(EMPTY_LINE)


def test_dragrect_snapto_all_nan_data_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = DragRect(ax=ax, position=0, width=1)
    with pytest.raises(ValueError, match="finite"):
        dr.validate_snap_to(ALL_NAN_LINE)


def test_dragrect_snapto_nan_gaps(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(GAPPED_X, GAPPED_Y)[0]
    ax.set_xlim(-4, 8)  # Leave room to drag beyond the data inside the axes
    dr = DragRect(ax, position=1, width=1, snap_to=ls)

    drag(ax, (1.5, 12), (5.5, 12))
    assert dr.bounds == pytest.approx((3, 4))

    drag(ax, (3.5, 12), (-0.5, 12))
    assert dr.bounds == pytest.approx((0, 1))


def test_dragrect_snapto_nan_gaps_out_of_bounds_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(GAPPED_X, GAPPED_Y)[0]

    with pytest.raises(ValueError, match="bounds"):
        _ = DragRect(ax, position=3, width=2, snap_to=ls)


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


@SNAP_TO_DATA_PARAMS
def test_dragrect_snapto_data_types(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(data, range(5))[0]
    lo, hi, span = native_extents(ls, "x")
    ax.set_xlim(lo - span, hi + span)  # Leave room to drag beyond the data inside the axes

    native = get_native_data(ls, "x")
    width = native[2] - native[1]
    dr = DragRect(ax, position=native[1], width=width, snap_to=ls)

    # Drag from the middle of the rectangle so the click lands on the patch; dragging by the full
    # data span pushes the leading edge beyond the data while keeping the cursor inside the axes
    mid = native[1] + width / 2
    drag(ax, (mid, 2), (mid + span, 2))
    assert dr.bounds == pytest.approx((hi - width, hi), abs=span * 1e-6)

    mid = hi - width / 2
    drag(ax, (mid, 2), (mid - span, 2))
    assert dr.bounds == pytest.approx((lo, lo + width), abs=span * 1e-6)


@SNAP_TO_DATA_PARAMS
def test_dragrect_snapto_data_types_out_of_bounds_raises(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(data, range(5))[0]
    _, hi, span = native_extents(ls, "x")

    with pytest.raises(ValueError, match="bounds"):
        _ = DragRect(ax, position=hi, width=span, snap_to=ls)


@SNAP_TO_DATA_PARAMS
def test_dragrect_data_type_position_width(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(data, range(5))[0]
    native = get_native_data(ls, "x")

    dr = DragRect(ax, position=data[1], width=(data[2] - data[1]), snap_to=ls)
    assert all(isinstance(edge, float) for edge in dr.bounds)
    assert dr.bounds == pytest.approx((native[1], native[2]))


@SNAP_TO_DATA_PARAMS
def test_dragrect_data_type_negative_width_raises(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ax.plot(data, range(5))

    with pytest.raises(ValueError, match="greater than"):
        _ = DragRect(ax, position=data[2], width=(data[1] - data[2]))
