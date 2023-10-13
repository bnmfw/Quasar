"""
Backend module, responsible for acting as an interface to the other files in the package
"""
from .components import LET
from .circuito import Circuito
from .circuitManager import CircuitManager
from .mcManager import MCManager
from .arquivos import JManager, CManager
from .letFinder import LetFinder
from .spiceInterface import SpiceRunner
from .dataAnalysis import DataAnalist
from collections.abc import Callable

class Backend:
    """
    Backend object, this is the only object of the project the interface should interact with
    """
    def __init__(self) -> None:
        """
        Constructor object
        """
        self.circuit = None
        self.vdd = None

    def set_circuit(self, circuit: Circuito, vdd: float):
        """
        Sets the simulated circuit

        Args:
            circuit (Circuito): circuit to be simulated.
            vdd (float): vdd of the simulation
        """
        self.circuit = circuit
        self.vdd = vdd
        return self

    def check_circuit(self):
        """
        Checks whether or not a circuit is set. Raises a ValueError if one is not
        """
        if self.circuit is None:
            raise ValueError("Circuit not informed")

    def determine_LETs(self, delay: bool = False, report: bool = False, progress_report: Callable = None):
        """
        Determines the LETs of the set circuit from scratch

        Args:
            delay (bool, optional): Whether the delay of the circuit is to be taken into consideration. Defaults to False.
            report (bool, optional): Whether work is to be print to terminal. Defaults to False.
            progress_report (Callable, optional): _description_. Defaults to None.
        """
        self.check_circuit()
        CircuitManager(self.circuit, report=report).determine_LETs(delay=delay, progress_report=progress_report)
        JManager.codify(self.circuit, self.circuit.path_to_circuits)
    
    def update_lets(self, delay: bool = False, report: bool = False):
        """
        Updates the LETs of a circuit. For this to be run LETs must already have been determined.

        Args:
            delay (bool, optional): Whether the delay of the circuit is to be taken into consideration. Defaults to False.
            report (bool, optional): Whether work is to be print to terminal. Defaults to False.
        """
        self.check_circuit()
        CircuitManager(self.circuit, report=report).update_LETs(delay=delay)
        JManager.codify(self.circuit, self.circuit.path_to_circuits)

    def save_let_data(self, path_to_folder: str):
        """
        Saves all the LETs data into a .csv file

        Args:
            path_to_folder (str): Path to folder where the file is to be saved.
        """
        self.check_circuit()
        CManager.write_full_csv(self.circuit, path_to_folder)
    
    def mc_analysis(self, n_simu: int, continue_backup:bool = False, delay:bool = False, progress_report: Callable = None):
        """
        Runs a full Monte Carlo analysis of the circuit

        Args:
            n_simu (int): number of MC points
            continue_backup (bool, optional): Whether the MC work should continue from a backup file. Defaults to False.
            delay (bool, optional): Whether delay should be taken into consideration. Defaults to False.
            progress_report (Callable, optional): _description_. Defaults to None.
        """
        self.check_circuit()
        MCManager(self.circuit).full_mc_analysis(n_simu, continue_backup=continue_backup, delay=delay, progress_report=progress_report)
        scatter_data = {"PMOS": [],"NMOS":[],"node":[],"output":[],"current":[],"LETth":[],"pulse_in":[],"pulse_out":[],"input":[]}
        with open(f"{self.circuit.path_to_my_dir}/{self.circuit.name}_mc_LET.csv") as file:
            for linha in file:
                pmos, nmos, node, output, pulse_in, pulse_out, current, let, *inputs = linha.split(",")
                scatter_data["PMOS"].append(float(pmos))
                scatter_data["NMOS"].append(float(nmos))
                scatter_data["node"].append(node)
                scatter_data["output"].append(output)
                scatter_data["current"].append(float(current))
                scatter_data["LETth"].append(float(let))
                scatter_data["pulse_in"].append(pulse_in.strip("['").strip("'"))
                scatter_data["pulse_out"].append(pulse_out.strip("']").strip(" '"))
                inputs = ",".join(inputs).replace("1, ", "1").replace("0, ", "0").replace("[","").replace("]","")
                scatter_data["input"].append(inputs)
        analist = DataAnalist()
        analist.describe(scatter_data, self.circuit.path_to_my_dir)
        analist.quantitative_scatter(scatter_data, "PMOS", "NMOS", "LETth", self.circuit.path_to_my_dir)
        analist.qualitative_scatter(scatter_data, "PMOS", "NMOS", "node", self.circuit.path_to_my_dir)
        analist.qualitative_scatter(scatter_data, "PMOS", "NMOS", "pulse_in", self.circuit.path_to_my_dir)
        analist.qualitative_scatter(scatter_data, "PMOS", "NMOS", "pulse_out", self.circuit.path_to_my_dir)
        analist.qualitative_scatter(scatter_data, "PMOS", "NMOS", "input", self.circuit.path_to_my_dir)
        analist.count_unique(scatter_data, "pulse_out", self.circuit.path_to_my_dir)

    def find_single_let(self, node: str, output: str, logical_input: list, pmos_var: float = 4.8108, nmos_var: float = 4.372, report: bool = True):
        """
        Finds a single minimal LET given a configuration.

        Args:
            node (str): Name of the node the fault is to be inserted.
            output (str): Name of the output the fault it to be propagated to. 
            logical_input (list[bool]): Logical values of the inputs. 
            pmos_var (float, optional): Pmos var. Defaults to 4.8108.
            nmos_var (float, optional): Nmos var. Defaults to 4.372.
            report (bool, optional): Whether a report is to be printed. Defaults to True.
        """
        self.check_circuit()
        with SpiceRunner(self.circuit.path_to_circuits).MC_Instance(pmos_var, nmos_var):
            let_analisado = LET(None, self.circuit.vdd, node, output, [None, None])
            LetFinder(self.circuit, path_to_folder=self.circuit.path_to_circuits, report=report).minimal_LET(let_analisado, logical_input)

