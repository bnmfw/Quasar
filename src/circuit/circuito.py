"""
Circuit object module. The Circuit object only tracks its nodes, delay, inputs, outputs and Lets.
The actual circuit is fully described in the .cir file and simulated by Spice.
"""
from ..utils.arquivos import JManager
from ..utils.matematica import InDir
from ..simconfig.simulationConfig import sim_config
from .graph import Graph
from .components import Node, Signal_Input, LET
from os import path

class Circuito():
    """
    Circuit object. Tracks its file, relevant nodes and LETs.
    """
    def __init__(self, name: str, path_to_folder = path.join("project")):
        """
        Constructor.

        Args:
            name (str): Name of the circuit.
            path_to_circuits (str): Path from project dir to circuits dir.
            vdd (float): Vdd of the circuit.
        """
        ##### ATRIBUTOS DO CIRCUITO #####
        self.name = name
        self.path_to_folder = path_to_folder
        self.path_to_circuits = path.join(path_to_folder,'circuits')
        self.path_to_my_dir = path.join(self.path_to_circuits, name)
        self.file = f"{name}.cir"
        self.graph: Graph = None
        self.inputs: list[Signal_Input] = []
        self.saidas: list[Node] = []
        self.nodes: list[Node]= []
        # self.vdd: float = vdd
        self.SPdelay: float = 0
        self.LETth: LET = None
        self.loaded: bool = False

    def ha_cadastro(self) -> bool:
        """
        Checks whether or not a json file containing the circuit data exists.

        Returns:
            bool: If the json file exists or not.
        """
        return path.exists(path.join(self.path_to_my_dir,f"{self.name}.json"))

    def from_json(self):
        """
        Fills the circuit object data from the json file.
        """
        JManager.decodify(self, path_to_circuits=self.path_to_circuits)
        self.loaded = True
        return self
    
    def from_nodes(self, inputs: list, outputs: list):
        """
        Fills the circuit object by parsing the .cir file.

        Args:
            inputs (list[str]): List of node names to be interpreted as inputs.
            outputs (list[str]): List of node names to be interpreted as outputs.
        """
        self.inputs = [Signal_Input(input) for input in inputs]
        nodes_set, self.graph = sim_config.runner(path_to_folder=self.path_to_folder).get_nodes(self.name)
        self.nodes = [Node(nodo) for nodo in nodes_set]
        self.saidas = [self.get_node(output) for output in outputs]
        return self

    def set_signals(self, sig_values: list):
        """
        Sets signals of inputs given its values.

        Args:
            sig_values (list[Input_Signals]): A list of input values.
        """

        for input_gate, input_signal in zip(self.inputs, sig_values):
            input_gate.signal = input_signal
    
    def get_node(self, node: str):
        """
        Gets the node object given its name

        Args:
            node (str): Node name
        """
        for n in self.nodes:
            if n.name == node: return n
        return None

if __name__ == "__main__":
    with InDir('debug'):
        print("Testing Circuit Module...")
        from ..spiceInterface.spiceInterface import HSpiceRunner
        sim_config.runner = HSpiceRunner
        # Decodification test of the circuit
        print("\tTesting decodification of circuit from json file...")
        decodec_test = Circuito("decodec_test").from_json()
        assert decodec_test.ha_cadastro(), "CIRCUIT FAILED FOR CHECKING JSON FILE"
        assert decodec_test.name == "decodec_test", "CIRCUIT DECODE FAILED FOR NAME"
        assert decodec_test.path_to_my_dir == path.join("project","circuits","decodec_test"), "CIRCUIT DECODE FAILED FOR PATH"
        assert decodec_test.file == "decodec_test.cir", "CIRCUIT DECODE FAILED FOR FILE NAME"
        assert decodec_test.inputs[0].name == "a" and decodec_test.inputs[0].signal == "setup", "CIRCUIT DECODE FAILED FOR INPUT SIGNALS"
        assert list(map(lambda e: e.name, decodec_test.nodes)) == ["g1", "i1"], "CIRCUIT DECODE FAILED FOR NODES"
        assert list(map(lambda e: len(e.LETs), decodec_test.nodes)) == [2, 2], "CIRCUIT DECODE FAILED FOR NUMBER OS LETS"
        assert list(map(lambda e: e.name, decodec_test.saidas)) == ["g1"], "CIRCUIT DECODE FAILED FOR OUTPUTS"
        
        print("\tTesting parsing of circuit file...")
        parsing_test = Circuito("fadder").from_nodes(["a","b", "cin"],["cout", "sum"])
        # assert {nodo.name for nodo in parsing_test.nodes} == {"cout", "sum"}, "CIRCUIT PARSING FAILED"
        # for vi in parsing_test.graph.vertices.values():
        #     print(vi["name"],end="\t")
        #     print(vi["reaches"])

        print("Circuit Module OK")