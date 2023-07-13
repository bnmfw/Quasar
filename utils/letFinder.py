from .spiceInterface import HSRunner
from .components import LET

# Classe Responsavel por encontrar o valor de um LET
# O Trabalho realizado por esta classe pode ser considerado atomico para os propositos de concorrencia
class LetFinder:
    def __init__(self, circuito, relatorio: bool = False):
        self.circuito = circuito
        self.__relatorio = relatorio
        self.__limite_sup: float = 400
        self.__limite_sim: int = 25

    ##### VERIFICA SE UM LET EH VALIDO #####
    def __verificar_validacao(self, vdd: float, let: LET) -> tuple:
        inclinacao_nodo, inclinacao_saida = let.orientacao
        
        # Checagem se os niveis de tensao estar corretos
        tensao_pico_nodo, tensao_pico_saida = HSRunner.run_SET(self.circuito.path, self.circuito.arquivo, let, 0)

        if (inclinacao_saida == "rise" and tensao_pico_saida > vdd * 0.51) or\
            (inclinacao_saida == "fall" and tensao_pico_saida < vdd * 0.1) or\
            (inclinacao_nodo == "rise" and tensao_pico_nodo > vdd * 0.51) or\
            (inclinacao_nodo == "fall" and tensao_pico_nodo < vdd * 0.1):
            if self.__relatorio: print("Analise invalida - Tensoes improprias\n")
            return (False, 1)

        # Chegagem se o pulso no nodo tem resposta na saída
        tensao_pico_nodo, tensao_pico_saida = HSRunner.run_SET(self.circuito.path, self.circuito.arquivo, let,self.__limite_sup)

        if (inclinacao_saida == "rise" and tensao_pico_saida < vdd * 0.50) or\
            (inclinacao_saida == "fall" and tensao_pico_saida > vdd * 0.50) or\
            (inclinacao_nodo == "rise" and tensao_pico_nodo < vdd * 0.50) or\
            (inclinacao_nodo == "fall" and tensao_pico_nodo > vdd * 0.50):
            if self.__relatorio: print("Analise invalida - Pulso sem efeito\n")
            return (False, 2)

        return (True, 2)

    ##### ENCONTRA A CORRENTE MAXIMA PARA UM LET #####
    def __encontrar_corrente_maxima(self, let:LET) -> float:
        self.__limite_sup = 400

        inclinacao_saida = let.orientacao[1]

        for _ in range(10):
            _, tensao_pico_saida = HSRunner.run_SET(self.circuito.path, self.circuito.arquivo, let, self.__limite_sup)

            # Encontrou efeito
            if (inclinacao_saida == "rise" and tensao_pico_saida > self.circuito.vdd/2) or\
                (inclinacao_saida == "fall" and tensao_pico_saida < self.circuito.vdd/2):
                if self.__relatorio: print(f"PULSO MAXIMO ENCONTRADO ({self.__limite_sup})")
                return self.__limite_sup

            self.__limite_sup += 100
        
        print("Corrente maxima imensa")
        return 800

    ##### ENCONTRA A CORRENTE MINIMA PARA UM LET ######
    def __encontrar_corrente_minima(self, let: LET) -> float:

        # variaveis da busca binaria da corrente
        limite_sup: float = self.__limite_sup
        csup: float = self.__limite_sup
        cinf: float = 0
        corrente: float = (csup + cinf)/2

        # Busca binaria para largura de pulso
        diferenca_largura: float = 100
        precisao_largura: float = 0.05e-9

        # Busca binaria para corrente minima
        for _ in range(self.__limite_sim):
            # Encontra a largura minima de pulso pra vencer o atraso
            largura = HSRunner.run_pulse_width(self.circuito.path, self.circuito.arquivo, let, corrente)
            diferenca_largura: float = None if largura == None else largura - self.circuito.atrasoCC

            # Largura minima satisfeita
            if diferenca_largura and -precisao_largura < diferenca_largura < precisao_largura:
                if self.__relatorio: print(f"PULSO MINIMO ENCONTRADO - PRECISAO SATISFEITA ({corrente})")
                return corrente


            if abs(csup - cinf) < 1:
                if self.__relatorio: print(f"PULSO MINIMO ENCONTRADO - DIFERENCA DE BORDAS PEQUENA ({corrente})")
                return corrente
            if diferenca_largura == None:
                cinf = corrente
            elif diferenca_largura > precisao_largura:
                csup = corrente
            elif diferenca_largura < -precisao_largura:
                cinf = corrente
            corrente = (csup + cinf) / 2

        if self.__relatorio: print(f"PULSO MINIMO NAO ENCONTRADO - LIMITE DE SIMULACOES ATINGIDO")
        return None

    ##### ENCONTRA A CORRENTE DE UM LET ######
    def definir_corrente(self, let: LET, validacao: list, safe: bool = False, delay: bool = False) -> int:
        limite_sup = self.__limite_sup
        precisao: float = 0.05
        simulacoes: int = 0

        # Renomeamento de variaveis
        vdd: float = self.circuito.vdd
        entradas: list = self.circuito.entradas

        # Escreve a validacao no arquivo de fontes
        for i in range(len(entradas)):
            entradas[i].sinal = validacao[i]
        
        with HSRunner.Inputs(vdd, entradas):
            
            # Verifica se as saidas estao na tensao correta pra analise de pulsos
            if not safe:
                analise_valida, simulacoes = self.__verificar_validacao(vdd, let)
                if not analise_valida:
                    let.corrente = None
                    return simulacoes

            # Variaveis da busca binaria da corrente
            csup: float = limite_sup
            cinf: float  = 0
            cinf: float = 0 if not delay else self.__encontrar_corrente_minima(let)
            corrente: float = cinf
            sup_flag: bool = False

            # Busca binaria pela falha
            for i in range(self.__limite_sim):

                # Roda o HSPICE e salva os valores no arquivo de texto
                # try:
                print("Erro no SET: ", let, corrente, validacao)
                _, tensao_pico = HSRunner.run_SET(self.circuito.path, self.circuito.arquivo, let, corrente)
                # except KeyError:                    
                #     exit()
                simulacoes += 1

                ##### ENCERRAMENTO POR PRECISAO SATISFEITA #####
                if (1 - precisao) * vdd / 2 < tensao_pico < (1 + precisao) * vdd / 2:
                    if self.__relatorio: print("LET ENCONTRADO - PRECISAO SATISFEITA\n")
                    let.corrente = corrente
                    let.append(validacao)
                    return simulacoes

                ##### CONVERGENCIA DA CORRENTE ####
                elif csup - cinf < 1:
                    #### CONVERGENIA PARA VALOR EXATO ####
                    if 1 < corrente < limite_sup - 1:
                        if self.__relatorio: print("LET ENCONTRADO - CONVERGENCIA\n")
                        let.corrente = corrente
                        let.append(validacao)
                        return simulacoes
                    #### CONVERGENCIA PARA 0 ####
                    elif corrente <= 1:
                        if self.__relatorio: print("LET NAO ENCONTRADO - DIVERGENCIA NEGATIVA\n")
                        let.corrente = None
                        return simulacoes
                    #### CONVERGENCIA PARA LIMITE SUPERIOR ####
                    else:
                        if self.__relatorio: print("LIMITE SUPERIOR AUMENTADO - DIVERGENCIA POSITIVA\n")
                        csup += 100
                        limite_sup += 100
                        sup_flag = True

                ##### BUSCA BINARIA #####
                elif let.orientacao[1] == "fall":
                    if tensao_pico <= (1 - precisao) * vdd / 2:
                        csup = corrente
                    elif tensao_pico >= (1 + precisao) * vdd / 2:
                        cinf = corrente
                else:
                    if tensao_pico <= (1 - precisao) * vdd / 2:
                        cinf = corrente
                    elif tensao_pico >= (1 + precisao) * vdd / 2:
                        csup = corrente

                corrente: float = float((csup + cinf) / 2)
                # print(f"Corrente: {corrente}")

            #### LIMITE SIMULACOES FEITAS NA BUSCA ATINGIDO ####

            ### CONVERGENCIA PARA VALOR EXATO ###
            if 1 < corrente <self.__limite_sup - 1:
                if self.__relatorio: print("LET ENCONTRADO - LIMITE DE SIMULACOES ATINGIDO\n")
                let.corrente = corrente
                let.append(validacao)
            
            ### DIVERGENCIA ###
            else:
                if self.__relatorio: print("LET NAO ENCONTRADO - LIMITE DE SIMULACOES ATINGIDO\n")
                let.corrente = 99999 if sup_flag else 11111
            return simulacoes