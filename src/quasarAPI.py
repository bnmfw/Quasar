"""
API module, responsible for acting as an interface to the other files in the package
"""

from .circuit.components import LET
from .circuit.circuito import Circuito
from .circuit.circuitManager import CircuitManager
from .variability.mcManager import MCManager
from .variability.dataAnalysis import DataAnalist
from .variability.distribution.distribution import Distribution
from .utils.arquivos import JManager, CManager
from .letSearch.letFinder import LetFinder
from .spiceInterface.spiceRunner import SpiceRunner
from .simconfig.simulationConfig import sim_config
from .simconfig.transistorModel import Transistor
from .simconfig.faultModel import DoubleExponential
from .utils.matematica import Time
from typing import Callable, Type
from os import path


class API:
    """
    API object, this is the only object of the project the interface should interact with
    """

    def __init__(self) -> None:
        """
        Constructor object
        """
        self.circuit = None

    def set_sim_config(
        self,
        vdd: float,
        colection_time: float,
        track_establishment: float,
        transistor_depth: float,
        spice: Type[SpiceRunner],
        path_to_dir: str,
    ) -> None:
        """
        Sets the simulation configuration

        Args:
            vdd (float): Vdd of the circuit in volts.
            colection_time (float): Messenger's equation collection time constant in pico seconds.
            track_establishment (float): Track_establishment_constant_pico (float): Messenger's equation track establishment contant in pico <unit>.
            transistor_depth (float): Transistor's collection.
            spice (Type[SpiceRunner]): Simulator Runner used.
        """
        sim_config.vdd = vdd
        sim_config.fault_model = DoubleExponential(colection_time, track_establishment)
        sim_config.transistor_model = Transistor(transistor_depth)
        sim_config.runner_type = spice
        sim_config.dump(path_to_folder=path_to_dir)

    def set_circuit(self, circuit: Circuito):
        """
        Sets the simulated circuit

        Args:
            circuit (Circuito): circuit to be simulated.
        """
        self.circuit = circuit
        sim_config.circuit = circuit
        sim_config.model_manager.writeModelFile()
        return self

    def check_circuit(self):
        """
        Checks whether or not a circuit is set. Raises a ValueError if one is not
        """
        if self.circuit is None:
            raise ValueError("Circuit not informed")

    def determine_LETs(
        self,
        delay: bool = False,
        report: bool = False,
        progress_report: Callable = None,
        log_circuit: bool = False,
    ):
        """
        Determines the LETs of the set circuit from scratch

        Args:
            delay (bool, optional): Whether the delay of the circuit is to be taken into consideration. Defaults to False.
            report (bool, optional): Whether work is to be print to terminal. Defaults to False.
            progress_report (Callable, optional): _description_. Defaults to None.
        """
        self.check_circuit()
        with Time():
            CircuitManager(self.circuit, report=report).determine_LETs(
                delay=delay, progress_report=progress_report
            )
        if log_circuit:
            JManager.codify(self.circuit, self.circuit.path_to_circuits)

    def save_let_data(self, path_to_folder: str):
        """
        Saves all the LETs data into a .csv file

        Args:
            path_to_folder (str): Path to folder where the file is to be saved.
        """
        self.check_circuit()
        CManager.write_full_csv(self.circuit, path_to_folder)

    def mc_analysis(
        self,
        n_simu: int,
        distribution: list,
        continue_backup: bool = False,
        delay: bool = False,
        progress_report: Callable = None,
    ):
        """
        Runs a full Monte Carlo analysis of the circuit

        Args:
            n_simu (int): number of MC points
            distribution (list[Distribution]): list of distribution objects.
            continue_backup (bool, optional): Whether the MC work should continue from a backup file. Defaults to False.
            delay (bool, optional): Whether delay should be taken into consideration. Defaults to False.
            progress_report (Callable, optional): _description_. Defaults to None.
        """
        self.check_circuit()
        with Time():
            MCManager(self.circuit).full_mc_analysis(
                n_simu,
                distribution,
                continue_backup=continue_backup,
                delay=delay,
                progress_report=progress_report,
            )
        scatter_data = {
            "PMOS": [],
            "NMOS": [],
            "node": [],
            "output": [],
            "current": [],
            "LETth": [],
            "pulse_in": [],
            "pulse_out": [],
            "input": [],
        }

        with open(
            path.join(self.circuit.path_to_my_dir, f"{self.circuit.name}_mc_LET.csv")
        ) as file:
            for linha in file:
                pmos, nmos, node, output, pulse_in, pulse_out, current, let, *inputs = (
                    linha.split(",")
                )
                scatter_data["PMOS"].append(float(pmos))
                scatter_data["NMOS"].append(float(nmos))
                scatter_data["node"].append(node)
                scatter_data["output"].append(output)
                scatter_data["current"].append(float(current))
                scatter_data["LETth"].append(float(let))
                scatter_data["pulse_in"].append(pulse_in.strip("['").strip("'"))
                scatter_data["pulse_out"].append(pulse_out.strip("']").strip(" '"))
                inputs = (
                    ",".join(inputs)
                    .replace("1, ", "1")
                    .replace("0, ", "0")
                    .replace("[", "")
                    .replace("]", "")
                )
                scatter_data["input"].append(inputs)
        analist = DataAnalist()
        analist.describe(scatter_data, self.circuit.path_to_my_dir)
        analist.quantitative_scatter(
            scatter_data, "PMOS", "NMOS", "LETth", self.circuit.path_to_my_dir, "winter"
        )
        analist.qualitative_scatter(
            scatter_data, "PMOS", "NMOS", "node", self.circuit.path_to_my_dir
        )
        analist.qualitative_scatter(
            scatter_data, "PMOS", "NMOS", "pulse_in", self.circuit.path_to_my_dir
        )
        analist.qualitative_scatter(
            scatter_data, "PMOS", "NMOS", "pulse_out", self.circuit.path_to_my_dir
        )
        analist.qualitative_scatter(
            scatter_data, "PMOS", "NMOS", "input", self.circuit.path_to_my_dir
        )
        analist.count_unique(scatter_data, "pulse_out", self.circuit.path_to_my_dir)

    def find_single_let(
        self,
        node: str,
        output: str,
        logical_input: list,
        pulse_in: str = None,
        pulse_out: str = None,
        pmos_var: float = 4.8108,
        nmos_var: float = 4.372,
        report: bool = True,
    ):
        """
        Finds a single minimal LET given a configuration.

        Args:
            node (str): Name of the node the fault is to be inserted.
            output (str): Name of the output the fault it to be propagated to.
            logical_input (list[bool]): Logical values of the inputs.
            pulse_in (str, optional): Pulse type in strucked node, either "rise" or "fall". Defaults to None.
            pulse_out (str, optional): Pulse type to be measured, either "rise" or "fall". Defaults to None.
            pmos_var (float, optional): Pmos var. Defaults to 4.8108.
            nmos_var (float, optional): Nmos var. Defaults to 4.372.
            report (bool, optional): Whether a report is to be printed. Defaults to True.
        """
        self.check_circuit()
        # with sim_config.runner.MC_Instance(pmos_var, nmos_var):
        target_let = LET(None, sim_config.vdd, node, output, [pulse_in, pulse_out])
        LetFinder(
            self.circuit, path_to_folder=self.circuit.path_to_folder, report=report
        ).minimal_LET(target_let, logical_input, safe=True)