if __name__ == "__main__":

    from .matematica import InDir

    print("Testing Backend...")

    with InDir("debug"):

        pseudo: Circuito = Circuito("pseudo", "test_circuits", 0.7).from_json()
        backend: Backend = Backend().set_circuit(pseudo, 0.7)
        backend.find_single_let("out", "out", [0], 4.8825, 4.4941)


        # fadder: Circuito = Circuito("fadder", "test_circuits", 0.7).from_nodes(["a", "b", "cin"], ["cout", "sum"])
        # xor1: Circuito = Circuito("xorv1", "test_circuits", 0.7).from_json()
        # xor5: Circuito = Circuito("xorv5", "test_circuits", 0.7).from_json()

        # {"na", "nb", "ncin", "gate_p16", "gate_p15", "gate_q16", "gate_q15", "drain_p16", "drain_p15", "drain_q16", "drain_q15", "ncout", "nsum", "a1", "b1", "cin1"}

        # backend: Backend = Backend().set_circuit(xor5, 0.7)

        # print("\tTesting LETth determination...")
        # backend.determine_LETs(report=True)
        # backend.save_let_data("test_circuits")

        # backend.mc_analysis(1000)

        # fadder = Circuito("fadder", "test_circuits", 0.7).from_nodes(["a", "b", "cin"], ["cout", "sum"], {"na", "nb", "ncin", "gate_p16", "gate_p15", "gate_q16", "gate_q15", "drain_p16", "drain_p15", "drain_q16", "drain_q15", "ncout", "nsum", "a1", "b1", "cin1"})
        # fadder = Circuito("fadder", "test_circuits", 0.7).from_json()
        # fadder.nodes.sort(key=lambda e: e.name)
        # backend = Backend().set(fadder, 0.7)
        # backend.analise_mc(1000)