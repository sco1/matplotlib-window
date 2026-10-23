import typing as t

import numpy as np
import pytest
from matplotlib.lines import Line2D
from pytest_mock import MockerFixture

from matplotlib_window.base import FlexibleRect, get_native_data
from tests.conftest import PLOTOBJ_T
from tests.helpers import SNAP_TO_DATA_PARAMS, drag, has_callback_to


def test_flexrect_invalid_width_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    with pytest.raises(ValueError, match="greater than"):
        _ = FlexibleRect(ax=ax, position=0, width=0)


def test_flexrect_get_bounds(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = FlexibleRect(ax=ax, position=0, width=1)
    assert dr.bounds == (0, 1)


def test_flexrect_limit_change_respans(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    fr = FlexibleRect(ax=ax, position=0.2, width=0.3)

    ax.set_ylim(5, 15)

    assert fr.face.myobj.get_xy() == pytest.approx((0.2, 5))
    assert fr.face.myobj.get_height() == pytest.approx(10)


def test_flexrect_disables_click(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dr = FlexibleRect(ax=ax, position=0, width=1, allow_face_drag=False)

    parent_canvas = dr.face.parent_canvas
    assert not has_callback_to(parent_canvas, "DragRect")


def test_flexrect_redraw_callback(plotobj: PLOTOBJ_T, mocker: MockerFixture) -> None:
    _, ax = plotobj
    callback = mocker.Mock()
    fr = FlexibleRect(ax=ax, position=0, width=1, redraw_callback=callback)

    ax.set_ylim(0, 10)  # Limit change triggers a redraw
    callback.assert_called()
    assert fr.redraw_callback is callback


def test_flexrect_face_drag_disabled_by_default(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    fr = FlexibleRect(ax=ax, position=0.2, width=0.3)

    drag(ax, (0.35, 0.5), (0.45, 0.5))
    assert fr.bounds == pytest.approx((0.2, 0.5))
    assert fr.face.bounds == pytest.approx((0.2, 0.5))


def test_flexrect_face_drag_moves_edges(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    fr = FlexibleRect(ax=ax, position=0.2, width=0.3, allow_face_drag=True)

    drag(ax, (0.35, 0.5), (0.45, 0.5))
    assert fr.bounds == pytest.approx((0.3, 0.6))
    assert fr.face.bounds == pytest.approx((0.3, 0.6))


def test_flexrect_face_drag_after_edge_drag(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    fr = FlexibleRect(ax=ax, position=0.2, width=0.3, allow_face_drag=True)

    # Widen using the right edge, then drag the face; the face should retain the new width & not
    # jump back to its pre-resize location
    drag(ax, (0.5, 0.5), (0.7, 0.5))
    assert fr.bounds == pytest.approx((0.2, 0.7))

    drag(ax, (0.45, 0.5), (0.55, 0.5))
    assert fr.bounds == pytest.approx((0.3, 0.8))
    assert fr.face.bounds == pytest.approx((0.3, 0.8))


def test_flexrect_face_drag_crossed_edges(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    fr = FlexibleRect(ax=ax, position=0.2, width=0.3, allow_face_drag=True)

    # Drag the left edge past the right edge, then drag the face
    drag(ax, (0.2, 0.5), (0.7, 0.5))
    assert fr.bounds == pytest.approx((0.5, 0.7))

    drag(ax, (0.6, 0.5), (0.5, 0.5))
    assert fr.bounds == pytest.approx((0.4, 0.6))
    assert fr.face.bounds == pytest.approx((0.4, 0.6))


FACE_DRAG_SNAP_TO = Line2D(xdata=np.array([0, 0.5, 1]), ydata=np.array([10, 11, 10]))


def test_flexrect_face_drag_snapto_clamps_right(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ax.set_xlim(-1, 2)  # Leave room to drag beyond the snap_to data while still inside the axes
    fr = FlexibleRect(
        ax=ax, position=0.2, width=0.3, snap_to=FACE_DRAG_SNAP_TO, allow_face_drag=True
    )

    drag(ax, (0.35, 0.5), (1.35, 0.5))
    assert fr.bounds == pytest.approx((0.7, 1.0))
    assert fr.face.bounds == pytest.approx((0.7, 1.0))


def test_flexrect_face_drag_snapto_clamps_left(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ax.set_xlim(-1, 2)  # Leave room to drag beyond the snap_to data while still inside the axes
    fr = FlexibleRect(
        ax=ax, position=0.2, width=0.3, snap_to=FACE_DRAG_SNAP_TO, allow_face_drag=True
    )

    drag(ax, (0.35, 0.5), (-0.65, 0.5))
    assert fr.bounds == pytest.approx((0.0, 0.3))
    assert fr.face.bounds == pytest.approx((0.0, 0.3))


def test_flexrect_face_drag_redraw_callback(plotobj: PLOTOBJ_T, mocker: MockerFixture) -> None:
    _, ax = plotobj
    callback = mocker.Mock()
    _ = FlexibleRect(ax=ax, position=0.2, width=0.3, redraw_callback=callback, allow_face_drag=True)

    drag(ax, (0.35, 0.5), (0.45, 0.5))
    callback.assert_called()


@SNAP_TO_DATA_PARAMS
def test_flexrect_data_type_position_width(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(data, range(5))[0]
    native = get_native_data(ls, "x")

    fr = FlexibleRect(ax, position=data[1], width=(data[2] - data[1]), snap_to=ls)
    assert all(isinstance(edge, float) for edge in fr.bounds)
    assert fr.bounds == pytest.approx((native[1], native[2]))
    assert fr.face.bounds == pytest.approx((native[1], native[2]))


@SNAP_TO_DATA_PARAMS
def test_flexrect_data_type_negative_width_raises(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ax.plot(data, range(5))

    with pytest.raises(ValueError, match="greater than"):
        _ = FlexibleRect(ax, position=data[2], width=(data[1] - data[2]))
