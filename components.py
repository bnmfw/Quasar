class Entrada:
    def __init__(self, nome, sinal):
        self.nome = nome
        self.sinal = sinal
        self.atraso = [0, "saida.nome", ["Vetor de validacao"]]

    def __dict__(self):
        dic = {}
        dic["nome"] = self.nome
        dic["sinal"] = self.sinal
        dic["atraso"] = self.atraso
        return dic

    def decodec(self, dic: dict):
        self.nome = dic["nome"]
        self.sinal = dic["sinal"]
        self.atraso = dic["atraso"]



class Nodo:
    def __init__(self, nome):
        self.nome = nome
        self.validacao = {}
        # self.validacao[saida.nome] = [0,0,"x",1,"t"]
        self.LETs = []
        # Eh um dicionario de dicionarios
        self.LETth: float = 9999.9
        self.atraso = {}

    def __dict__(self):
        dic = {}
        dic["nome"] = self.nome
        dic["val"] = self.validacao
        dic["critico"] = self.LETth
        dic["atraso"] = self.atraso
        lista_de_nodos = []
        for let in self.LETs:
            lista_de_nodos.append(let.__dict__)
        dic["lets"] = lista_de_nodos
        return dic

    def decodec(self, dic:dict, vdd:float):
        self.nome = dic["nome"]
        self.validacao = dic["val"]
        self.LETth = dic["critico"]
        self.atraso = dic["atraso"]
        for dicionario_let in dic["lets"]:
            let = LET(9999, vdd, "nodo", "saida", "orientacao")
            let.decodec(dicionario_let)
            self.LETs.append(let)


class LET:
    def __init__(self, corrente:float, vdd:float, nodo_nome:str, saida_nome:str, orientacao:str):
        self.corrente = corrente
        self.orientacao = orientacao
        self.vdd = vdd
        self.nodo_nome = nodo_nome
        self.saida_nome = saida_nome
        self.validacoes = []

    def __eq__(self, other):
        return (self.nodo_nome == other.nodo_nome and self.saida_nome == other.saida_nome and self.orientacao == other.orientacao)

    def adicionar_entrada(self, validacao:list):
        if type(validacao) != list: raise TypeError("Validacao nao eh uma lista")
        self.validacoes.append(validacao)

    def __dict__(self):
        dic = {}
        dic["corr"] = self.corrente
        dic["orie"] = self.orientacao
        dic["nodo"] = self.nodo_nome
        dic["said"] = self.saida_nome
        dic["val"] = self.validacoes
        return dic

    def decodec(self, dic:dict):
        self.corrente = dic["corr"]
        self.orientacao = dic["orie"]
        self.nodo_nome = dic["nodo"]
        self.saida_nome = ["said"]
        self.validacoes = dic["val"]