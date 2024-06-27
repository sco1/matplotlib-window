import typing as t

import matplotlib.pyplot as plt
import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

PLOTOBJ_T: t.TypeAlias = tuple[Figure, Axes]


@pytest.fixture
def plotobj() -> t.Generator[tuple[Figure, Axes], None, None]:
    fig, ax = plt.subplots()
    yield fig, ax

    plt.close()
