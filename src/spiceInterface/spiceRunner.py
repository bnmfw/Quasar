"""
Spice Runner.
This is the only class allowed to call spice.
This is the only class that knows Spice File Manager
"""

from .spiceFileManager import SpiceFileManager
from ..circuit.components import LET
from ..simconfig.simulationConfig import sim_config
from ..utils.matematica import InDir
from os import path, system
from typing import Callable
from abc import ABC


class SpiceRunner(ABC):
    """
    Responsible for running spice. Used as a Interface for spice to the rest of the system.
    """

    # TODO This is a huge problem, this variable is a class variable not a object variable
    # I want you to be able to call with SpiceRunner().Vdd(0.5) for example but for that the Vdd context manager
    # Must know path_to_folder of the SpiceRunner instance, wich seems to be very hard to do
    file_manager = None

    def __init__(
        self, spice_run_line: Callable, path_to_folder: str = "project"
    ) -> None:
        """
        Constructor

        Args:
            spice_run_line (Callable): a function that gets a filename and returns the run spice file
            path_to_folder (str): relative path into the folder that contain spice files.
        """
        self.path_to_folder = path_to_folder
        self.spice_run_line: Callable = spice_run_line
        SpiceRunner.file_manager = SpiceFileManager(path_to_folder=path_to_folder)
        self.file_manager = SpiceRunner.file_manager

    class Monte_Carlo:
        """
        Context Mangers that sets the number of MC simulations.
        """

        def __init__(self, num_testes):
            self.num = num_testes

        def __enter__(self):
            SpiceRunner.file_manager.set_monte_carlo(self.num)

        def __exit__(self, type, value, traceback):
            SpiceRunner.file_manager.set_monte_carlo(0)

    class SET:
        """
        Context Mangers that sets the number a single fault.
        """

        def __init__(self, let: LET, current: float = None):
            self.let = let
            if current == None:
                self.current = let.current
            else:
                self.current = current

        def __enter__(self):
            SpiceRunner.file_manager.set_pulse(self.let, self.current)
            SpiceRunner.file_manager.measure_pulse(
                self.let.node_name, self.let.output_name
            )

        def __exit__(self, type, value, traceback):
            pass
            # SpiceRunner.file_manager.set_pulse(self.let, 0)

    class Vss:
        """
        Context Manager that sets the vss of the simulation.
        """

        def __init__(self, vss: float):
            self.vss = vss

        def __enter__(self):
            SpiceRunner.file_manager.set_vss(self.vss)

        def __exit__(self, type, value, traceback):
            pass

    class Vdd:
        """
        Context Manager that sets the vdd of the simulation.
        """

        def __init__(self, vdd: float):
            self.vdd = vdd

        def __enter__(self):
            SpiceRunner.file_manager.set_vdd(self.vdd)

        def __exit__(self, type, value, traceback):
            pass

    class Inputs:
        """
        Context Mangers that sets the input signals of the simulation.
        """

        def __init__(self, inputs: list, vdd: float, vss: float = 0):
            """
            Constructor.

                inputs (list[int]): Input logical values, either 0 or 1.
                vdd (float): Input vdd.
                vdd (float): Input vss.
            """
            self.vdd = vdd
            self.vss = vss
            self.inputs = {}
            for entrada in inputs:
                self.inputs[entrada.name] = entrada.signal

        def __enter__(self):
            SpiceRunner.file_manager.set_signals(self.inputs, self.vdd, self.vss)

        def __exit__(self, type, value, traceback):
            pass

    def _run_spice(self, labels: list = None) -> None:
        """
        Runs spice and dumps labels into output.txt.

        Args:
            filename (str): Name of the file.
            labels (list[str]): labels to be dumped
        """
        if labels is None:
            labels = []
        filename = sim_config.circuit.file
        f = "\|"
        command = f"cd {path.join(self.path_to_folder,'circuits',filename.replace('.cir',''))} ;"
        command += self.spice_run_line(filename)
        labels += ["Error", "error"]
        command += f'| grep "{f.join(labels)}" '
        command += f"> {path.join('..','..','output.txt')}"
        sim_config.update()
        system(command)

    def log_error(self, filename: str) -> None:
        """
        Runs spice and dumps the full report into error_log.txt.

        Args:
            filename (str): Name of the file.
        """
        command = f"cd {path.join(self.path_to_folder,'circuits',filename.replace('.cir',''))} ;"
        command += self.spice_run_line(filename)
        command += f"> {path.join('..','..','error_log.txt')}"
        system(command)

    def default(self, vdd: float) -> None:
        """
        Sets circuit to default configuration, includind vdd, no fault and no MC.

        Args:
            vdd (float): Standard vdd of the simulation.
        """
        self.file_manager.set_vdd(vdd)
        self.file_manager.set_vss(0)
        self.file_manager.set_pulse(LET(0, vdd, "none", "none", [None, None]))
        self.file_manager.set_monte_carlo(0)

    def get_nodes(self, circ_name: str, tension_sources: list = None, inputs: list = None) -> set:
        """
        Parse a <circut_name>.cir file and gets all nodes connected to transistor devices.

        Args:
            curcuit_name (str): name of the circuit to be parsed.
            tension_sources (list[str]): Nodes that should be ignored.
            inputs (list[str]): List of circuit input names.

        Returns:
            set: The label of all nodes.
        """
        return SpiceRunner.file_manager.get_nodes(circ_name, tension_sources, inputs)

    def run_delay(self, input_name: str, output_name: str, inputs: list) -> float:
        """
        Returns the delay of shortest path from a input to and output.

        Args:
            input_name (str): Name of the input node from where the delay is propagated.
            output_name (str): Name of the output node where the delay propagates to.
            inputs (list[Signal_Input]): A list of Signal_Input objects.

        Returns:
            float: The delay of shortest path from the input to the output.
        """

        # Set the signals to be simualted
        SpiceRunner.file_manager.measure_delay(input_name, output_name, sim_config.vdd)
        SpiceRunner.file_manager.set_signals(
            {input.name: input.signal for input in inputs}, sim_config.vdd
        )
        # Runs the simulation in the respective folder
        self._run_spice(["atraso_rr", "atraso_rf", "atraso_fr", "atraso_ff"])
        # Gets and returns the results
        delay = SpiceRunner.file_manager.get_delay()
        return delay

    def run_SET(self, let: LET, current: float = None) -> tuple:
        """
        Returns the peak voltage output for a given let.

        Args:
            let (LET): let simulated.
            current (float): current of the fault. If left as None let.current will be used.

        Returns:
            tuple: A tuple containing the peak tension at the node where the fault originated and output.
        """
        # Sets the SET
        with self.SET(let, current):
            # Runs the simulation
            self._run_spice(["minout", "maxout", "minnod", "maxnod"])
            # Gets the peak tensions in the node and output
            peak_node = SpiceRunner.file_manager.get_peak_tension(
                let.orientacao[0], True
            )
            peak_output = SpiceRunner.file_manager.get_peak_tension(let.orientacao[1])
        return (peak_node, peak_output)

    def run_pulse_width(self, let: LET, current: float = None) -> float:
        """
        Returns the pulse width of the propagated fault.

        Args:
            let (LET): Let to be simulated.
            current (float): current to be simulated. If None then let.current will be used.

        Returns:
            float: Fault width at output.
        """
        with self.SET(let, current):
            SpiceRunner.file_manager.measure_pulse_width(let)
            self._run_spice(["larg"])
            output = SpiceRunner.file_manager.get_output()

        try:
            if output["larg"].value == None:
                return None

            return abs(output["larg"].value)
        except KeyError:
            return None

    def run_nodes_value(self, nodes: list) -> dict:
        """
        Runs the standard circuit and retrieves all the nodes min and max tensions

        Args:
            vdd (float): Vdd of the simulation.
            nodes (list[str]): A list of node names to be measured.

        Returns:
            dict: a dict in the form {node: (min_tension, max_tension)}
        """
        measure_labels = [f"max{node}" for node in nodes] + [
            f"min{node}" for node in nodes
        ]
        self.file_manager.measure_nodes(nodes)
        self._run_spice(measure_labels)
        return self.file_manager.get_nodes_tension(nodes)

    def run_MC_var(self, sim_num: int, distributions: list) -> dict:
        """
        Returns the MC variability points.

        Args:
            circuit_name (str): Name of the circuit.
            sim_num (int): Number of simulations.
            dist (list[DistRules]): A list of different distribution templates

        Returns:
            dict: MC variability instances.
        """
        params = []
        model_vars = []
        for dist in distributions:
            model_vars.append((dist.model, dist.var))
            params.append(sim_config.model_manager[dist.model][dist.var])
            sim_config.model_manager[dist.model][
                dist.var
            ] = f"gauss({dist.mean}, {dist.std_dev}, {dist.sigmas})"

        with self.Monte_Carlo(sim_num):
            self._run_spice()

        for dist, param in zip(distributions, params):
            sim_config.model_manager[dist.model][dist.var] = param

        return SpiceRunner.file_manager.get_mc_instances(
            sim_config.circuit.name, model_vars
        )


