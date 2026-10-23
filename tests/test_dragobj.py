import pytest

from matplotlib_window.base import _DraggableObject
from tests.helpers import ALL_NAN_LINE, EMPTY_LINE


def test_dragobj_snapto_none_passthrough() -> None:
    do = _DraggableObject()
    assert do.validate_snap_to(None) is None


def test_dragobj_snapto_empty_data_raises() -> None:
    do = _DraggableObject()
    with pytest.raises(ValueError, match="empty"):
        do.validate_snap_to(EMPTY_LINE)


def test_dragobj_snapto_all_nan_data_raises() -> None:
    do = _DraggableObject()
    with pytest.raises(ValueError, match="finite"):
        do.validate_snap_to(ALL_NAN_LINE)
