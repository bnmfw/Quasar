from typing import Callable
from .rootSearch import RootSearch


class FalsePosition(RootSearch):
    def __init__(
        self,
        f: Callable,
        lower_bound: float,
        upper_bound: float,
        increasing: bool,
        x_precision: float = 0.1,
        y_precision: float = 0.001,
        report: bool = False,
        iteration_limit: int = 50,
    ) -> None:

        super().__init__(f, report)
        self.__f: Callable = f
        self.__lower_bound: float = lower_bound
        self.__upper_bound: float = upper_bound
        self.__increasing: bool = increasing
        self.__x_precision: float = x_precision
        self.__y_precision: float = y_precision
        self.__iteration_limit: int = iteration_limit

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
        for i in range(self.__iteration_limit):

            self._log(
                f"{i}"
                f"\tlower border: x={x0:.1f} y={f0:.3f}"
                f"\tupper border: x={x1:.1f} y={f1:.3f}"
            )

            if (self.__increasing and f0 > 0) or (not self.__increasing and f0 < 0):
                x1, f1 = x0, f0
                x0 -= step
                x0 = max(0, x0)
                f0 = self.__f(x0)

            else:
                x0, f0 = x1, f1
                x1 += step
                x1 = max(0, x1)
                f1 = self.__f(x1)

            step *= 2

            # x1 and x0 in oposite sides
            if f1 / f0 < 0:
                return x0, f0, x1, f1

        return None * 4

    def root(self) -> float:
        """
        Finds the approximation for the root

        Returns:
            float: the root
        """
        x0: float = self.__lower_bound
        x1: float = self.__upper_bound
        f0: float = self.__f(x0)
        f1: float = self.__f(x1)

        x0, f0, x1, f1 = self.define_bounds(x0, f0, x1, f1)

        if x0 is None:
            return None

        for i in range(self.__iteration_limit):

            self._log(
                f"{i}"
                f"\tcurrent: {x1:.1f}"
                f"\tpeak_tension: {f1:.3f}"
                f"\tlastX: {x0:.1f}"
                f"\tlastf(X): {f0:.3f}"
            )

            for f, x in [(f0, x0), (f1, x1)]:
                if abs(f) < self.__y_precision:
                    self._log("Minimal Let Found - Convergence")
                    return x

            if abs(x1 - x0) < self.__x_precision:
                self._log("Minimal Let Found - Convergence")
                return (x1 + x0) / 2

            x2 = x0 - f0 * (x1 - x0) / (f1 - f0)
            f2 = self.__f(x2)

            if f2 == 0:
                return x2

            if f2 / f0 > 0:
                x0, f0 = x2, f2

            else:
                x1, f1 = x2, f2

        return None
