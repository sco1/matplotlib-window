import typing as t

import matplotlib.pyplot as plt
import pytest
from pytest_mock import MockType, MockerFixture

from matplotlib_window.window import DEFAULT_AXES_KWARGS, fixed_window, flexible_window
from tests.helpers import drag

X_DATA = [0, 1, 2, 3, 4, 5]
Y_DATA = [10, 11, 12, 13, 14, 15]


@pytest.fixture
def mock_show(mocker: MockerFixture) -> t.Generator[MockType, None, None]:
    """
    Patch `plt.show` so the window helpers return immediately.

    A `side_effect` may be set on the returned mock to simulate user interaction with the figure
    before it is "closed".
    """
    show = mocker.patch("matplotlib.pyplot.show")
    yield show

    # The window helpers create their own figures
    plt.close("all")


def test_fixed_window_returns_dragged_bounds(mock_show: MockType) -> None:
    mock_show.side_effect = lambda: drag(plt.gca(), (1.5, 12), (2.5, 12))

    bounds = fixed_window(X_DATA, Y_DATA, position=1, window_width=1)

    mock_show.assert_called_once()
    assert bounds == pytest.approx((2, 3))


def test_fixed_window_kwargs_merged(mock_show: MockType) -> None:
    fixed_window(
        X_DATA,
        Y_DATA,
        position=1,
        window_width=1,
        axes_kwargs={"xlabel": "Time"},
        plot_kwargs={"color": "red"},
    )

    ax = plt.gca()
    assert ax.get_title() == DEFAULT_AXES_KWARGS["title"]
    assert ax.get_xlabel() == "Time"
    assert ax.lines[0].get_color() == "red"


def test_fixed_window_axes_kwargs_override_default(mock_show: MockType) -> None:
    fixed_window(X_DATA, Y_DATA, position=1, window_width=1, axes_kwargs={"title": "Custom"})

    assert plt.gca().get_title() == "Custom"


def test_fixed_window_snap_to_data(mock_show: MockType) -> None:
    # Window extends beyond the right edge of the plotted data
    with pytest.raises(ValueError, match="bounds"):
        fixed_window(X_DATA, Y_DATA, position=4.5, window_width=1, snap_to_data=True)


def test_fixed_window_no_snap_to_data(mock_show: MockType) -> None:
    bounds = fixed_window(X_DATA, Y_DATA, position=4.5, window_width=1, snap_to_data=False)

    assert bounds == pytest.approx((4.5, 5.5))


def test_flexible_window_returns_dragged_bounds(mock_show: MockType) -> None:
    mock_show.side_effect = lambda: drag(plt.gca(), (2, 12), (3, 12))  # Drag the right edge

    bounds = flexible_window(X_DATA, Y_DATA, position=1, window_width=1)

    mock_show.assert_called_once()
    assert bounds == pytest.approx((1, 3))


def test_flexible_window_kwargs_merged(mock_show: MockType) -> None:
    flexible_window(
        X_DATA,
        Y_DATA,
        position=1,
        window_width=1,
        axes_kwargs={"xlabel": "Time"},
        plot_kwargs={"color": "red"},
    )

    ax = plt.gca()
    assert ax.get_title() == DEFAULT_AXES_KWARGS["title"]
    assert ax.get_xlabel() == "Time"
    assert ax.lines[0].get_color() == "red"


def test_flexible_window_axes_kwargs_override_default(mock_show: MockType) -> None:
    flexible_window(X_DATA, Y_DATA, position=1, window_width=1, axes_kwargs={"title": "Custom"})

    assert plt.gca().get_title() == "Custom"


def test_flexible_window_snap_to_data(mock_show: MockType) -> None:
    # Window extends beyond the right edge of the plotted data
    with pytest.raises(ValueError, match="bounds"):
        flexible_window(X_DATA, Y_DATA, position=4.5, window_width=1, snap_to_data=True)


def test_flexible_window_no_snap_to_data(mock_show: MockType) -> None:
    bounds = flexible_window(X_DATA, Y_DATA, position=4.5, window_width=1, snap_to_data=False)

    assert bounds == pytest.approx((4.5, 5.5))


def test_flexible_window_face_drag_enabled(mock_show: MockType) -> None:
    mock_show.side_effect = lambda: drag(plt.gca(), (1.5, 12), (2.5, 12))  # Drag the face

    bounds = flexible_window(X_DATA, Y_DATA, position=1, window_width=1, allow_face_drag=True)

    assert bounds == pytest.approx((2, 3))


def test_flexible_window_face_drag_disabled(mock_show: MockType) -> None:
    mock_show.side_effect = lambda: drag(plt.gca(), (1.5, 12), (2.5, 12))  # Drag the face

    bounds = flexible_window(X_DATA, Y_DATA, position=1, window_width=1, allow_face_drag=False)

    assert bounds == pytest.approx((1, 2))
