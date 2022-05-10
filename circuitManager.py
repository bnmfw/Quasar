from runner import HSRunner
from components import *

class CircuitManager:
    def __init__(self):
        self.circuito = None
        self.limite_sup = 799

    # Funcao que verifica se aquela analise de radiacao eh valida (ou seja, se tem o efeito desejado na saida)
    def verificar_validacao(self, circuito, vdd: float, let: LET) -> tuple:
        inclinacao_nodo, inclinacao_saida = let.orientacao
        
        # Checagem se os niveis de tensao estar corretos

        tensao_pico_nodo, tensao_pico_saida = HSRunner.run_SET(circuito.path, circuito.arquivo, let, 0)

        if (inclinacao_saida == "r" and tensao_pico_saida > vdd * 0.51) or\
            (inclinacao_saida == "f" and tensao_pico_saida < vdd * 0.1) or\
            (inclinacao_nodo == "r" and tensao_pico_nodo > vdd * 0.51) or\
            (inclinacao_nodo == "f" and tensao_pico_nodo < vdd * 0.1):
            print("Analise invalida - Tensoes improprias\n")
            return (False, 1)

        # Chegagem se o pulso no nodo tem resposta na saída
        tensao_pico_nodo, tensao_pico_saida = HSRunner.run_SET(circuito.path, circuito.arquivo, let,self.limite_sup)

        if (inclinacao_saida == "r" and tensao_pico_saida < vdd * 0.50) or\
            (inclinacao_saida == "f" and tensao_pico_saida > vdd * 0.50) or\
            (inclinacao_nodo == "r" and tensao_pico_nodo < vdd * 0.50) or\
            (inclinacao_nodo == "f" and tensao_pico_nodo > vdd * 0.50):
            print("Analise invalida - Pulso sem efeito\n")
            return (False, 2)

        return (True, 2)


    ##### ENCONTRA A CORRENTE MINIMA PARA UM LET #####
    def encontrar_corrente_minima(self, circuito, let: LET) -> float:

        # variaveis da busca binaria da corrente
        csup: float = self.limite_sup
        cinf: float = 0
        corrente: float = (csup + cinf)/2

        # Busca binaria para largura de pulso
        diferenca_largura: float = 100
        precisao_largura: float = 0.05e-9

        # Busca binaria para corrente minima
        while diferenca_largura == None or not -precisao_largura < diferenca_largura < precisao_largura:

            # Encontra a largura minima de pulso pra vencer o atraso
            largura = HSRunner.run_pulse_width(circuito.path, circuito.arquivo, let, corrente)
            diferenca_largura: float = None if largura == None else largura - circuito.atrasoCC

            if abs(csup - cinf) < 1:
                print("PULSO MINIMO ENCONTRADO - DIFERENCA DE BORDAS PEQUENA")
                return corrente
            if diferenca_largura == None:
                cinf = corrente
            elif diferenca_largura > precisao_largura:
                csup = corrente
            elif diferenca_largura < -precisao_largura:
                cinf = corrente
            corrente = (csup + cinf) / 2

        print("PULSO MINIMO ENCONTRADO - PRECISAO SATISFEITA")
        return corrente


    ##### ENCONTRA A CORRENTE DE UM LET ######
    def definir_corrente(self, circuito, let: LET, validacao: list) -> int:
        precisao: float = 0.05

        # Renomeamento de variaveis
        vdd: float = circuito.vdd
        entradas: list = circuito.entradas

        # Escreve a validacao no arquivo de fontes
        for i in range(len(entradas)):
            entradas[i].sinal = validacao[i]
        HSRunner.configure_input(vdd, entradas)

        # Verifica se as saidas estao na tensao correta pra analise de pulsos
        simulacoes: int = 0
        analise_valida, simulacoes = self.verificar_validacao(circuito, vdd, let)
        if not analise_valida:
            let.corrente = 1111 * simulacoes
            return simulacoes

        tensao_pico: float = 0

        # variaveis da busca binaria da corrente
        csup: float = self.limite_sup
        cinf: float = self.encontrar_corrente_minima(circuito, let)
        # print(cinf)
        # print(f"corrente minima: {cinf}")
        corrente: float = cinf

        # Busca binaria pela falha
        for _ in range(25):

            # Roda o HSPICE e salva os valores no arquivo de texto
            _, tensao_pico = HSRunner.run_SET(circuito.path, circuito.arquivo, let, corrente)
            # print(tensao_pico)

            simulacoes += 1

            # Le a o pico de tensao na saida do arquivo

            ##### ENCERRAMENTOS #####
            if (1 - precisao) * vdd / 2 < tensao_pico < (1 + precisao) * vdd / 2:
                print("LET ENCONTRADO - PRECISAO SATISFEITA\n")
                let.corrente = corrente
                let.append(validacao)
                return simulacoes

            elif csup - cinf < 1:
                # print(f"convergencia: {corrente}")
                if 1 < corrente <self.limite_sup - 1:
                    print("LET ENCONTRADO - CONVERGENCIA\n")
                    let.corrente = corrente
                    let.append(validacao)
                else:
                    print("LET NAO ENCONTRADO - DIVERGENCIA\n")
                    let.corrente = 5555
                return simulacoes

            ##### BUSCA BINARIA #####
            elif let.orientacao[1] == "f":
                if tensao_pico <= (1 - precisao) * vdd / 2:
                    csup = corrente
                elif tensao_pico >= (1 + precisao) * vdd / 2:
                    cinf = corrente
            elif let.orientacao[1] == "r":
                if tensao_pico <= (1 - precisao) * vdd / 2:
                    cinf = corrente
                elif tensao_pico >= (1 + precisao) * vdd / 2:
                    csup = corrente

            corrente: float = float((csup + cinf) / 2)

        if 1 < corrente <self.limite_sup - 1:
            print("LET ENCONTRADO - CICLOS MAXIMOS\n")
            let.corrente = corrente
            let.append(validacao)
        else:
            print("LET NAO ENCONTRADO - CICLOS MAXIMOS\n")
            let.corrente = 3333
        return simulacoes

CircMan = CircuitManager()