if __name__ == "__main__":

    from utils.matematica import InDir

    print("Testing API...")

    # with InDir("debug"):

    nand: Circuito = Circuito("nor").from_json()
    quasarAPI: API = API().set_circuit(nand, 0.7)
    quasarAPI.find_single_let("g1", "g1", [1, 1], "rise", "rise", 4.8108, 4.3720)

    # fadder: Circuito = Circuito("fadder", "test_circuits", 0.7).from_nodes(["a", "b", "cin"], ["cout", "sum"])
    # xor1: Circuito = Circuito("xorv1", "test_circuits", 0.7).from_json()
    # xor5: Circuito = Circuito("xorv5", "test_circuits", 0.7).from_json()

    # {"na", "nb", "ncin", "gate_p16", "gate_p15", "gate_q16", "gate_q15", "drain_p16", "drain_p15", "drain_q16", "drain_q15", "ncout", "nsum", "a1", "b1", "cin1"}

    # quasarAPI: API = API().set_circuit(xor5, 0.7)

    # print("\tTesting LETth determination...")
    # quasarAPI.determine_LETs(report=True)
    # quasarAPI.save_let_data("test_circuits")

    # quasarAPI.mc_analysis(1000)

    # fadder = Circuito("fadder", "test_circuits", 0.7).from_nodes(["a", "b", "cin"], ["cout", "sum"], {"na", "nb", "ncin", "gate_p16", "gate_p15", "gate_q16", "gate_q15", "drain_p16", "drain_p15", "drain_q16", "drain_q15", "ncout", "nsum", "a1", "b1", "cin1"})
    # fadder = Circuito("fadder", "test_circuits", 0.7).from_json()
    # fadder.nodes.sort(key=lambda e: e.name)
    # quasarAPI = API().set(fadder, 0.7)
    # quasarAPI.analise_mc(1000)
