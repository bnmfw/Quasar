from typing import Callable
from .rootSearch import RootSearch
from .secant import Secant

class Hybrid(RootSearch):
    def __init__(self, f: Callable,
                 root_guess: float,
                 increasing: bool,
                 max_y: float,
                 min_y: float,
                 x_precision: float = 0.1, 
                 y_precision: float = 0.001,
                 report: bool = False, 
                 iteration_limit: int = 50) -> None:
        super().__init__(f, report)
        self.__f: Callable = f
        self.__guess: float = root_guess
        self.__increasing: bool = increasing
        self.__max_y: float = max_y
        self.__min_y: float = min_y
        self.__x_precision: float = x_precision
        self.__y_precision: float = y_precision
        self.__report: bool = report
        self.__iteration_limit: int = iteration_limit

    def linear_zone(self, y_value: float) -> bool:
        """
        Determines if a point in in the linear zone

        Args:
            y_value (float): y value of the point
        """
        tolerance = (self.__max_y - self.__min_y)/8
        return (self.__min_y + tolerance < y_value < self.__max_y - tolerance)

    def get_to_linear(self) -> float:
        """
        Does bisection until it has a point in the linear zone

        Returns:
            float: The point in the linear zone
        """
        f_calls = 0
        x0: float = self.__guess
        f0: float = self.__f(x0)
        f_calls += 1

        # f0 happens to be in linear zone
        if self.linear_zone(f0):
            return f_calls, x0, f0
        
        direction = 1 if (self.__increasing and f0 < 0) or (not self.__increasing and f0 > 0) else -1
        step_up = x0 * 0.8 * direction
        x1: float = max(x0 + step_up, 0)
        f1: float = self.__f(x1)
        f_calls += 1

        self._log(f"Starting Border Search")
        # Guarantees oposite borders
        for i in range(self.__iteration_limit):
            
            
            self._log(f"{i}\tfixed border: x={x0:.1f} y={f0:.3f}\tmoving border: x={x1:.1f} y={f1:.3f}")
            
            # f1 happens to be in linear zone
            if self.linear_zone(f1):
                return f_calls, x1, f1

            # x1 and x0 in oposite sides
            if f1/f0 < 0:
                break

            x1 += step_up
            x1 = max(0, x1)
            f1 = self.__f(x1)
            f_calls += 1
        
        upper, f_out_up, lower, f_out_lw = (x0, f0, x1, f1) if x0 > x1 else (x1, f1, x0, f0)

        self._log(f"Starting Binary Search for Linear Zone")
        # binary search
        for i in range(self.__iteration_limit - f_calls):

            x = (lower+upper)/2
            y = self.__f(x)
            f_calls += 1
            self._log(f"{i}\tcurrent: {x:.1f}\tpeak_tension: {y:.3f}\tbottom: {lower:.1f}\ttop: {upper:.1f}")

            if self.linear_zone(y):
                return f_calls, x, y
            
            if f_out_up/f_out_lw > 0:
                raise RuntimeError(f"Both bounds of binary search in the same side {f_out_up} and {f_out_lw}")
            if f_out_up/y > 0:
                f_out_up = y
                upper = x
            elif f_out_lw/y > 0:
                f_out_lw = y
                lower = x
        
        return f_calls, None, None


    def root(self) -> float:
        """
        Finds the approximation for the root
        
        Returns:
            float: the root
        """
        f_calls, x0, fx0 = self.get_to_linear()
        
        if x0 is None: return f_calls, None

        if abs(fx0) < self.__y_precision:
            return f_calls, x0
        
        self._log("Start Secant Root Finding")
        secant_finder = Secant(self.__f, x0, self.__increasing, fx0,
                               self.__x_precision, self.__y_precision,
                               report=self.__report)
        
        
        n_sim, ret = secant_finder.root()
        f_calls += n_sim
        return f_calls, ret