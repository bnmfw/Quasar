from dataclasses import dataclass

@dataclass(order=True)
class LET:
    valor: float
    vdd: float
    nodo: str
    saida: str
    orientacao: str
    validacoes: list

class Entrada:
    def __init__(self, nome, sinal):
        self.nome = nome
        self.sinal = sinal
        self.atraso = [0, "saida.nome", ["Vetor de validacao"]]


class Nodo:
    def __init__(self, nome):
        self.nome = nome
        self.validacao = {}
        # self.validacao[saida.nome] = [0,0,"x",1,"t"]
        # Eh um dicionario de vetores
        self.LETth = {}
        # self.LETth[saida.nome] = {"rr": [valor, [//vetor com as validacoes para tal LETth//]],
        #                           "rf": [valor, [//vetor com as validacoes para tal LETth//]],
        #                           "fr": [valor, [//vetor com as validacoes para tal LETth//]],
        #                           "ff": [valor, [//vetor com as validacoes para tal LETth//]]}
        # Eh um dicionario de dicionarios
        self.LETth_critico: float = 9999.9
        self.atraso = {}