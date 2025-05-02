"""
Module with LetFinder a Level 1 simulation responsible for calculating the minimal Let for a fault given some parameters.
"""

from ..simconfig.simulationConfig import sim_config
from ..circuit.components import LET
from .rootSearch.falsePosition import FalsePosition
from typing import Callable
# TODO: fix annotation
# from ..variability.predictionServer import PredictionServer


class LetFinder:
    """
    Responsible for finding the minimal LET value from a faulted node to an output.
    """

    def __init__(
            self,
            predictor = None, #PredictionServer
            report: bool = False):
        """
        Constructor.

        Args:
            report (bool): Whether or not the run will report to terminal with prints.
        """
        self.predictor = predictor
        self.__report = report
        self.__upper_bound: float = 300
        self.__simulations: int = 0

    @property
    def report(self):
        return self.__report

    @report.setter
    def report(self, value: bool):
        self.__report = value

    def __fault_inclination(self, node_name: str, vdd: float, let: LET) -> str:
        """
        Returns the fault inclination on the given node.

        Args:
            node_name (str): Relevant node.
            vdd (float): Vdd of the simulation.
            let (LET): Let of the simulation.

        Returns:
            str: A string representing the inclination, either 'rise' or 'fall'
        """
        self.__simulations += 1
        with sim_config.runner.SET(let, 0):
            min_ten, max_ten = sim_config.runner.run_nodes_value([node_name])[node_name]
        if (max_ten - min_ten) > 0.1 * vdd:
            raise RuntimeError(
                f"Max and Min vdd have too much variation max: {max_ten} min: {min_ten}"
            )
        return "rise" if max_ten < 0.5 * vdd else "fall"

    def __is_let_validity(self, vdd: float, let: LET) -> tuple:
        """
        Verifies the validity of the Let, if in this configuration a fault in the node will have an effect on the output.

        Args:
            vdd (float): Vdd of the simulation.
            let (LET): Let being validated.

        Returns:
            bool: If the Fault configuration is valid.
        """
        node_inclination, output_inclination = let.orient

        # Checks if the fault is logically masked
        lower_tolerance: float = 0.2
        upper_tolerance: float = 0.8

        self.__simulations += 1
        node_peak, output_peak = sim_config.runner.run_SET(let, self.__upper_bound)

        if self.__report:
            print(
                f"masking\tnode: {node_peak:.3f} ({int(100*node_peak/vdd)}%)\t output: {output_peak:.3f}"
            )
        if (
            (output_inclination == "rise" and output_peak < vdd * lower_tolerance)
            or (output_inclination == "fall" and output_peak > vdd * upper_tolerance)
            or (node_inclination == "rise" and node_peak < vdd * lower_tolerance)
            or (node_inclination == "fall" and node_peak > vdd * upper_tolerance)
        ):
            if self.__report:
                print("Invalid Let - Masked Fault\n")
            return False

        # Greater then 10*vdd, weird stuff
        if abs(node_peak / vdd) > 10:
            print(f"Let too great {node_peak/vdd} times! {let} {self.debug_signals}\n")
            return False

        return True

    def __root_function(self, let, target: float = sim_config.vdd / 2) -> Callable:

        def f(current) -> float:
            self.__simulations += 1
            _, peak_tension = sim_config.runner.run_SET(let, current)
            return peak_tension - target

        return f

    def minimal_LET(
        self, let: LET, input_signals: list, safe: bool = False, vars: dict = None
    ) -> tuple:
        """
        Returns the minimal current of a modeled Set to propagate a fault from the node to the output.

        Args:
            let (LET): Let modeled including node and output.
            input_signals (list): Logical value of each input.
            safe (bool): Whether the Let is already known to be valid.
            var (dict, optional): Dict containing variability

        Returns:
            tuple: A tuple containing the simulation number and the current found, if any.
        """
        self.__simulations = 0
        vdd: float = sim_config.vdd
        inputs: list = sim_config.circuit.inputs

        # Sets the input signals
        self.debug_signals = input_signals
        for i in range(len(inputs)):
            inputs[i].signal = input_signals[i]

        with sim_config.runner.Inputs(inputs, vdd):

            # Figures the inclination of the simulation
            if let.orient[0] is None or not safe:
                let.orient[0] = self.__fault_inclination(let.node_name, vdd, let)

            if let.orient[1] is None or not safe:
                let.orient[1] = self.__fault_inclination(let.output_name, vdd, let)

            # debugging report

            if self.__report:
                print(
                    "Starting a LET finding job\n"
                    + f"node: {let.node_name}\toutput: {let.output_name}\n"
                    + f"vdd: {vdd}\tsafe: {safe}\n"
                    + f"inc1: {let.orient[0]}\tinc2: {let.orient[1]}\n"
                    + f"input vector: {' '.join([inp.name+':'+str(inp.signal) for inp in inputs])}"
                )

            # Checks if the Let configuration is valid
            if not safe:
                if not self.__is_let_validity(vdd, let):
                    let.current = None
                    return self.__simulations, None

            f: Callable = self.__root_function(let)
            function_increases: bool = let.orient[1] == "rise"

            guess: float = None
            margin: float = None
            if self.predictor is not None and vars is not None:
                guess = self.predictor.request_prediction(
                    let.identity, tuple(vars.values())
                )
                margin = 5
            if guess is None:
                guess = 150
                margin = 50
            root_finder = FalsePosition(
                f,
                guess - margin,
                guess + margin,
                function_increases,
                report=self.__report,
            )

            if self.__report:
                print(f"f_calls={self.__simulations}")

            current = root_finder.root()
            if current is None:
                return self.__simulations, None

            if self.__report:
                print(f"f_calls={self.__simulations}")

            let.current = current
            if current is not None:
                let.append(input_signals)

            return self.__simulations, current


