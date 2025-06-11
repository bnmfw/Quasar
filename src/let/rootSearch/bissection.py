from typing import Callable
from .rootSearch import RootSearch


class Bissection(RootSearch):
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
        """
        Constructor

        Args:
            f (Callable): function to be minimized
            lower_bound (float): lower bound of the binary search
            upper_bound (float): upper bound of the binary search
            increasing (bool): whether the function is increasing or decreasing
            x_precision (float): tolerance for final upper-lower
            y_precision (float): tolerance for f(root) value
            report (bool): Whether report should be printed
            iteration_limit (float): A limit of function iterations
        """
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

        x0, f0, x1, f1 = self.define_bounds(x0, f0, x1, f1, 50)

        # Actual binary search
        for i in range(self._iteration_limit):

            x2 = float((x0 + x1) / 2)

            # Function call
            f2 = self._f(x2)
            self._log(
                f"{i}\tcurrent: {x2:.1f}\tpeak_tension: {f2:.3f}\tbottom: {x0:.1f}\ttop: {x1:.1f}"
            )

            # Precision satisfied
            if abs(f2) < self.__y_precision or abs(x1 - x0) < self.__x_precision:
                self._log("Minimal Let Found - Convergence\n")
                return x2

            if f1 / f0 > 0:
                raise RuntimeError(
                    f"Both bounds of binary search in the same side {f1} and {f0}"
                )
            if f1 / f2 > 0:
                f1 = f2
                x1 = x2
            elif f0 / f2 > 0:
                f0 = f2
                x0 = x2

        self._log("Minimal Let NOT Found - Maximum Simulation Number Reached\n")
        return None
