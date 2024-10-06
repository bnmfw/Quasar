"""
Module with LetFinder a Level 1 simulation responsible for calculating the minimal Let for a fault given some parameters.
"""

from ..simconfig.simulationConfig import sim_config
from ..circuit.components import LET
from .rootSearch.bissection import Bissection
from .rootSearch.secant import Secant
from .rootSearch.hybrid import Hybrid
from .rootSearch.falsePosition import FalsePosition
from typing import Callable


class LetFinder:
    """
    Responsible for finding the minimal LET value from a faulted node to an output.
    """

    def __init__(self, circuit, path_to_folder: str = "project", report: bool = False):
        """
        Constructor.

        Args:
            circuit (Circuit): A Circuit object to have its let found.
            path_to_folder (str): relative path into the folder that contain spice files.
            report (bool): Whether or not the run will report to terminal with prints.
        """
        self.circuito = circuit
        self.__report = report
        self.__upper_bound: float = 300  # Valor maximo considerado da falha
        # 200 é um numero bem razoavel de quanto é uma falha real
        # Pede pro rafael o tga ou tfa ?
        self.__limite_sim: int = 50
        self.__simulations: int = 0

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

    def __verify_let_validity(self, vdd: float, let: LET) -> tuple:
        """
        Verifies the validity of the Let, if in this configuration a fault in the node will have an effect on the output.

        Args:
            vdd (float): Vdd of the simulation.
            let (LET): Let being validated.

        Returns:
            bool: If the Fault configuration is valid.
        """
        node_inclination, output_inclination = let.orientacao

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

    def __find_maximal_current(self, let: LET) -> float:
        """
        Finds the upper limit for the current of the Let.

        Args:
            let (LET): Let to have the upper limit found.

        Returns:
            float: The maximal current for the Let.
        """
        self.__upper_bound = 400

        output_inclination = let.orientacao[1]

        for _ in range(10):
            _, output_peak = sim_config.runner.run_SET(let, self.__upper_bound)

            # Fault effect on the output was found
            if (output_inclination == "rise" and output_peak > sim_config.vdd / 2) or (
                output_inclination == "fall" and output_peak < sim_config.vdd / 2
            ):
                if self.__report:
                    print(f"Upper current bound: ({self.__upper_bound})")
                return self.__upper_bound

            self.__upper_bound += 100

        print("Upper current too big")
        return 800

    def __find_minimal_current(self, let: LET) -> float:
        """
        Finds the lower limit for the current of the Let.

        Args:
            let (LET): Let to have the upper limit found.

        Returns:
            float: The minimal current for the Let.
        """

        # Variables for the minary search of the current
        limite_sup: float = self.__upper_bound
        csup: float = self.__upper_bound
        cinf: float = 0
        current: float = (csup + cinf) / 2

        # Busca binaria para largura de pulso
        diferenca_largura: float = 100
        precisao_largura: float = 0.05e-9

        # Binary search for minimal current
        for _ in range(self.__limite_sim):
            # Encontra a largura minima de pulso pra vencer o delay
            largura = sim_config.runner.run_pulse_width(let, current)
            diferenca_largura: float = (
                None if largura is None else largura - self.circuito.SPdelay
            )

            # checks if minimal width is satisfied
            if (
                diferenca_largura
                and -precisao_largura < diferenca_largura < precisao_largura
            ):
                if self.__report:
                    print(f"PULSO MINIMO ENCONTRADO - PRECISAO SATISFEITA ({current})")
                return current

            if abs(csup - cinf) < 1:
                if self.__report:
                    print(
                        f"PULSO MINIMO ENCONTRADO - DIFERENCA DE BORDAS PEQUENA ({current})"
                    )
                return current
            if diferenca_largura == None:
                cinf = current
            elif diferenca_largura > precisao_largura:
                csup = current
            elif diferenca_largura < -precisao_largura:
                cinf = current
            current = (csup + cinf) / 2

        if self.__report:
            print(f"PULSO MINIMO NAO ENCONTRADO - LIMITE DE SIMULACOES ATINGIDO")
        return None

    def __root_function(self, let, target: float = sim_config.vdd / 2) -> Callable:

        def f(current) -> float:
            self.__simulations += 1
            _, peak_tension = sim_config.runner.run_SET(let, current)
            return peak_tension - target

        return f

    def minimal_LET(
        self,
        let: LET,
        input_signals: list,
        safe: bool = False,
        delay: bool = False,
        lowerth: float = None,
        upperth: float = None,
    ) -> tuple:
        """
        Returns the minimal current of a modeled Set to propagate a fault from the node to the output.

        Args:
            let (LET): Let modeled including node and output.
            input_signals (list): Logical value of each input.
            safe (bool): Whether the Let is already known to be valid.
            delay (bool): Whether the delay of the circuit will be taken into consideration.
            lowerth (float, optional): The lowest value the current can get. Defaults to None.
            upperth (float, optional): The highest value the current can get. Defaults to None.

        Returns:
            tuple: A tuple containing the simulation number and the current found, if any.
        """
        vdd: float = sim_config.vdd
        inputs: list = self.circuito.inputs

        # Sets the input signals
        self.debug_signals = input_signals
        for i in range(len(inputs)):
            inputs[i].signal = input_signals[i]

        with sim_config.runner.Inputs(inputs, vdd):

            # Figures the inclination of the simulation
            if let.orientacao[0] is None or not safe:
                let.orientacao[0] = self.__fault_inclination(let.node_name, vdd, let)

            if let.orientacao[1] is None or not safe:
                let.orientacao[1] = self.__fault_inclination(let.output_name, vdd, let)

            # debugging report

            if self.__report:
                print(
                    "Starting a LET finding job\n"
                    + f"node: {let.node_name}\toutput: {let.output_name}\n"
                    + f"vdd: {vdd}\tsafe: {safe}\n"
                    + f"inc1: {let.orientacao[0]}\tinc2: {let.orientacao[1]}\n"
                    + f"input vector: {' '.join([inp.name+':'+str(inp.signal) for inp in inputs])}"
                )

            # Checks if the Let configuration is valid
            if not safe:
                valid_let = self.__verify_let_validity(vdd, let)
                if not valid_let:
                    let.current = None
                    return self.__simulations, None

            # Binary search variables
            # cinf: float = 0 if not delay else self.__find_minimal_current(let)

            f: Callable = self.__root_function(let)
            lower: float = 0
            upper: float = self.__upper_bound
            function_increases: bool = let.orientacao[1] == "rise"

            # root_finder = Bissection(f, lower, upper, report=self.__report)
            # root_finder = Secant(f, 110, report=self.__report)
            # root_finder = Hybrid(f, 150, function_increases, vdd/2, -vdd/2, report=self.__report)
            guess: float = 150
            root_finder = FalsePosition(f, guess-50, guess+50, function_increases, report=self.__report)

            if self.__report:
                print(f"f_calls={self.__simulations}")

            current = root_finder.root()
            if current is None:
                raise RuntimeError("Current not found")
            
            if self.__report:
                print(f"f_calls={self.__simulations}")

            let.current = current
            if current is not None:
                let.append(input_signals)

            return self.__simulations, current

if __name__ == "__main__":

    from ..circuit.circuito import Circuito
    from ..spiceInterface.spiceRunner import NGSpiceRunner, HSpiceRunner
    from ..utils.matematica import InDir
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
            measured = LetFinder(inv, report=False).minimal_LET(
                let, valid_input, safe=True
            )[1]
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
        measured = LetFinder(nand, report=False).minimal_LET(
            let, valid_input, safe=True
        )[1]
        assert (
            abs(measured - target) <= 10e-1
        ), f"LET FINDING FAILED simulated:{measured} expected:{target}"

        print("\tTesting Finding Current of valid unsafe Let...")
        sim_config.circuit = nand
        valid_input = [1, 1]
        # target = 140.625
        target = 115.2
        unsafe_valid_let = LET(target, 0.9, "i1", "g1", [None, None], valid_input)
        measured = LetFinder(nand, report=False).minimal_LET(
            unsafe_valid_let, valid_input, safe=False
        )[1]
        assert (
            abs(measured - target) < 1
        ), f"LET FINDING FAILED simulated:{measured} expected:{target}"

        print("LET Finder OK")
