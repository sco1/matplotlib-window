import typing as t

import matplotlib.pyplot as plt
import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

PLOTOBJ_T: t.TypeAlias = tuple[Figure, Axes]


@pytest.fixture
def plotobj() -> tuple[Figure, Axes]:
    fig, ax = plt.subplots()
    return fig, ax
