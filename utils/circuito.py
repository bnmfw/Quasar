"""
Circuit object module. The Circuit object only tracks its nodes, delay, inputs, outputs and Lets.
The actual circuit is fully described in the .cir file and simulated by Spice.
"""
from .arquivos import JManager
from .spiceInterface import SpiceRunner
from .graph import Graph
from .components import Nodo, Entrada, LET
import os

class Circuito():
    """
    Circuit object. Tracks its file, relevant nodes and LETs.
    """
    def __init__(self, name: str, path_to_circuits: str = "circuitos", vdd: float = None):
        """
        Constructor.

            :param str name: Name of the circuit.
            :param str path_to_circuits: Path from project dir to circuits dir.
            :param float vdd: Vdd of the circuit.
        """
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = name
        self.path_to_circuits = path_to_circuits
        self.path_to_my_dir = f"{path_to_circuits}/{name}"
        self.arquivo = f"{name}.cir"
        self.graph: Graph = None
        self.entradas: list[Entrada] = []
        self.saidas: list[Nodo] = []
        self.nodos: list[Nodo]= []
        self.vdd: float = vdd
        self.atrasoCC: float = 0
        self.LETth: LET = None

    def ha_cadastro(self) -> bool:
        """
        Checks whether or not a json file containing the circuit data exists.

            :returns: If the json file exists or not.
        """
        return os.path.exists(f"{self.path_to_my_dir}/{self.nome}.json")

    def from_json(self):
        """
        Fills the circuit object data from the json file.
        """
        JManager.decodificar(self, path_to_folder=self.path_to_circuits)
        return self
    
    def from_nodes(self, inputs: list, outputs: list, ignore: list = None):
        """
        Fills the circuit object by parsing the .cir file.

            :param list[str] inputs: List of node names to be interpreted as inputs.
            :param list[str] outputs: List of node names to be interpreted as outputs.
            :param list[str] ignore: Nodes that should be ignored.
        """
        self.saidas = [Nodo(output) for output in outputs]
        self.entradas = [Entrada(input) for input in inputs]
        nodes_set, self.graph = SpiceRunner(path_to_folder=self.path_to_circuits).get_nodes(self.nome, ignore)
        self.nodos = [Nodo(nodo) for nodo in nodes_set]
        return self

if __name__ == "__main__":
    print("Testing Circuit Module...")
    # Decodification test of the circuit
    print("\tTesting decodification of circuit from json file...")
    decodec_test = Circuito("decodec_test", path_to_circuits="debug/test_circuits", vdd=0.7).from_json()
    assert decodec_test.ha_cadastro(), "CIRCUIT FAILED FOR CHECKING JSON FILE"
    assert decodec_test.nome == "decodec_test", "CIRCUIT DECODE FAILED FOR NAME"
    assert decodec_test.path_to_my_dir == "debug/test_circuits/decodec_test", "CIRCUIT DECODE FAILED FOR PATH"
    assert decodec_test.arquivo == "decodec_test.cir", "CIRCUIT DECODE FAILED FOR FILE NAME"
    assert decodec_test.entradas[0].nome == "a" and decodec_test.entradas[0].sinal == "setup", "CIRCUIT DECODE FAILED FOR INPUT SIGNALS"
    assert list(map(lambda e: e.nome, decodec_test.nodos)) == ["g1", "i1"], "CIRCUIT DECODE FAILED FOR NODES"
    assert list(map(lambda e: len(e.LETs), decodec_test.nodos)) == [2, 2], "CIRCUIT DECODE FAILED FOR NUMBER OS LETS"
    assert list(map(lambda e: e.nome, decodec_test.saidas)) == ["g1"], "CIRCUIT DECODE FAILED FOR OUTPUTS"
    assert decodec_test.vdd == 0.7, "CIRCUIT DECODE FAILED FOR VDD"
    
    print("\tTesting parsing of circuit file...")
    parsing_test = Circuito("fadder", path_to_circuits="debug/test_circuits", vdd=0.7).from_nodes(["a","b", "cin"],["cout", "sum"])
    # assert {nodo.nome for nodo in parsing_test.nodos} == {"cout", "sum"}, "CIRCUIT PARSING FAILED"
    # for vi in parsing_test.graph.vertices.values():
    #     print(vi["name"],end="\t")
    #     print(vi["reaches"])

    print("Circuit Module OK")