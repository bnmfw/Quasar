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

        super().__init__(f, increasing, iteration_limit, report)
        self.__lower_bound: float = lower_bound
        self.__upper_bound: float = upper_bound
        self.__x_precision: float = x_precision
        self.__y_precision: float = y_precision

    def root(self) -> float:
        """
        Finds the approximation for the root

        Returns:
            float: the root
        """
        x0: float = self.__lower_bound
        x1: float = self.__upper_bound
        f0: float = self._f(x0)
        f1: float = self._f(x1)

        x0, f0, x1, f1 = self.define_bounds(x0, f0, x1, f1)

        if x0 is None:
            return None

        for i in range(self._iteration_limit):

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
            f2 = self._f(x2)

            if f2 == 0:
                return x2

            if f2 / f0 > 0:
                x0, f0 = x2, f2

            else:
                x1, f1 = x2, f2

        return None
