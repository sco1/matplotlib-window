# matplotlib-window
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/matplotlib-window/1.1.0?logo=python&logoColor=FFD43B)](https://pypi.org/project/matplotlib-window/)
[![PyPI](https://img.shields.io/pypi/v/matplotlib-window?logo=Python&logoColor=FFD43B)](https://pypi.org/project/matplotlib-window/)
[![PyPI - License](https://img.shields.io/pypi/l/matplotlib-window?color=magenta)](https://github.com/sco1/matplotlib-window/blob/main/LICENSE)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sco1/matplotlib-window/main.svg)](https://results.pre-commit.ci/latest/github/sco1/matplotlib-window/main)

Draggable data windowing for matplotlib plots. Inspired by the adventures of past me and [`dragpy`](https://github.com/sco1-archive/dragpy).

![fixed window sample](/example/fixed_width_window.gif?raw=true)

## Interface
For most use cases, interaction with this library is done via the helper wrappers in `matplotlib_window.window`. These functions will accept the user data and build the plots directly for windowing.

### `fixed_window`
Plot the provided data & build a draggable fixed-width window to select bounds of interest; the x-locations of the edges of the window are returned once the figure window is closed.

#### Parameters
| Parameter      | Description                                                                 | Type                   | Default          |
|----------------|-----------------------------------------------------------------------------|------------------------|------------------|
| `x_data`       | x data values to plot                                                       | `Sequence[int\|float]` | Required         |
| `y_data`       | y data values to plot                                                       | `Sequence[int\|float]` | Required         |
| `position`     | x-coordinate of the left edge of the window                                 | `int\|float`           | Required         |
| `window_width` | Width, along the x-axis, of the draggable window                            | `int\|float`           | Required         |
| `snap_to_data` | Prevent dragging of the window beyond beyond the bounds of the plotted data | `bool`                 | `True`           |
| `axes_kwargs`  | Optional kwargs to pass to the `Axes` constructor<sup>1</sup>               | `dict[str, Any]`       | `{"title": ...}` |
| `plot_kwargs`  | Optional kwargs to pass to the plotting call<sup>2</sup>                    | `dict[str, Any]`       | `{}`             |

1. kwargs are passed directly to the `Axes` constructor, see the [`matplotlib.axes.Axes` documentation](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.html#matplotlib.axes.Axes) for supported arguments.
2. kwargs are passed directly to the plotting call, see the [`matplotlib.pyplot.plot` documentation](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html) for supported arguments.

### `flexible_window`
Plot the provided data & build a flexible-width window to select bounds of interest; the x-locations of the edges of the window are returned once the figure window is closed.

#### Parameters
| Parameter         | Description                                                                 | Type                   | Default          |
|-------------------|-----------------------------------------------------------------------------|------------------------|------------------|
| `x_data`          | x data values to plot                                                       | `Sequence[int\|float]` | Required         |
| `y_data`          | y data values to plot                                                       | `Sequence[int\|float]` | Required         |
| `position`        | x-coordinate of the left edge of the window                                 | `int\|float`           | Required         |
| `window_width`    | Starting width, along the x-axis, of the flexible window                    | `int\|float`           | Required         |
| `snap_to_data`    | Prevent dragging of the window beyond beyond the bounds of the plotted data | `bool`                 | `True`           |
| `allow_face_drag` | Allow dragging of the window using its face<sup>1</sup>                     | `bool`                 | `False`          |
| `axes_kwargs`     | Optional kwargs to pass to the `Axes` constructor<sup>2</sup>               | `dict[str, Any]`       | `{"title": ...}` |
| `plot_kwargs`     | Optional kwargs to pass to the plotting call<sup>3</sup>                    | `dict[str, Any]`       | `{}`             |

1. Currently not implemented
2. kwargs are passed directly to the `Axes` constructor, see the [`matplotlib.axes.Axes` documentation](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.html#matplotlib.axes.Axes) for supported arguments.
3. kwargs are passed directly to the plotting call, see the [`matplotlib.pyplot.plot` documentation](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.plot.html) for supported arguments.
