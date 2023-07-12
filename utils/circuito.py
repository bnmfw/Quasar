from .arquivos import JManager
from .runner import HSRunner
from .components import Nodo, Entrada, LET
import os

barra_comprida = "---------------------------"

class Circuito():
    def __init__(self, nome: str, vdd: float = None):
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = nome
        self.path = f"/{nome}/"
        self.arquivo = f"{nome}.cir"
        self.entradas = []
        self.saidas = []
        self.nodos = []
        self.vdd: float = vdd
        self.atrasoCC: float = 0
        self.LETth: LET = None

    def ha_cadastro(self) -> bool:
        return os.path.exists(f"circuitos{self.path}{self.nome}.json")

    # Instancia o circuito a partir de um json
    def from_json(self):
        JManager.decodificar(self)
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

    print("Testando funcionalidades basicas do circuito...")

    circuito_teste = Circuito()
    circuito_teste.nome = "Teste"
    circuito_teste.arquivo = "Teste.cir"
    circuito_teste.vdd = 0.7
