from typing import Callable
from .rootSearch import RootSearch


class Secant(RootSearch):
    def __init__(
        self,
        f: Callable,
        root_guess: float,
        increasing: bool,
        root_guess_image: float = None,
        x_precision: float = 0.1,
        y_precision: float = 0.001,
        perturbation: float = 0.03,
        report: bool = False,
        iteration_limit: int = 50,
    ) -> None:
        """
        Constructor

        Args:
            f (Callable): function to be minimized
            root_guess (float): An aproximation of the root
            increasing (bool): Whether the function increases with X or decreases
            root_guess_image (float): f(root_guess) if already calculated
            x_precision (float): tolerance for final x1-x0
            x_precision (float): tolerance for f(root) value
            perturbation (float): a perturbation to be applied to the root_guess (% of x0)
            report (bool): Whether report should be printed
            iteration_limit (float): A limit of function iterations
        """
        super().__init__(f, report)
        self.__f: Callable = f
        self.__guess: float = root_guess
        self.__guess_image: float = root_guess_image
        self.__increasing: bool = increasing
        self.__x_precision: float = x_precision
        self.__y_precision: float = y_precision
        self.__perturbation: float = perturbation
        self.__iteration_limit: int = iteration_limit

    def root(self) -> float:
        """
        Finds the approximation for the root

        Returns:
            float: the root
        """
        f_calls: int = 0
        x0 = self.__guess

        f0 = self.__guess_image
        if f0 is None:
            f0 = self.__f(x0)
            f_calls += 1
        if abs(f0) < self.__y_precision:
            self._log("Minimal Let Found - Convergence")
            return f_calls, x0

        x1 = self.__guess
        direction = (
            1
            if (self.__increasing and f0 < 0) or (not self.__increasing and f0 > 0)
            else -1
        )
        offset = self.__perturbation * x0 * direction
        x1 += offset
        f1 = self.__f(x1)
        f_calls += 1

        out_of_offset_loop = False
        for i in range(self.__iteration_limit):

            self._log(
                f"{i}\tcurrent: {x1:.1f}"
                f"\tpeak_tension: {f1:.3f}"
                f"\tlastX: {x0:.1f}"
                f"\tlastf(X): {f0:.3f}"
            )

            if abs(f1) < self.__y_precision:
                self._log("Minimal Let Found - Convergence")
                return f_calls, x1

            if f1 == f0:
                if out_of_offset_loop:
                    self._log(f"Let approached Nonsense {f1}")
                    return f_calls, None
                x1 += offset * 4
                f1 = self.__f(x1)
                f_calls += 1
                continue

            out_of_offset_loop = True

            if abs(x1 - x0) < self.__x_precision:
                self._log("Minimal Let Found - Convergence")
                return f_calls, x1

            step = f1 * (x1 - x0) / (f1 - f0)
            step = max(-30, min(step, 30))
            x2 = x1 - step
            x0, f0 = (x0, f0) if abs(f0) < abs(f1) else (x1, f1)
            x1, f1 = x2, self.__f(x2)
            f_calls += 1

        return f_calls, None