class NGSpiceRunner(SpiceRunner):
    def __init__(self, path_to_folder: str = "project") -> None:
        f = lambda filename: f" ngspice -b < {filename} 2>&1 "
        super().__init__(f, path_to_folder)


class HSpiceRunner(SpiceRunner):
    def __init__(self, path_to_folder: str = "project") -> None:
        f = lambda filename: f" hspice {filename} "
        super().__init__(f, path_to_folder)
        if self.test_spice():
            raise RuntimeError("HSPICE NOT WORKING!")

    def test_spice(self) -> bool:
        """
        Testes if spice is working. If not will exit as nothing can be done without spice.

        Returns: True if not working
        """
        system(
            f"hspice {path.join('debug','empty.cir')} > {path.join('debug','output.txt')}"
        )
        with open(path.join("debug", "output.txt"), "r") as file:
            for linha in file:
                if "Cannot connect to license server system" in linha:
                    return True
        return False


HSRunner = HSpiceRunner()
sim_config.runner_type = NGSpiceRunner

if __name__ == "__main__":
    print("Testing Spice Runner")
    ptf = path.join("project")
    from ..circuit.circuito import Circuito

    sim_config.runner_type = NGSpiceRunner
    TestManager = SpiceFileManager(path_to_folder=ptf)
    vdd = 0.9
    sim_config.runner.default(vdd)

    with InDir("debug"):
        print("\tTesting node tensions...")
        nand_test = Circuito("nand").from_json()
        sim_config.circuit = nand_test
        for vi, entrada in zip([0, 0], nand_test.inputs):
            entrada.signal = vi
        with sim_config.runner.Vdd(vdd), sim_config.runner.Inputs(
            nand_test.inputs, vdd
        ):
            assert (
                sim_config.runner.run_nodes_value(["i1", "g1"])["i1"][0] - 0.104784
                < 10e-3
            ), "TENSIONS RUN FAILED"

        print("\tTesting circuit parsing...")
        nor_test = Circuito("nor").from_nodes(["a", "b"], ["g1"])
        sim_config.circuit = nor_test
        assert {nodo.name for nodo in nor_test.nodes} == {
            "g1",
            "i1",
            "a",
            "b",
            "ng1",
        }, "CIRCUIT PARSING FAILED"

        print("\tTesting SET simulation with known SET value...")
        nand_test = Circuito("nand").from_json()
        sim_config.circuit = nand_test
        valid_input = [0, 1]
        valid_let = LET(156.25, vdd, "g1", "g1", ["fall", "fall"], valid_input)
        expected_let_value = 0.36585829999999997
        for vi, entrada in zip(valid_input, nand_test.inputs):
            entrada.signal = vi
        with sim_config.runner.Vdd(vdd), sim_config.runner.Inputs(
            nand_test.inputs, vdd
        ):  # , TestRunner.MC_Instance(4.7443, 4.3136):
            peak_node, peak_output = sim_config.runner.run_SET(valid_let)
            assert (
                abs(peak_node - expected_let_value) <= 10e-1
            ), f"SET SIMULATION FAILED simulated: {peak_node} expected: {expected_let_value}"

        print("Spice Runner OK.")
