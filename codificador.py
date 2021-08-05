from components import Nodo, Entrada, LET
import json

class JsonManager():
    def __init__(self):
        pass


    def codificar(self, circuito):
        #Codificacao dos nodos
        dicionario_de_nodos = {} #criacao do dicionario que tera o dicionario de todos os nodos
        lista_de_nodos = []
        for nodo in circuito.nodos:
            lista_de_nodos.append(nodo.codec())

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
        circuito_codificado["nodos"] = lista_de_nodos

        json.dump(circuito_codificado, open(f"{circuito.nome}_{circuito.vdd}.json","w"))

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
        lista_de_nodos = circuito_codificado["nodos"]
        lista_de_saidas = circuito_codificado["saidas"]
        lista_de_entradas = circuito_codificado["entradas"]

        #Carregamento das saidas
        for saida in lista_de_saidas:
            circuito.saidas.append(Nodo(saida))

        #Carregamento das entradas
        for entrada in lista_de_entradas:
            circuito.entradas.append(Entrada(entrada, "t"))

        #Carregamento dos nodos
        for nodo_analisado in lista_de_nodos:
            nodo = Nodo("nome")
            nodo.decodec(nodo_analisado, circuito.vdd)
            circuito.nodos.append(nodo)

        print("Leitura do Json realizada com sucesso\n")

JM = JsonManager()

def alternar_combinacao(combinacao):
    if type(combinacao) == str:
        if combinacao == "rr": return ["rise", "rise"]
        elif combinacao == "rf": return ["rise", "fall"]
        elif combinacao == "fr": return ["fall", "rise"]
        else: return ["fall", "fall"]
    elif type(combinacao) == list:
        if combinacao == ["rise", "rise"]: return "rr"
        elif combinacao == ["rise", "fall"]: return "rf"
        elif combinacao == ["fall", "rise"]: return "fr"
        else: return "ff"
    else: raise TypeError("Entrada nao foi uma lista (ex: [\"rise\",\"fall\"]) ou uma string (ex: \"rf\"")

if __name__ == "__main__":

    print("Rodando Teste de Codificacao...")

    let1 = LET(154.3, 0.7, "nodo1", "saida1", "fr")
    let2 = LET(300, 0.7, "nodo1", "saida1", "rf")
    let3 = LET(190.8, 0.7, "nodo2", "saida1", "fr")
    let4 = LET(156.9, 0.7, "nodo2", "saida1", "ff")
    let5 = LET(7.4, 0.7, "saida", "saida1", "rr")
    let6 = LET(288.1, 0.7, "saida", "saida1", "rf")

    nodo1 = Nodo("nodo1")
    nodo1.validacao = {"saida1":["x","x","x","x","x"]}
    nodo1.LETs = [let1, let2]
    nodo1.LETth = 154.3

    nodo2 = Nodo("nodo2")
    nodo2.validacao = {"saida1": ["x", "x", "x", "x", "x"]}
    nodo2.LETs = [let2, let3]
    nodo2.LETth = 156.9

    nodo3 = Nodo("saida1")
    nodo3.validacao = {"saida1": ["x", "x", "x", "x", "x"]}
    nodo3.LETs = [let4, let5]
    nodo3.LETth = 7.4

    class FakeCircuit:
        def __init__(self):
            self.nome = "teste_circuito"
            self.entradas = [Entrada("a", "t"), Entrada("b", "t")]
            self.saidas = [nodo3]
            self.nodos = [nodo1, nodo2, nodo3]
            self.vdd = 0.7
            self.atrasoCC = 9999.0

    circuito = FakeCircuit()

    JM.codificar(circuito)
    JM.decodificar(circuito, 0.7, True)

    print("Testes realizados com sucesso")