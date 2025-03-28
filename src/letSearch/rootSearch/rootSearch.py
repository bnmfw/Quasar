from abc import ABC
from typing import Callable


class RootSearch(ABC):
    def __init__(
        self,
        f: Callable,
        increasing: bool,
        iteration_limit: int = 50,
        report: bool = False,
    ) -> None:
        self._f: Callable = f
        self.__report: bool = report
        self._increasing: bool = increasing
        self._iteration_limit: int = iteration_limit

    def define_bounds(self, x0: float, f0: float, x1: float, f1: float) -> float:
        """
        Guarantees f0 and f1 are in different sides of the linear zone

        Args:
            x0 (float): lower bound
            f0 (float): lower bound image
            x1 (float): upper bound
            f1 (float): upper bound image

        Returns:
            list[float]: bounds
        """

        step = 50

        # x1 and x0 in oposite sides
        if f1 / f0 < 0:
            return x0, f0, x1, f1

        self._log(f"Starting Border Search")
        # Guarantees oposite borders
        for i in range(self._iteration_limit):

            self._log(
                f"{i}"
                f"\tlower border: x={x0:.1f} y={f0:.3f}"
                f"\tupper border: x={x1:.1f} y={f1:.3f}"
            )

            if (self._increasing and f0 > 0) or (not self._increasing and f0 < 0):
                x1, f1 = x0, f0
                x0 -= step
                x0 = max(0, x0)
                f0 = self._f(x0)

            else:
                x0, f0 = x1, f1
                x1 += step
                x1 = max(0, x1)
                f1 = self._f(x1)

            step *= 2

            # x1 and x0 in oposite sides
            if f1 / f0 < 0:
                return x0, f0, x1, f1

        return [None] * 4

    def root() -> float:
        pass

    def _log(self, text: str) -> None:
        if self.__report:
            print(text)
