from matematica import combinacoes_possiveis
from runner import HSRunner
from components import *
from arquivos import CManager
import json

barra_comprida = "---------------------------"

class CircuitManager:
    def __init__(self):
        self.circuito = None
        self.__limite_sup: float = 400
        self.__limite_sim: int = 25

        # Estado de simulacoes MC
        self.em_analise: bool = False
        self.__num_analises: int = None
        self.__atual: int = None
        self.__var: dict = None
    
    ##### DESCARREGA O CONTEXTO DAS SIMULACOES DA ANALISE MC #####
    def __dump_MC(self, saida, circuito):
        estado: dict = {"analise": self.em_analise, 
                        "num": self.__num_analises, 
                        "atual": self.__atual, 
                        "var": self.__var,
                        "saida": saida}
        json.dump(estado, open(f"circuitos/{circuito.nome}/MC_context.json", "w"))

    ##### CARREGA O CONTEXTO DAS SIMULACOES DA ANALISE MC #####
    def __load_MC(self, circuito):
        estado: dict = json.load(open(f"circuitos/{circuito.nome}/MC_context.json", "r"))
        self.em_analise = estado["analise"]
        self.__num_analises = estado["num"]
        self.__atual = estado["atual"]
        self.__var = estado["var"]
        return estado["saida"]
    
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
    def definir_corrente(self, circuito, let: LET, validacao: list, safe: bool = False, delay: bool = False) -> int:
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
            cinf: float  = 0
            cinf: float = 0 if not delay else self.encontrar_corrente_minima(circuito, let)
            corrente: float = cinf
            sup_flag: bool = False

            # Busca binaria pela falha
            for i in range(self.__limite_sim):

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
                print("LET ENCONTRADO - LIMITE DE SIMULACOES ATINGIDO\n")
                let.corrente = corrente
                let.append(validacao)
            
            ### DIVERGENCIA ###
            else:
                print("LET NAO ENCONTRADO - LIMITE DE SIMULACOES ATINGIDO\n")
                let.corrente = 99999 if sup_flag else 11111
            return simulacoes

    ##### ENCONTRA O ATRASO DE CAMINHO CRITICO PARA UM CIRCUITO #####
    def get_atrasoCC(self, circuito):
        entrada_critica = None
        saida_critica = None
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
                        saida_critica = saida.nome
                        entrada_critica = entrada.nome
        # with open("atrasoCC.txt", "a") as arq:
        #     arq.write(f"entada: {entrada_critica}\t saida: {saida_critica}\n")
        print(f"Atraso CC do arquivo: {circuito.atrasoCC} simulacoes: {simulacoes}")

    ##### ATUALIZA OS LETs DE UM CIRCUITO #####
    def atualizar_LETths(self, circuito, pmos=None, nmos=None, delay: bool = False):
        with HSRunner.Vdd(circuito.vdd):
            simulacoes: int = 0
            circuito.LETth = None
            ##### BUSCA DO LETs DO CIRCUITO #####
            for nodo in circuito.nodos:
                for let in nodo.LETs:
                    # try: 
                    ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                    print(let.nodo_nome, let.saida_nome, let.orientacao, let.validacoes[0])
                    simulacoes += self.definir_corrente(circuito, let, let.validacoes[0], safe=True, delay=delay)
                    print(f"corrente: {let.corrente}\n")
                    if not circuito.LETth:
                        circuito.LETth = let
                    elif let < circuito.LETth: 
                        circuito.LETth = let
                    # except KeyboardInterrupt:
                    #     exit() 
                    # except (ValueError, KeyError):
                    #     with open("erros.txt", "a") as erro:
                    #         erro.write(f"pmos {pmos} nmos {nmos} {let.nodo_nome} {let.saida_nome} {let.orientacao} {let.validacoes[0]}\n")  
            print(f"{simulacoes} simulacoes feitas na atualizacao")

    ##### DETERMINA OS LETs DE UM CIRCUITO #####
    def determinar_LETths(self, circuito, delay: bool = False):
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
                        
                        simulacoes += self.definir_corrente(circuito, let_analisado, validacao, delay = delay)

                        # Nenhum Let encontrado
                        if let_analisado.corrente == None:
                            continue

                        # Atualizacao do LETth do circuito
                        if circuito.LETth is None or let_analisado < circuito.LETth:
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
                            if let_analisado < 10000:
                                nodo.LETs.append(let_analisado)

    ##### INICIA A VARIABILIDADE PARA A ANALISE MC ####
    def __determinar_variabilidade(self, circuito):
        num_analises = int(input(f"{barra_comprida}\nQuantidade de analises: "))
        print("Gerando instancias MC")
        var: dict = HSRunner.run_MC_var(circuito.path, circuito.arquivo, circuito.nome, num_analises)

        for i in var:
            var[i][0] = 4.8108 + var[i][0] * (0.05 * 4.8108)/3
            var[i][1] = 4.372 + var[i][1] * (0.05 * 4.372)/3

        # Estado do manejador
        self.em_analise = True
        self.__num_analises = num_analises
        self.__var = var
        self.__atual = 0
        self.__dump_MC(None, circuito)
    
    ##### REALIZA A ANALISE MONTE CARLO TOTAL #####
    def analise_monte_carlo_total(self, circuito, delay:bool = False):
        
        ## Gera o arquivo caso nao exista ##
        try:
            self.__load_MC(circuito)
        except FileNotFoundError:
            self.__dump_MC(None, circuito)
        
        ### Carregamento ou nao de simulacoes
        if not self.em_analise:
            print("Encontrando LETth para cada instancia")
            self.__determinar_variabilidade(circuito)
            saida: dict = {"indice": ("pmos", "nmos", "nodo", "saida", "corrente", "LETth")}
        else:
            print("\nSimulacao em andamento encontrada! continuando de onde parou...\n")
            saida = self.__load_MC(circuito)

        # ### Arquivo com controle de errosS
        # with open("erros.txt", "a") as erro: erro.write(f"\nErros do circuito: {circuito.nome}\n")

        for i, (pmos, nmos) in self.__var.items():
            ### Guarda que com ctz tem como melhorar
            if int(i) <= int(self.__atual): continue
            if int(i) > int(self.__num_analises): break

            print(f"index: {i} pmos: {pmos} nmos: {nmos}")
            
            self.__atual = i

            with HSRunner.MC_Instance(pmos, nmos):
                if delay: CircMan.get_atrasoCC(circuito)
                CircMan.atualizar_LETths(circuito, pmos, nmos, delay=delay)
                saida[i] = (round(pmos,4), round(nmos,4), circuito.LETth.nodo_nome, circuito.LETth.saida_nome, circuito.LETth.corrente, circuito.LETth.valor)
                self.__dump_MC(saida, circuito)

        CManager.tup_dict_to_csv(circuito.path,f"{circuito.nome}_mc_LET.csv", saida)
        print("Pontos da analise Monte Carlo gerados com sucesso")

        self.em_analise = False
        self.__var = None
        self.__dump_MC(None, circuito)

CircMan = CircuitManager()