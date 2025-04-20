"""
Circuit level simulation (Lvl 2) manager.
"""

from ..utils.math import all_vector_n_bits, InDir
from .components import *
from ..letSearch.letFinder import LetFinder
from ..utils.parallel import ProcessMaster
from ..variability.predictionServer import PredictionServer
from .components import LET, Node
from .circuit import Circuito
from .graph import LogicSimulationError
from ..simconfig.simulationConfig import sim_config

relatorio = False


class CircuitManager:
    """
    Circuit level simulations manager.
    """

    def __init__(self, predictor: PredictionServer = None, report: bool = False):
        """
        Constructor.

        Args:
            report (bool, optional): Whether or not print reports will be done.
        """
        self.report: bool = report
        self.min_let_predictor = (
            PredictionServer(sim_config.circuit.path_to_my_dir)
            if predictor is None
            else predictor
        )
        self.let_manager = LetFinder(report=report, predictor=self.min_let_predictor)

    def __all_possible_LETs(self, nodes: list, outputs: list, inputs: list) -> list:
        """
        Recieves a list of nodes, outputs and the number of inputs and returns all possible lets.

        Args:
            nodes (list[Node]): List of Node objects (Includes output nodes).
            outputs (list[Node]): List of Node objects interpreted as outputs.
            inputs (list): List of circuit inputs.

        Returns:
            list: A list of all possible lets.
        """
        try:
            # Generates all valid lets from the circuit graph model
            f = lambda l: list(map(lambda n: n.name, l))
            lets = sim_config.circuit.graph.generate_valid_let_configs(
                f(nodes), f(outputs), f(inputs), sim_config.circuit.get_node
            )
        except LogicSimulationError:
            lets = [
                [node, output, signals, None, None]
                for node in nodes
                for output in outputs
                for signals in all_vector_n_bits(len(inputs))
            ]

        # Enumerates lets
        return lets

    def update_LETs(
        self, delay: bool = False, only_lowest: bool = False, var: dict = None
    ) -> int:
        """
        Updates the minimal LETs of the circuit.

        Args:
            delay (bool, optional): Whether the delay will be considered in the simulations. Defaults to False.
            only_lowest (bool, optional): Whether LETs higher than the lowest should be ignored. Deafults to False
            var (dict, optional): Dict containing variability

        Returns:
            int: The number of simulations done
        """
        sim_num: int = 0
        sim_config.circuit.LETth = None
        ##### BUSCA DO LETs DO CIRCUITO #####
        nodo: Node
        for nodo in sim_config.circuit.nodes:
            let: LET
            for let in nodo.LETs:

                sim, current = self.let_manager.minimal_LET(
                    let, let.input_states[0], safe=True, vars=var
                )

                let.current = current
                sim_num += sim

                if let.current is None:
                    continue

                if var is not None:
                    self.min_let_predictor.submit_data(
                        let.identity, tuple(var.values()), current
                    )

                if sim_config.circuit.LETth is None or let < sim_config.circuit.LETth:
                    sim_config.circuit.LETth = let
        return sim_num

    def run_let_job(
        self,
        _,
        node: Node,
        output: Node,
        input_signals: list,
        in_dir: str = None,
        out_dir: str = None,
        delay: bool = False,
    ) -> tuple:
        """
        Runs a single let job a returns the same let with its minimal current.
        Method meant to be run cuncurrently.

        Args:
            _: Important for cuncurrency, dont you dare take it out.
            node (Node): Node object where fault originates.
            output (Node): Output where fault propagates to.
            input_signals (list): Signal values of inputs.
            in_dir (str): direction of fault. Either 'rise' or 'fall'.
            out_dir (str): direction of propagated fault at output. Either 'rise' or 'fall'.
            delay (bool): Whether or not delay will be taken into consideration.

        Returns:
            tuple: A tuple with the minimal let and the input signals run.
        """
        target_let = LET(
            None, sim_config.vdd, node.name, output.name, [in_dir, out_dir]
        )
        sim_num, _ = self.let_manager.minimal_LET(target_let, input_signals, safe=True)
        return (target_let, input_signals, sim_num)

    def determine_LETs(self, delay: bool = False, progress_report=None):
        """
        Determines all the minimal LETs of the circuit from all possible configurations.

        Args:
            delay (bool): Whether or not delay will be taken into consideration.
            progress_report (Callable): Optional function that progress can be reported to.
        """
        if sim_config.circuit.loaded:
            # Gathers all jobs
            jobs = []
            for node in sim_config.circuit.nodes:
                for let in node.LETs:
                    for input_config in let.input_states:
                        jobs.append(
                            [
                                node,
                                sim_config.circuit.get_node(let.output_name),
                                input_config,
                                let.orient[0],
                                let.orient[1],
                            ]
                        )

        else:
            sim_config.circuit.loaded = True
            jobs = self.__all_possible_LETs(
                sim_config.circuit.nodes,
                sim_config.circuit.outputs,
                sim_config.circuit.inputs,
            )

        for i, job in enumerate(jobs):
            job.insert(0, i)

        for node in sim_config.circuit.nodes:
            node.LETs = []

        if self.report:
            [print(j) for j in jobs]
            print()

        with self.min_let_predictor:
            manager = ProcessMaster(
                self.run_let_job,
                jobs,
                work_dir=sim_config.circuit.path_to_my_dir,
                progress_report=progress_report,
            )
            error = manager.work((delay,))
            if error:

                print(
                    "\n\nAn error was raised during let root search, here is the search in detail:\n"
                )

                problem_job, _ = error
                self.let_manager.report = True
                self.run_let_job(*problem_job)

        lets = manager.return_done()

        # for let in lets:
        #     print(let)

        sim_num_acc = 0
        let: LET
        for let, _, sim_num in lets:
            sim_num_acc += sim_num

            # Ignora currents invalidas
            if let.current is None:
                continue

            node = sim_config.circuit.get_node(let.node_name)

            # Updates circuits LETth
            if sim_config.circuit.LETth is None or let < sim_config.circuit.LETth:
                sim_config.circuit.LETth = let

            node.add_let(let)

        print(f"total simulations: {sim_num_acc}")


if __name__ == "__main__":
    from os import path
    from ..spiceInterface.spiceRunner import NGSpiceRunner
    from ..utils.math import compare_fault_config_lists

    sim_config.runner_type = NGSpiceRunner
    print("Testing Circuit Manager...")

    from .circuit import Circuito

    # print("\tTesting update of minimal LETs...")
    # nand_test = Circuito("nand", ptf, 0.7).from_json()
    # manager = CircuitManager(nand_test, report=False)
    # manager.update_LETs()

    print("\tTesting determining minimal LETs...")
    with InDir("debug"):
        nor_test = Circuito("nor").from_nodes(["a", "b"], ["g1"])
        sim_config.circuit = nor_test
        manager = CircuitManager(report=False)
        manager.determine_LETs()
        with open(path.join("project", "circuits", "nor", "Raw_data.csv"), "r") as file:
            data = sorted(list(map(lambda e: e.split(","), file.read().split()[1:])))
            for line in data:
                line[4] = int(float(line[4]))
            ans = [
                ["g1", "g1", "fall", "fall", 65, "00"],
                ["g1", "g1", "rise", "rise", 112, "01"],
                ["g1", "g1", "rise", "rise", 113, "10"],
                ["g1", "g1", "rise", "rise", 223, "11"],
                ["i1", "g1", "rise", "rise", 113, "10"],
            ]
            compare_fault_config_lists(data, ans), "LET DETERMINING FAILED"

    print("Circuit Manager OK.")
