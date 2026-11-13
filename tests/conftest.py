import typing as t

import matplotlib
import matplotlib.pyplot as plt
import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

# Tests interact with figures via dispatched events & don't need a GUI; the default interactive
# backend (e.g. TkAgg) can intermittently fail to initialize when repeatedly creating figures
matplotlib.use("Agg")

PLOTOBJ_T: t.TypeAlias = tuple[Figure, Axes]


@pytest.fixture
def plotobj() -> t.Generator[tuple[Figure, Axes], None, None]:
    fig, ax = plt.subplots()
    yield fig, ax

    plt.close()
