from typing import Callable
from .rootSearch import RootSearch

class Bissection(RootSearch):
    def __init__(self, f: Callable, 
                 lower_bound: float, 
                 upper_bound: float,
                 x_precision: float = 0.1,
                 y_precision: float = 0.001, 
                 report: bool = False, 
                 iteration_limit: int = 50) -> None:
        """
        Constructor

        Args:
            f (Callable): function to be minimized
            lower_bound (float): lower bound of the binary search
            upper_bound (float): uppder bound of the binary search
        """
        self.__f: Callable = f
        self.__lower_bound: float = lower_bound
        self.__upper_bound: float = upper_bound
        self.__x_precision: float = x_precision
        self.__y_precision: float = y_precision
        self.__report: bool = report
        self.__iteration_limit: int = iteration_limit

    def root(self) -> float:
        lower = self.__lower_bound
        upper = self.__upper_bound
        f_calls = 0
        step_up = 100

        f_out_up = self.__f(upper)
        f_out_lw = self.__f(lower)
        f_calls += 2

        # Guarantees the upper and lower bound are in different sides
        it = 0
        while f_out_up/f_out_lw > 0:
            self.__upper_bound += step_up
            step_up += 100
            upper = self.__upper_bound
            f_out_up = self.__f(upper)
            f_calls += 1
            it += 1
            if it > 5:
                raise RuntimeError(f"Current higher than {upper}")

        # Actual binary search
        for i in range(self.__iteration_limit):
            
            f_in = float((lower + upper)/2)

            # Function call
            f_out = self.__f(f_in)
            f_calls += 1
            if self.__report:
                print(f"{i}\tcurrent: {f_in:.1f}\tpeak_tension: {f_out:.3f}\tbottom: {lower:.1f}\ttop: {upper:.1f}")

            # Precision satisfied
            if abs(f_out) < self.__y_precision:
                    if self.__report: print("Minimal Let Found - Convergence\n")
                    return f_calls, f_in

            # Upper and Lower convergence
            if abs(upper-lower) < self.__x_precision:
                # To the lower bound
                if f_in <= self.__lower_bound+1:
                    if self.__report: print("Minimal Let NOT Found - Lower Divergence\n")
                    return f_calls, None
                
                # To the upper bound (Increase)
                elif f_in >= self.__upper_bound-1:
                    if self.__report: print("Upper Divergence - Upper Bound Increased\n")
                    self.__upper_bound += step_up
                    step_up += 100
                    upper = self.__upper_bound
            
            if f_out_up/f_out_lw > 0:
                raise RuntimeError(f"Both bounds of binary search in the same side {f_out_up} and {f_out_lw}")
            if f_out_up/f_out > 0:
                f_out_up = f_out
                upper = f_in
            elif f_out_lw/f_out > 0:
                f_out_lw = f_out
                lower = f_in
        
        if self.__report: print("Minimal Let NOT Found - Maximum Simulation Number Reached\n")
        return f_calls, None