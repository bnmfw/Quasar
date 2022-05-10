from arquivos import alternar_combinacao, JManager, CManager
from runner import HSRunner
from matematica import bin2list
from corrente import definir_corrente
from components import Nodo, Entrada, LET
from circuito import Circuito
from time import time
from interface import UserInterface
import os

barra_comprida = "---------------------------"

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
            return None
        
        circuito = Circuito()
        circuito.nome = circuito_nome
        circuito.arquivo = f"{circuito_nome}.cir"
        circuito.path = f"circuitos/{circuito_nome}/"

        # Decodificacao de circuito existente
        if os.path.exists(f"{circuito.path}/{circuito_nome}.json"):
            tensao: float = float(input(f"{barra_comprida}\nCadastro encontrado\nQual vdd deseja analisar: "))
            circuito.vdd = tensao    
            JManager.decodificar(circuito, tensao)
            self.__atualizar_LETths(circuito) # ATUALIZACAO DO CIRCUITO
            return circuito

        # Circuito nao codificado
        self.vdd = float(input("vdd: "))
        HSRunner.default(self.vdd)
        circuito.entradas, circuito.nodos, circuito.saidas = self.declare_circuit_info()

        self.__get_atrasoCC(circuito)
        self.__determinar_LETths(circuito)

        JManager.codificar(circuito)

        return circuito

    @relatorio_de_tempo
    def __get_atrasoCC(self, circuito):
        circuito.atrasoCC = 0
        simulacoes: int = 0

        # Todas as entradas em todas as saidas com todas as combinacoes
        for entrada_analisada in circuito.entradas:
            for saida in circuito.saidas:
                for i in range(2 ** (len(circuito.entradas) - 1)):

                    # Atribui o Sinal das Entradas que Nao Estao em Analise
                    sinais_entrada = bin2list(i, len(circuito.entradas)-1)
                    index = 0
                    for entrada in circuito.entradas:
                        if entrada != entrada_analisada:
                            entrada.sinal = sinais_entrada[index]
                            index += 1
                    entrada_analisada.sinal = "atraso"

                    # Etapa de medicao de atraso
                    atraso: float = HSRunner.run_delay(circuito.path, circuito.arquivo, entrada_analisada.nome, saida.nome, self.vdd, self.entradas)

                    simulacoes += 1

                    if atraso > circuito.atrasoCC:
                        circuito.atrasoCC = atraso

        print(f"Atraso CC do arquivo: {circuito.atrasoCC} simulacoes: {simulacoes}")

    @relatorio_de_tempo
    def __determinar_LETths(self, circuito):
        for nodo in circuito.nodos:
            nodo.LETs = []
        simulacoes: int = 0
        
        ##### BUSCA DO LETs DO CIRCUITO #####
        for nodo in circuito.nodos:
            for saida in circuito.saidas:
                for k in range(2 ** len(circuito.entradas)):  # PASSA POR TODAS AS COMBINACOES DE ENTRADA

                    final = bin2list(k, len(circuito.entradas))
                    ##### DECOBRE OS LETs PARA TODAS AS COBINACOES DE rise E fall #####
                    for combinacao in [a+b for a in "rf" for b in "rf"]:

                        ##### ENCONTRA O LETth PARA AQUELA COMBINACAO #####
                        let_analisado = LET(9999, circuito.vdd, nodo.nome, saida.nome, combinacao)

                        print(nodo.nome, saida.nome, combinacao[0], combinacao[1], final)
                        simulacoes += definir_corrente(circuito, let_analisado, final)

                        for let in nodo.LETs:
                            if let_analisado == let: #encontrou a combinacao correta
                                if let_analisado.corrente == let.corrente:
                                    let.append(final)
                                elif let_analisado.corrente < let.corrente:
                                    nodo.LETs.remove(let)
                                    nodo.LETs.append(let_analisado)
                                break
                        else:
                            if let_analisado.corrente < 1111:
                                nodo.LETs.append(let_analisado)

                        # LETth do circuito
                        if let_analisado.corrente < nodo.LETth.corrente:
                            nodo.LETth = let_analisado

                        if let_analisado.corrente < 1111: break
    
    @relatorio_de_tempo
    def __atualizar_LETths(self, circuito):
        HSRunner.default(circuito.vdd)
        self.__get_atrasoCC(circuito)
        simulacoes: int = 0
        ##### BUSCA DO LETs DO CIRCUITO #####
        circuito.LETth = LET(9999, circuito.vdd, "setup", "setup", "setup")
        for nodo in circuito.nodos:
            for let in nodo.LETs:
                ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                print(let.nodo_nome, let.saida_nome, let.orientacao, let.validacoes[0])
                simulacoes += definir_corrente(circuito, let, let.validacoes[0])
                if let < circuito.LETth:
                    circuito.LETth = let
        print(f"{simulacoes} simulacoes feitas na atualizacao")
        JManager.codificar(circuito)
