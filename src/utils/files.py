"""
Auxillary files manager. Responsible for saving simulation data.
"""

from ..circuit.components import Node, Signal_Input
import json
from os import path


class CSVManager:
    """
    CSV Manager class.
    """

    @staticmethod
    def tup_dict_to_csv(path_to_file: str, filename: str, dicionario: dict):
        with open(path.join(path_to_file, filename), "w") as table:
            for key, value_tuple in dicionario.items():
                table.write(f"{key}")
                for value in value_tuple:
                    table.write(f",{value}")
                table.write("\n")

    @staticmethod
    def tup_to_csv(path_to_file: str, filename: str, lista: list):
        with open(path.join(path_to_file, filename), "w") as tabela:
            for linha in lista:
                tabela.write(f'{",".join([str(e) for e in linha])}')
                tabela.write("\n")

    @staticmethod
    def write_full_csv(circuit, path_to_circuits: str):
        with open(
            path.join(path_to_circuits, circuit.name, f"{circuit.name}.csv"), "w"
        ) as sets:
            sets.write("Node,Output,Pulse,Pulse,Current,LET,#Vector,Vectors->\n")
            for nodo in circuit.nodes:
                nodo.LETs.sort()
                for let in nodo.LETs:
                    c0, c1 = let.orient
                    sets.write(
                        f"{nodo.name},{let.output_name},{c0},{c1},{let.current:.2f},{let.value:.2e},{len(let)}"
                    )
                    for validacao in let.input_states:
                        sets.write(",'")
                        for num in validacao:
                            sets.write(f"{num}")
                    sets.write("\n")
        print(f"\nTable {circuit.name}.csv generated successfully\n")


class JsonManager:
    def __init__(self):
        pass

    def codify(self, circuit, path_to_circuits=path.join("project", "circuits")):
        node_list = []
        for nodo in circuit.nodes:
            node_list.append(nodo.codec())

        # Codificacao de inputs
        output_list = []
        for output_node in circuit.outputs:
            output_list.append(output_node.name)

        # Codificacao de saidas
        input_list = []
        for input_node in circuit.inputs:
            input_list.append(input_node.name)

        codec_circuit = {}
        codec_circuit["name"] = circuit.name
        # codec_circuit["vdd"] = circuit.vdd
        codec_circuit["SPdelay"] = circuit.SPdelay
        codec_circuit["inputs"] = input_list
        codec_circuit["saidas"] = output_list
        codec_circuit["nodos"] = node_list

        if not path.exists(
            path.join(path_to_circuits, circuit.name, f"{circuit.name}.json")
        ):
            json.dump(
                codec_circuit,
                open(
                    path.join(path_to_circuits, circuit.name, f"{circuit.name}.json"),
                    "w",
                ),
            )

        print("Json log dumped")

    def decodify(self, circuit, path_to_circuits=path.join("project", "circuits")):
        codec_circuit: dict = json.load(
            open(path.join(path_to_circuits, circuit.name, f"{circuit.name}.json"), "r")
        )

        # Desempacotamento dos dados
        circuit.SPdelay = codec_circuit["SPdelay"]
        node_list: list = codec_circuit["nodos"]
        output_list: list = codec_circuit["saidas"]
        input_list: list = codec_circuit["inputs"]

        # Carregamento das saidas
        circuit.outputs = [Node(output_node) for output_node in output_list]

        # Carregamento das inputs
        circuit.inputs = [Signal_Input(input_node) for input_node in input_list]

        # Carregamento dos nodos
        for nodo_dict in node_list:
            nodo = Node("name")
            nodo.decodec(nodo_dict)
            circuit.nodes.append(nodo)


# Instancias
JManager = JsonManager()
CManager = CSVManager()
