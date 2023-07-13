from .arquivos import JManager
from .spiceInterface import HSRunner
from .components import Nodo, Entrada, LET
import os

barra_comprida = "---------------------------"

class Circuito():
    def __init__(self, nome: str, vdd: float = None):
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = nome
        self.path = f"/{nome}/"
        self.arquivo = f"{nome}.cir"
        self.entradas: list[Entrada] = []
        self.saidas: list[Nodo] = []
        self.nodos: list[Nodo]= []
        self.vdd: float = vdd
        self.atrasoCC: float = 0
        self.LETth: LET = None

    def ha_cadastro(self, path_to_folder="circuitos") -> bool:
        return os.path.exists(f"{path_to_folder}{self.path}{self.nome}.json")

    # Instancia o circuito a partir de um json
    def from_json(self, path_to_folder="circuitos"):
        JManager.decodificar(self, path_to_folder=path_to_folder)
        return self
    
    def from_nodes(self, nodes, entradas, saidas):
        # entradas, saidas = (input("entradas: ").split() , input("saidas: ").split())
        ##### SAIDAS #####
        self.saidas = [Nodo(saida) for saida in saidas]
        ##### ENTRADAS #####
        self.entradas = [Entrada(entrada) for entrada in entradas]
        ##### OUTROS NODOS #####
        self.nodos = [Nodo(nodo) for nodo in HSRunner.get_nodes(self.nome)]
        # JManager.codificar(self)
        return self

if __name__ == "__main__":
    # Decodification test of the circuit
    print("Testing decodification of circuit from json file...")
    decodec_test = Circuito("decodec_test", 0.7).from_json(path_to_folder="debug/test_circuits")
    assert decodec_test.nome == "decodec_test"
    assert decodec_test.path == "/decodec_test/"
    assert decodec_test.arquivo == "decodec_test.cir"
    assert decodec_test.entradas[0].nome == "a" and decodec_test.entradas[0].sinal == "setup"
    assert list(map(lambda e: e.nome, decodec_test.nodos)) == ["g1", "i1"]
    assert list(map(lambda e: len(e.LETs), decodec_test.nodos)) == [2, 2]
    assert list(map(lambda e: e.nome, decodec_test.saidas)) == ["g1"]
    assert decodec_test.vdd == 0.7
    assert decodec_test.ha_cadastro(path_to_folder="debug/test_circuits")