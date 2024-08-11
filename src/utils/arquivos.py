"""
Auxillary files manager. Responsible for saving simulation data.
"""

from ..circuit.components import Node, Signal_Input
import json
from os import path

class CSVManager():
    """
    CSV Manager class.
    """
    @staticmethod
    def tup_dict_to_csv(path_to_file: str, filename: str, dicionario: dict):
        with open(path.join(path_to_file,filename), "w") as table:
            for chave, tupla in dicionario.items():
                table.write(f"{chave}")
                for value in tupla:
                    table.write(f",{value}")
                table.write("\n")

    @staticmethod
    def tup_to_csv(path_to_file: str, filename: str, lista: list):
        with open(path.join(path_to_file,filename), "w") as tabela:
            for linha in lista:
                tabela.write(f'{",".join([str(e) for e in linha])}')
                tabela.write("\n")

    @staticmethod
    def write_full_csv(circuito, path_to_circuits: str):
        with open(path.join(path_to_circuits,circuito.name,f"{circuito.name}.csv"), "w") as sets:
            sets.write("Node,Output,Pulse,Pulse,Current,LET,#Vector,Vectors->\n")
            for nodo in circuito.nodes:
                nodo.LETs.sort()
                for let in nodo.LETs:
                    c0, c1 = let.orientacao
                    sets.write(f"{nodo.name},{let.output_name},{c0},{c1},{let.current:.2f},{let.value:.2e},{len(let)}")
                    for validacao in let.input_states:
                        sets.write(",'")
                        for num in validacao: sets.write(f"{num}")
                    sets.write("\n")
        print(f"\nTabela {circuito.name}.csv gerada com sucesso\n")

class JsonManager():
    def __init__(self):
        pass

    def codify(self, circuito, path_to_circuits=path.join("project","circuits")):
        # Codificacao dos nodos
        dicionario_de_nodos = {}  # criacao do dicionario que tera o dicionario de todos os nodos
        lista_de_nodos = []
        for nodo in circuito.nodes:
            lista_de_nodos.append(nodo.codec())

        # Codificacao de inputs
        lista_de_saidas = []
        for saida in circuito.saidas:
            lista_de_saidas.append(saida.name)

        # Codificacao de saidas
        lista_de_entradas = []
        for entrada in circuito.inputs:
            lista_de_entradas.append(entrada.name)

        circuito_codificado = {}
        circuito_codificado["name"] = circuito.name
        # circuito_codificado["vdd"] = circuito.vdd
        circuito_codificado["SPdelay"] = circuito.SPdelay
        circuito_codificado["inputs"] = lista_de_entradas
        circuito_codificado["saidas"] = lista_de_saidas
        circuito_codificado["nodos"] = lista_de_nodos

        if not path.exists(path.join(path_to_circuits,circuito.name,f"{circuito.name}.json")):
            json.dump(circuito_codificado, open(path.join(path_to_circuits,circuito.name,f"{circuito.name}.json"), "w"))

        print("Carregamento do Json realizado com sucesso")

    def decodify(self, circuito, path_to_circuits=path.join("project","circuits")):
        circuito_codificado: dict = json.load(open(path.join(path_to_circuits,circuito.name,f"{circuito.name}.json"), "r"))

        # Desempacotamento dos dados
        circuito.SPdelay = circuito_codificado["SPdelay"]
        lista_de_nodos: list = circuito_codificado["nodos"]
        lista_de_saidas: list = circuito_codificado["saidas"]
        lista_de_entradas: list = circuito_codificado["inputs"]

        # Carregamento das saidas
        circuito.saidas = [Node(saida) for saida in lista_de_saidas]

        # Carregamento das inputs
        circuito.inputs = [Signal_Input(entrada) for entrada in lista_de_entradas]

        # Carregamento dos nodos
        for nodo_dict in lista_de_nodos:
            nodo = Node("name")
            nodo.decodec(nodo_dict)
            circuito.nodes.append(nodo)

        # print("Leitura do Json realizada com sucesso")

# Instancias
JManager = JsonManager()
CManager = CSVManager()