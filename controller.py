from arquivos import alternar_combinacao, JManager, CManager
from runner import HSRunner
from matematica import bin2list
from corrente import definir_corrente
from components import Nodo, Entrada, LET
from circuito import Circuito
from time import time
import os

def relatorio_de_tempo(func):
    def wrapper(*args, **kwargs):
        start = time()
        rv = func(*args, **kwargs)
        end = time()
        tempo = int(end - start)
        dias: int = tempo // 86400
        horas: int = (tempo % 86400) // 3600
        minutos: int = (tempo % 3600) // 60
        if dias: print(f"{dias} dias, ", end='')
        if horas: print(f"{horas} horas, ", end='')
        if minutos: print(f"{minutos} minutos e ", end='')
        print(f"{tempo % 60} segundos de execucao")
        return rv
    return wrapper

class Controlador:
    def __init__(self):
        self.circuito: Circuito = None
        pass

    def declare_circuit_info(self):
        # Recebe a entrada do usuario e cria uma lista de nodos, entradas e saidas pro circuito
        saidas = [Nodo(saida) for saida in input("saidas: ").split()]
        entradas = [Entrada(entrada) for entrada in input("entradas: ").split()]
        nodos = []
        nodos_visitados = []
        ignorados = ["t" + entrada.nome for entrada in self.entradas] + ["f" + entrada.nome for entrada in self.entradas]

        with open(f"{self.path}{self.arquivo}", "r") as circuito:
            for linha in circuito:
                if "M" in linha:
                    _, coletor, base, emissor, _, _, _ = linha.split()
                    for nodo in [coletor, base, emissor]:
                        if nodo not in {"vdd", "gnd", *nodos_visitados, *ignorados}:
                            nodo = Nodo(nodo)
                            nodos_visitados.append(nodo.nome)
                            for saida in self.saidas:
                                nodo.atraso[saida.nome] = 1111
                            nodos.append(nodo)

        return (entradas, nodos, saidas)

    def configure_circuit(self, circuito_nome: str):
        # Configura o circuito escolhido pelo usuario
        
        if not os.path.exists(f"circuitos/{circuito_nome}/{circuito_nome}.cir"):
            print("O circuito escolhido nao existe\n")
            return
        
        
        entradas, nodos, saidas = self.declare_circuit_info()
