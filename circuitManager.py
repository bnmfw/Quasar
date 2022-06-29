from matematica import combinacoes_possiveis
from runner import HSRunner
from components import *
from arquivos import JManager

class CircuitManager:
    def __init__(self):
        self.circuito = None
        self.__limite_sup: float = 400
        self.__limite_sim: int = 25 
    
    ##### VERIFICA SE UM LET EH VALIDO #####
    def verificar_validacao(self, circuito, vdd: float, let: LET) -> tuple:
        inclinacao_nodo, inclinacao_saida = let.orientacao
        
        # Checagem se os niveis de tensao estar corretos
        tensao_pico_nodo, tensao_pico_saida = HSRunner.run_SET(circuito.path, circuito.arquivo, let, 0)

        if (inclinacao_saida == "rise" and tensao_pico_saida > vdd * 0.51) or\
            (inclinacao_saida == "fall" and tensao_pico_saida < vdd * 0.1) or\
            (inclinacao_nodo == "rise" and tensao_pico_nodo > vdd * 0.51) or\
            (inclinacao_nodo == "fall" and tensao_pico_nodo < vdd * 0.1):
            print("Analise invalida - Tensoes improprias\n")
            return (False, 1)

        # Chegagem se o pulso no nodo tem resposta na saída
        tensao_pico_nodo, tensao_pico_saida = HSRunner.run_SET(circuito.path, circuito.arquivo, let,self.__limite_sup)

        if (inclinacao_saida == "rise" and tensao_pico_saida < vdd * 0.50) or\
            (inclinacao_saida == "fall" and tensao_pico_saida > vdd * 0.50) or\
            (inclinacao_nodo == "rise" and tensao_pico_nodo < vdd * 0.50) or\
            (inclinacao_nodo == "fall" and tensao_pico_nodo > vdd * 0.50):
            print("Analise invalida - Pulso sem efeito\n")
            return (False, 2)

        return (True, 2)

    ##### ENCONTRA A CORRENTE MAXIMA PARA UM LET #####
    def encontrar_corrente_maxima(self, circuito, let:LET) -> float:
        self.__limite_sup = 400

        inclinacao_saida = let.orientacao[1]

        for _ in range(10):
            _, tensao_pico_saida = HSRunner.run_SET(circuito.path, circuito.arquivo, let, self.__limite_sup)

            # Encontrou efeito
            if (inclinacao_saida == "rise" and tensao_pico_saida > circuito.vdd/2) or\
                (inclinacao_saida == "fall" and tensao_pico_saida < circuito.vdd/2):
                print(f"PULSO MAXIMO ENCONTRADO ({self.__limite_sup})")
                return self.__limite_sup

            self.__limite_sup += 100
        
        print("Corrente maxima imensa")
        return 800

    ##### ENCONTRA A CORRENTE MINIMA PARA UM LET ######
    def encontrar_corrente_minima(self, circuito, let: LET) -> float:

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
            largura = HSRunner.run_pulse_width(circuito.path, circuito.arquivo, let, corrente)
            diferenca_largura: float = None if largura == None else largura - circuito.atrasoCC

            # Largura minima satisfeita
            if diferenca_largura and -precisao_largura < diferenca_largura < precisao_largura:
                print(f"PULSO MINIMO ENCONTRADO - PRECISAO SATISFEITA ({corrente})")
                return corrente


            if abs(csup - cinf) < 1:
                print(f"PULSO MINIMO ENCONTRADO - DIFERENCA DE BORDAS PEQUENA ({corrente})")
                return corrente
            if diferenca_largura == None:
                cinf = corrente
            elif diferenca_largura > precisao_largura:
                csup = corrente
            elif diferenca_largura < -precisao_largura:
                cinf = corrente
            corrente = (csup + cinf) / 2

        print(f"PULSO MINIMO NAO ENCONTRADO - LIMITE DE SIMULACOES ATINGIDO")
        return None

    ##### ENCONTRA A CORRENTE DE UM LET ######
    def definir_corrente(self, circuito, let: LET, validacao: list, safe: bool = False) -> int:
        limite_sup = self.__limite_sup
        precisao: float = 0.05
        simulacoes: int = 0

        # Renomeamento de variaveis
        vdd: float = circuito.vdd
        entradas: list = circuito.entradas

        # Escreve a validacao no arquivo de fontes
        for i in range(len(entradas)):
            entradas[i].sinal = validacao[i]
        
        with HSRunner.Inputs(vdd, entradas):
            
            # Verifica se as saidas estao na tensao correta pra analise de pulsos
            if not safe:
                analise_valida, simulacoes = self.verificar_validacao(circuito, vdd, let)
                if not analise_valida:
                    let.corrente = None
                    return simulacoes

            # Variaveis da busca binaria da corrente
            csup: float = limite_sup
            cinf: float = self.encontrar_corrente_minima(circuito, let)
            corrente: float = cinf

            # Busca binaria pela falha
            for _ in range(self.__limite_sim):

                # Roda o HSPICE e salva os valores no arquivo de texto
                _, tensao_pico = HSRunner.run_SET(circuito.path, circuito.arquivo, let, corrente)

                simulacoes += 1

                ##### ENCERRAMENTO POR PRECISAO SATISFEITA #####
                if (1 - precisao) * vdd / 2 < tensao_pico < (1 + precisao) * vdd / 2:
                    print("LET ENCONTRADO - PRECISAO SATISFEITA\n")
                    let.corrente = corrente
                    let.append(validacao)
                    return simulacoes

                ##### CONVERGENCIA DA CORRENTE ####
                elif csup - cinf < 1:
                    #### CONVERGENIA PARA VALOR EXATO ####
                    if 1 < corrente < limite_sup - 1:
                        print("LET ENCONTRADO - CONVERGENCIA\n")
                        let.corrente = corrente
                        let.append(validacao)
                        return simulacoes
                    #### CONVERGENCIA PARA 0 ####
                    elif corrente <= 1:
                        print("LET NAO ENCONTRADO - DIVERGENCIA NEGATIVA\n")
                        let.corrente = None
                        return simulacoes
                    #### CONVERGENCIA PARA LIMITE SUPERIOR ####
                    else:
                        print("LIMITE SUPERIOR AUMENTADO - DIVERGENCIA POSITIVA\n")
                        csup += 100
                        limite_sup += 100

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

            #### LIMITE SIMULACOES FEITAS NA BUSCA ATINGIDO ####

            ### CONVERGENCIA PARA VALOR EXATO ###
            if 1 < corrente <self.__limite_sup - 1:
                print("LET ENCONTRADO - LIMITE DE SIMULACOES ATINGIDO\n")
                let.corrente = corrente
                let.append(validacao)
            
            ### DIVERGENCIA ###
            else:
                print("LET NAO ENCONTRADO - LIMITE DE SIMULACOES ATINGIDO\n")
                let.corrente = None
            return simulacoes

    ##### ENCONTRA O ATRASO DE CAMINHO CRITICO PARA UM CIRCUITO #####
    def get_atrasoCC(self, circuito):
        circuito.atrasoCC = 0
        simulacoes: int = 0

        # Todas as entradas em todas as saidas com todas as combinacoes
        for entrada_analisada in circuito.entradas:
            for saida in circuito.saidas:
                for validacao in combinacoes_possiveis(len(circuito.entradas)):

                    index = 0
                    for entrada in circuito.entradas:
                        if entrada != entrada_analisada:
                            entrada.sinal = validacao[index]
                            index += 1
                    entrada_analisada.sinal = "atraso"

                    # Etapa de medicao de atraso
                    atraso: float = HSRunner.run_delay(circuito.path, circuito.arquivo, entrada_analisada.nome, saida.nome, circuito.vdd, circuito.entradas)

                    simulacoes += 1

                    if atraso > circuito.atrasoCC:
                        circuito.atrasoCC = atraso
        print(f"Atraso CC do arquivo: {circuito.atrasoCC} simulacoes: {simulacoes}")

    ##### ATUALIZA OS LETs DE UM CIRCUITO #####
    def atualizar_LETths(self, circuito, pmos=None, nmos=None):
        with HSRunner.Vdd(circuito.vdd):
            simulacoes: int = 0
            circuito.LETth = None
            ##### BUSCA DO LETs DO CIRCUITO #####
            for nodo in circuito.nodos:
                for let in nodo.LETs:
                    try: 
                        ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                        print(let.nodo_nome, let.saida_nome, let.orientacao, let.validacoes[0])
                        simulacoes += self.definir_corrente(circuito, let, let.validacoes[0], safe=True)
                        print(f"corrente: {let.corrente}\n")
                        if not circuito.LETth:
                            circuito.LETth = let
                        elif let < circuito.LETth: 
                            circuito.LETth = let
                    except KeyboardInterrupt:
                        exit() 
                    except (ValueError, KeyError):
                        with open("erros.txt", "a") as erro:
                            erro.write(f"pmos {pmos} nmos {nmos} {let.nodo_nome} {let.saida_nome} {let.orientacao} {let.validacoes[0]}\n")  
            print(f"{simulacoes} simulacoes feitas na atualizacao")
            JManager.codificar(circuito)

    ##### DETERMINA OS LETs DE UM CIRCUITO #####
    def determinar_LETths(self, circuito):
        for nodo in circuito.nodos:
            nodo.LETs = []
        simulacoes: int = 0
        
        ##### BUSCA DO LETs DO CIRCUITO #####
        for nodo in circuito.nodos:
            for saida in circuito.saidas:
                #### PASSA POR TODAS AS COMBINACOES DE ENTRADA ####
                for validacao in combinacoes_possiveis(len(circuito.entradas)):  

                    ##### DECOBRE OS LETs PARA TODAS AS COBINACOES DE rise E fall #####
                    for combinacao in [[a,b] for a in ["rise", "fall"] for b in ["rise", "fall"]]:

                        ##### ENCONTRA O LETth PARA AQUELA COMBINACAO #####
                        let_analisado = LET(None, circuito.vdd, nodo.nome, saida.nome, combinacao)

                        print(nodo.nome, saida.nome, combinacao[0], combinacao[1], validacao)
                        
                        simulacoes += self.definir_corrente(circuito, let_analisado, validacao)

                        # Nenhum Let encontrado
                        if let_analisado.corrente == None:
                            continue

                        # Atualizacao do LETth do circuito
                        if let_analisado < circuito.LETth:
                            circuito.LETth = let_analisado

                        for let in nodo.LETs:
                            if let == let_analisado:
                                if let_analisado < let:
                                    nodo.LETs.remove(let)
                                    nodo.LETs.append(let_analisado)
                                elif let_analisado.corrente == let.corrente:
                                    let.append(validacao)
                                break
                        else:
                            nodo.LETs.append(let_analisado)

CircMan = CircuitManager()