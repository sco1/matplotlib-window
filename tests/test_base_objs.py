import pytest

from matplotlib_window.base import DragRect
from tests.conftest import PLOTOBJ_T


def test_dragrect_invalid_width_raises(plotobj: PLOTOBJ_T) -> None:
    _, ax = plotobj
    with pytest.raises(ValueError, match="greater than 1"):
        _ = DragRect(ax=ax, position=0, width=0)