if __name__ == "__main__":

    from ..circuit.circuit import Circuito
    from ..spiceInterface.spiceRunner import NGSpiceRunner, HSpiceRunner
    from ..utils.math import InDir
    from os import path

    sim_config.runner_type = HSpiceRunner
    hspice_is_working = not sim_config.runner.test_spice()

    with InDir("debug"):

        print("Testing LET finder...")

        print("\tTesting Finding Current of safe Let...")
        if hspice_is_working:
            inv = Circuito("radhardinv").from_json()
            sim_config.circuit = inv
            sim_config.vdd = 0.7
            valid_input = [0]
            target = 162.7
            let = LET(target, 0.7, "ina", "sout", ["fall", "rise"], valid_input)
            measured = LetFinder(report=False).minimal_LET(let, valid_input, safe=True)[
                1
            ]
            assert (
                abs(measured - target) <= 10e-1
            ), f"LET FINDING FAILED simulated:{measured} expected:{target}"

        sim_config.runner_type = NGSpiceRunner
        sim_config.vdd = 0.9
        nand = Circuito("nand").from_json()
        sim_config.circuit = nand

        valid_input = [1, 1]
        target = 59.7290039062
        let = LET(target, 0.9, "g1", "g1", [None, None], valid_input)
        _, measured = LetFinder(report=False).minimal_LET(let, valid_input, safe=True)
        assert (
            abs(measured - target) <= 10e-1
        ), f"LET FINDING FAILED simulated:{measured} expected:{target}"

        print("\tTesting Finding Current of valid unsafe Let...")
        sim_config.circuit = nand
        valid_input = [1, 1]
        # target = 140.625
        target = 115.2
        unsafe_valid_let = LET(target, 0.9, "i1", "g1", [None, None], valid_input)
        measured = LetFinder(report=False).minimal_LET(
            unsafe_valid_let, valid_input, safe=False
        )[1]
        assert (
            abs(measured - target) < 1
        ), f"LET FINDING FAILED simulated:{measured} expected:{target}"

        print("LET Finder OK")
