"""
Circuit object module. The Circuit object only tracks its nodes, delay, inputs, outputs and Lets.
The actual circuit is fully described in the .cir file and simulated by Spice.
"""
from .arquivos import JManager
from .spiceInterface import HSRunner
from .components import Nodo, Entrada, LET
import os

barra_comprida = "---------------------------"

class Circuito():
    """
    Circuit object. Tracks its file, relevant nodes and LETs.
    """
    def __init__(self, name: str, vdd: float = None):
        """
        Constructor.

            :param str name: Name of the circuit.
            :param float vdd: Vdd of the circuit.
        """
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = name
        self.path = f"/{name}/"
        self.arquivo = f"{name}.cir"
        self.entradas: list[Entrada] = []
        self.saidas: list[Nodo] = []
        self.nodos: list[Nodo]= []
        self.vdd: float = vdd
        self.atrasoCC: float = 0
        self.LETth: LET = None

    def ha_cadastro(self, path_to_folder: str = "circuitos") -> bool:
        """
        Checks whether or not a json file containing the circuit data exists.

            :param str path_to_folder: Path to circuits directory.
            :returns: If the json file exists or not.
        """
        return os.path.exists(f"{path_to_folder}{self.path}{self.nome}.json")

    def from_json(self, path_to_folder: str = "circuitos"):
        """
        Fills the circuit object data from the json file.
        """
        JManager.decodificar(self, path_to_folder=path_to_folder)
        return self
    
    def from_nodes(self, inputs: list, outputs: list):
        """
        Fills the circuit object by parsing the .cir file.

            :param list[str] inputs: List of node names to be interpreted as inputs.
            :param list[str] outputs: List of node names to be interpreted as outputs.
        """
        self.saidas = [Nodo(output) for output in outputs]
        self.entradas = [Entrada(input) for input in inputs]
        self.nodos = [Nodo(nodo) for nodo in HSRunner.get_nodes(self.nome)]
        return self

if __name__ == "__main__":
    # Decodification test of the circuit
    print("Testing decodification of circuit from json file...")
    decodec_test = Circuito("decodec_test", 0.7).from_json(path_to_folder="debug/test_circuits")
    assert decodec_test.ha_cadastro(path_to_folder="debug/test_circuits"), "CIRCUIT FAILED FOR CHECKING JSON FILE"
    assert decodec_test.nome == "decodec_test", "CIRCUIT DECODE FAILED FOR NAME"
    assert decodec_test.path == "/decodec_test/", "CIRCUIT DECODE FAILED FOR PATH"
    assert decodec_test.arquivo == "decodec_test.cir", "CIRCUIT DECODE FAILED FOR FILE NAME"
    assert decodec_test.entradas[0].nome == "a" and decodec_test.entradas[0].sinal == "setup", "CIRCUIT DECODE FAILED FOR INPUT SIGNALS"
    assert list(map(lambda e: e.nome, decodec_test.nodos)) == ["g1", "i1"], "CIRCUIT DECODE FAILED FOR NODES"
    assert list(map(lambda e: len(e.LETs), decodec_test.nodos)) == [2, 2], "CIRCUIT DECODE FAILED FOR NUMBER OS LETS"
    assert list(map(lambda e: e.nome, decodec_test.saidas)) == ["g1"], "CIRCUIT DECODE FAILED FOR OUTPUTS"
    assert decodec_test.vdd == 0.7, "CIRCUIT DECODE FAILED FOR VDD"