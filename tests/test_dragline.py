import typing as t

import pytest
from pytest_mock import MockerFixture

from matplotlib_window.base import DragLine, Orientation, get_native_data
from tests.conftest import PLOTOBJ_T
from tests.helpers import (
    ALL_NAN_LINE,
    DUMMY_LINE,
    EMPTY_LINE,
    GAPPED_X,
    GAPPED_Y,
    SNAP_TO_DATA_PARAMS,
    drag,
    native_extents,
)


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


def test_dragline_redraw_callback(plotobj: PLOTOBJ_T, mocker: MockerFixture) -> None:
    _, ax = plotobj
    callback = mocker.Mock()
    dl = DragLine(ax=ax, position=0, redraw_callback=callback)

    ax.set_ylim(0, 10)  # Limit change triggers a redraw
    callback.assert_called()
    assert dl.redraw_callback is callback


def test_dragline_set_location_vertical(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax=ax, position=0.2, orientation=Orientation.VERTICAL)

    dl.set_location(0.7)
    assert dl.location == pytest.approx(0.7)
    assert get_native_data(dl.myobj, "x") == pytest.approx([0.7, 0.7])


def test_dragline_set_location_horizontal(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax=ax, position=0.2, orientation=Orientation.HORIZONTAL)

    dl.set_location(0.7)
    assert dl.location == pytest.approx(0.7)
    assert get_native_data(dl.myobj, "y") == pytest.approx([0.7, 0.7])


def test_dragline_snapto_none_passthrough(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax=ax, position=0)
    assert dl.validate_snap_to(None) is None


def test_dragline_snapto_empty_data_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax=ax, position=0)
    with pytest.raises(ValueError, match="empty"):
        dl.validate_snap_to(EMPTY_LINE)


def test_dragline_snapto_all_nan_data_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax=ax, position=0)
    with pytest.raises(ValueError, match="finite"):
        dl.validate_snap_to(ALL_NAN_LINE)


def test_vertical_dragline_snapto_nan_gaps(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(GAPPED_X, GAPPED_Y)[0]
    ax.set_xlim(-4, 8)  # Leave room to drag beyond the data inside the axes
    dl = DragLine(ax, position=2, orientation=Orientation.VERTICAL, snap_to=ls)

    drag(ax, (2, 12), (6, 12))
    assert dl.location == pytest.approx(4)

    drag(ax, (4, 12), (-2, 12))
    assert dl.location == pytest.approx(0)


def test_horizontal_dragline_snapto_nan_gaps(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(GAPPED_X, GAPPED_Y)[0]
    ax.set_ylim(6, 18)  # Leave room to drag beyond the data inside the axes
    dl = DragLine(ax, position=12, orientation=Orientation.HORIZONTAL, snap_to=ls)

    drag(ax, (2, 12), (2, 16))
    assert dl.location == pytest.approx(14)

    drag(ax, (2, 14), (2, 8))
    assert dl.location == pytest.approx(10)


def test_dragline_snapto_nan_gaps_out_of_bounds_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(GAPPED_X, GAPPED_Y)[0]

    with pytest.raises(ValueError, match="bounds"):
        _ = DragLine(ax, position=5, snap_to=ls)


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
    _ = DragLine(ax, position=11, orientation=Orientation.HORIZONTAL, snap_to=DUMMY_LINE)


def test_vertical_dragline_snapto_oob_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax, position=101, orientation=Orientation.VERTICAL)

    with pytest.raises(ValueError, match="bounds"):
        dl.validate_snap_to(DUMMY_LINE)


def test_horizontal_dragline_snapto_oob_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    dl = DragLine(ax, position=1, orientation=Orientation.HORIZONTAL)

    with pytest.raises(ValueError, match="bounds"):
        dl.validate_snap_to(DUMMY_LINE)


@SNAP_TO_DATA_PARAMS
def test_vertical_dragline_snapto_data_types(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(data, range(5))[0]
    lo, hi, span = native_extents(ls, "x")
    ax.set_xlim(lo - span, hi + span)  # Leave room to drag beyond the data inside the axes

    start = get_native_data(ls, "x")[1]
    dl = DragLine(ax, position=start, orientation=Orientation.VERTICAL, snap_to=ls)

    drag(ax, (start, 2), (hi + span / 2, 2))
    assert dl.location == pytest.approx(hi, abs=span * 1e-6)

    drag(ax, (hi, 2), (lo - span / 2, 2))
    assert dl.location == pytest.approx(lo, abs=span * 1e-6)


@SNAP_TO_DATA_PARAMS
def test_horizontal_dragline_snapto_data_types(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(range(5), data)[0]
    lo, hi, span = native_extents(ls, "y")
    ax.set_ylim(lo - span, hi + span)  # Leave room to drag beyond the data inside the axes

    start = get_native_data(ls, "y")[1]
    dl = DragLine(ax, position=start, orientation=Orientation.HORIZONTAL, snap_to=ls)

    drag(ax, (2, start), (2, hi + span / 2))
    assert dl.location == pytest.approx(hi, abs=span * 1e-6)

    drag(ax, (2, hi), (2, lo - span / 2))
    assert dl.location == pytest.approx(lo, abs=span * 1e-6)


@SNAP_TO_DATA_PARAMS
def test_dragline_snapto_data_types_out_of_bounds_raises(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(data, range(5))[0]
    _, hi, span = native_extents(ls, "x")

    with pytest.raises(ValueError, match="bounds"):
        _ = DragLine(ax, position=(hi + span), snap_to=ls)


# Positions & widths may also be provided in the plotted data's own units (e.g. a datetime &
# timedelta), but are always reported back in the axes' native float units
@SNAP_TO_DATA_PARAMS
def test_vertical_dragline_data_type_position(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(data, range(5))[0]
    native = get_native_data(ls, "x")

    dl = DragLine(ax, position=data[1], orientation=Orientation.VERTICAL, snap_to=ls)
    assert isinstance(dl.location, float)
    assert dl.location == pytest.approx(native[1])


@SNAP_TO_DATA_PARAMS
def test_horizontal_dragline_data_type_position(data: t.Any, plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    ls = ax.plot(range(5), data)[0]
    native = get_native_data(ls, "y")

    dl = DragLine(ax, position=data[1], orientation=Orientation.HORIZONTAL, snap_to=ls)
    assert isinstance(dl.location, float)
    assert dl.location == pytest.approx(native[1])
