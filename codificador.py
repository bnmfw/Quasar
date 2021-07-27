from components import Nodo, Entrada
import json

class JsonManager():
    def __init__(self):
        pass

    def codificar(self, circuito):
        #Codificacao dos nodos
        dicionario_de_nodos = {} #criacao do dicionario que tera o dicionario de todos os nodos
        for nodo in circuito.nodos:
            este_nodo = {} #dicionario contendo as informacoes deste nodo
            este_nodo["nome"] = nodo.nome
            este_nodo["validacao"] = nodo.validacao
            este_nodo["LETth"] = nodo.LETth
            este_nodo["LETth_critico"] = nodo.LETth_critico
            este_nodo["atraso"] = nodo.atraso
            dicionario_de_nodos[nodo.nome] = este_nodo

        #Codificacao de entradas
        lista_de_saidas = []
        for saida in circuito.saidas:
            lista_de_saidas.append(saida.nome)

        #Codificacao de saidas
        lista_de_entradas = []
        for entrada in circuito.entradas:
            lista_de_entradas.append(entrada.nome)

        circuito_codificado = {}
        circuito_codificado["nome"] = circuito.nome
        circuito_codificado["vdd"] = circuito.vdd
        circuito_codificado["atrasoCC"] = circuito.atrasoCC
        circuito_codificado["entradas"] = lista_de_entradas
        circuito_codificado["saidas"] = lista_de_saidas
        circuito_codificado["nodos"] = dicionario_de_nodos

        json.dump(circuito_codificado, open(circuito.nome+"_"+str(circuito.vdd)+".json","w"))

        try:
            with open(circuito.nome+".json","r"):
                pass
        except FileNotFoundError:
            json.dump(circuito_codificado, open(circuito.nome + ".json", "w"))

        print("Carregamento do Json realizado com sucesso\n")

    def decodificar(self, circuito, tensao, nao_usar_template):
        circuito_codificado = []
        if nao_usar_template:
            circuito_codificado = json.load(open(circuito.nome+"_"+str(tensao)+".json", "r"))
            circuito.vdd = circuito_codificado["vdd"]
        else:
            circuito_codificado = json.load(open(circuito.nome + ".json", "r"))
            circuito.vdd = tensao

        #Desempacotamento dos dados
        circuito.atrasoCC = circuito_codificado["atrasoCC"]
        dicionario_de_nodos = circuito_codificado["nodos"]
        lista_de_saidas = circuito_codificado["saidas"]
        lista_de_entradas = circuito_codificado["entradas"]

        #Carregamento das saidas
        for saida in lista_de_saidas:
            circuito.saidas.append(Nodo(saida))

        #Carregamento das entradas
        for entrada in lista_de_entradas:
            circuito.entradas.append(Entrada(entrada, "t"))

        #Carregamento dos nodos
        for nodo in dicionario_de_nodos:
            nodo = dicionario_de_nodos[nodo]
            nodo_obj = Nodo(nodo["nome"])
            nodo_obj.LETth = nodo["LETth"]
            nodo_obj.validacao = nodo["validacao"]
            nodo_obj.LETth_critico = nodo["LETth_critico"]
            nodo_obj.atraso = nodo["atraso"]
            circuito.nodos.append(nodo_obj)

        print("Leitura do Json realizada com sucesso\n")

JM = JsonManager()