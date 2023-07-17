from .components import Nodo, Entrada
import json
import os

analise_manual = False

class CSVManager():
    def __init__(self):
        pass

    @staticmethod
    def tup_dict_to_csv(path: str, filename: str, dicionario: dict):
        with open(f"{path}/{filename}", "w") as tabela:
            for chave, tupla in dicionario.items():
                tabela.write(f"{chave}")
                for valor in tupla:
                    tabela.write(f",{valor}")
                tabela.write("\n")

    @staticmethod
    def tup_to_csv(path: str, filename: str, lista: list):
        with open(f"{path}/{filename}", "w") as tabela:
            for linha in lista:
                tabela.write(f'{",".join([str(e) for e in linha])}')
                tabela.write("\n")

    @staticmethod
    def escrever_csv_total(circuito):
        linha = 2
        with open(f"circuitos/{circuito.nome}/{circuito.nome}.csv", "w") as sets:
            sets.write("Nodo,Saida,Pulso,Pulso,Corrente,LETs,Num Val,Validacoes->\n")
            for nodo in circuito.nodos:
                for let in nodo.LETs:
                    c0, c1 = let.orientacao
                    sets.write(f"{nodo.nome},{let.saida_nome},{c0},{c1},{let.corrente:.2f},{let.valor:.2e},{len(let)}")
                    for validacao in let.validacoes:
                        sets.write(",'")
                        for num in validacao: sets.write(f"{num}")
                    sets.write("\n")
                    linha += 1
        print(f"\nTabela {circuito.nome}.csv gerada com sucesso\n")

    @staticmethod
    def escrever_csv_comparativo(circuito, lista_comparativa):
        with open(f"circuitos/{circuito.nome}/{circuito.nome}_compara.csv", "w") as tabela:
            for chave in lista_comparativa:
                tabela.write(chave + "," + "{:.2f}".format(lista_comparativa[chave]) + "\n")

        print(f"\nTabela {circuito.nome}_compara.csv" + " gerada com sucesso\n")

class JsonManager():
    def __init__(self):
        pass

    def codificar(self, circuito, path_to_folder="circuitos"):
        # Codificacao dos nodos
        dicionario_de_nodos = {}  # criacao do dicionario que tera o dicionario de todos os nodos
        lista_de_nodos = []
        for nodo in circuito.nodos:
            lista_de_nodos.append(nodo.codec())

        # Codificacao de entradas
        lista_de_saidas = []
        for saida in circuito.saidas:
            lista_de_saidas.append(saida.nome)

        # Codificacao de saidas
        lista_de_entradas = []
        for entrada in circuito.entradas:
            lista_de_entradas.append(entrada.nome)

        circuito_codificado = {}
        circuito_codificado["nome"] = circuito.nome
        circuito_codificado["vdd"] = circuito.vdd
        circuito_codificado["atrasoCC"] = circuito.atrasoCC
        circuito_codificado["entradas"] = lista_de_entradas
        circuito_codificado["saidas"] = lista_de_saidas
        circuito_codificado["nodos"] = lista_de_nodos

        if not os.path.exists(f"{path_to_folder}/{circuito.nome}/{circuito.nome}.json"):
            json.dump(circuito_codificado, open(f"{path_to_folder}/{circuito.nome}/{circuito.nome}.json", "w"))

        print("Carregamento do Json realizado com sucesso")

    def decodificar(self, circuito, path_to_folder="circuitos"):
        circuito_codificado: dict = json.load(open(f"{path_to_folder}/{circuito.nome}/{circuito.nome}.json", "r"))

        # Desempacotamento dos dados
        circuito.atrasoCC = circuito_codificado["atrasoCC"]
        lista_de_nodos: list = circuito_codificado["nodos"]
        lista_de_saidas: list = circuito_codificado["saidas"]
        lista_de_entradas: list = circuito_codificado["entradas"]

        # Carregamento das saidas
        circuito.saidas = [Nodo(saida) for saida in lista_de_saidas]

        # Carregamento das entradas
        circuito.entradas = [Entrada(entrada) for entrada in lista_de_entradas]

        # Carregamento dos nodos
        for nodo_dict in lista_de_nodos:
            nodo = Nodo("nome")
            nodo.decodec(nodo_dict, circuito.vdd)
            circuito.nodos.append(nodo)

        # print("Leitura do Json realizada com sucesso")

# Instancias
JManager = JsonManager()
CManager = CSVManager()