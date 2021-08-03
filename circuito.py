from arquivos import SpiceManager
from codificador import JsonManager, alternar_combinacao
from matematica import converter_binario, converter_binario_lista, ajustar_valor
from corrente import *
from components import Nodo, Entrada, LET

barra_comprida = "---------------------------"

class Circuito():
    def __init__(self):
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = "nome"
        self.arquivo = "nome.txt"
        self.entradas = []
        self.saidas = []
        self.nodos = []
        self.vdd: float = 0.0
        self.atrasoCC: float = 9999.9

        ##### RELATORIO DO CIRCUITO #####
        self.simulacoes_feitas: int = 0
        self.sets_validos = []
        self.sets_invalidos = []

        ##### MANEJADORES DE ARQUIVOS #####
        self.SM = SpiceManager()
        self.JM = JsonManager()

    def run(self):
        self.__tela_inicial()
        while True:
            self.__tela_principal()


    def __tela_inicial(self):
        # Escolha de dados do circuito
        circuito = input(barra_comprida+"\nEscolha o circuito: ")
        self.nome = circuito
        self.arquivo = self.nome + ".txt"
        try:
            tensao = 0.0
            with open(circuito+".json","r") as teste:
                tensao = float(input(f"{barra_comprida}\nCadastro encontrado\nQual vdd deseja analisar: "))
                self.vdd = tensao
            try:
                with open(f"{circuito}_{tensao}.json","r") as cadastro:
                    print(f"{barra_comprida}\nCadastro com essa tensao encontrado")
                    self.JM.decodificar(self, tensao, True) # LEITURA SIMPLES DO CIRCUITO
            except FileNotFoundError:
                print(f"{barra_comprida}\nCadastro com essa tensao nao encontrado\nGeracao sendo feita")
                self.JM.decodificar(self, tensao, False)
                self.__atualizar_LETths() # ATUALIZACAO DO CIRCUITO

        except FileNotFoundError:
            cadastro = "0"
            while not cadastro in ["y", "n"]:
                cadastro = input(f"{barra_comprida}\nCadastro do circuito nao encontrado\nDeseja gera-lo? (y/n) ")
            if cadastro == "y":
                self.analise_total() # GERA TODOS OS DADOS DO CIRCUITO
            else:
                print(f"{barra_comprida}\nPrograma encerrado")
                exit()

    def __tela_principal(self):
        acao = int(input(f"{barra_comprida}\n"
                     f"Trabalhando com o {self.nome} em {self.vdd} volts\n"
                     "O que deseja fazer?\n"
                     "0. Atualizar LETs\n"
                     "1. Gerar CSV de LETs\n"
                     "2. Analisar LET unico\n"
                     "3. Analise Monte Carlo\n"
                     "5. Sair\n"
                     "Resposta: "))
        if not acao:
            self.__atualizar_LETths()
        elif acao == 1:
            self.__escrever_csv_total()
        elif acao == 2:
            self.analise_manual()
        elif acao == 3:
            self.analise_monte_carlo()
        #elif acao == 4:
        elif acao == 5:
            exit()
        else:
            print("Comando invalido")

    def analise_total(self):
        self.vdd = float(input("vdd: "))
        self.SM.set_vdd(self.vdd)
        self.SM.set_monte_carlo(0)
        #self.__get_atrasoCC()
        self.__determinar_LETths()
        self.JM.codificar(self)

    def analise_tensao_comparativa(self, minvdd, maxvdd):
        self.SM.set_monte_carlo(0)
        lista_comparativa = {}
        while minvdd <= maxvdd + 0.0001:
            LETth_critico = 9999
            self.vdd = minvdd
            self.SM.set_vdd(minvdd)
            self.__determinar_LETths()
            for nodo in self.nodos:
                if nodo.LETth_critico < LETth_critico:
                    LETth_critico = nodo.LETth_critico
            lista_comparativa[str(minvdd)] = LETth_critico
            minvdd += 0.05
        #self.__escrever_csv_comparativo(lista_comparativa)

    def analise_manual(self):
        analise_manual = True
        self.SM.set_monte_carlo(0)
        self.vdd = input("vdd: ")
        self.SM.set_vdd(float(self.vdd))
        nodo, saida = input("nodo e saida analisados: ").split()
        pulso_in, pulso_out = input("pulsos na entrada e saida: ").split()
        nodo = Nodo(nodo)
        saida = Nodo(saida)
        vetor = [int(sinal) for sinal in input("vetor analisado: ").split()]
        current, simulacoes_feitas = definir_corrente(self, pulso_in, pulso_out, nodo, saida, vetor)
        print(f"Corrente final: {current}")

    def analise_monte_carlo(self):
        self.__configurar_LET()
        self.SM.set_monte_carlo(int(input(f"{barra_comprida}\nQuantidade de analises: ")))
        os.system(f"hspice {self.arquivo}| grep \"minout\|maxout\" > texto.txt")
        print("Analise monte carlo realizada com sucesso")

    def __get_atrasoCC(self):
        simulacoes_feitas = 0
        maior_atraso = 0
        for entrada_analisada in self.entradas:
            for saida in self.saidas:
                for i in range(2 ** (len(self.entradas) - 1)):

                    # Atribui o sinal das entradas que nao estao em analise
                    sinais_entrada = converter_binario_lista(i, len(self.entradas)-1)
                    index = 0
                    for entrada in self.entradas:
                        if entrada != entrada_analisada:
                            entrada.sinal = sinais_entrada[index]
                            index += 1
                    entrada_analisada.sinal = "atraso"

                    # SINAIS AQUI OU SAO INTEIROS OU ATRASO

                    # Etapa de medicao de atraso
                    self.SM.set_delay_param(entrada_analisada, saida, self.vdd)
                    self.SM.set_signals(self.vdd, self.entradas)
                    os.system(
                        f"hspice {self.arquivo}| grep \"atraso_rr\|atraso_rf\|atraso_fr\|atraso_ff\|largura\" > texto.txt")
                    simulacoes_feitas += 1
                    atraso = self.SM.get_delay()
                    paridade = 0
                    # if entradaAnalisada.nome == "a":
                    #    print(entradas[0].sinal,entradas[1].sinal,entradas[2].sinal,entradas[3].sinal,entradas[4].sinal)
                    if atraso[0] > atraso[1]: paridade = 1
                    print(atraso)
                    maior_atraso = max(atraso[0 + paridade], atraso[2 + paridade])
                    print(maior_atraso, self.entradas[0].sinal, self.entradas[1].sinal, self.entradas[2].sinal,
                          self.entradas[3].sinal, self.entradas[4].sinal)
                    if maior_atraso > entrada_analisada.atraso[0]:
                        entrada_analisada.atraso[0] = maior_atraso
                        entrada_analisada.atraso[1] = saida
                        entrada_analisada.atraso[1] = [self.entradas[0].sinal,
                                             self.entradas[1].sinal,
                                             self.entradas[2].sinal,
                                             self.entradas[3].sinal,
                                             self.entradas[4].sinal]

                        if maior_atraso > self.atrasoCC: self.atrasoCC = maior_atraso

                print(f"Atraso encontrado para {entrada_analisada.nome} em {saida.nome}")
        print("Atraso CC do arquivo: ", self.atrasoCC)
        return maior_atraso

    def __encontrar_nodo(self, nome):
        for nodo in self.nodos:
            if nodo.nome == nome:
                return nodo
        #Eu nem sei se essa funcao passa dessa linha, mas se nao passar nem importa tambem
        for nodo in self.saidas:
            if nodo.nome == nome:
                return nodo
        for nodo in self.entradas:
            if nodo.nome == nome:
                return nodo

    def __instanciar_nodos(self):
        ##### SAIDAS #####
        saidas = input("saidas: ").split()
        for saida in saidas:
            self.saidas.append(Nodo(saida))

        ##### ENTRADAS #####
        entradas = input("entradas: ").split()
        for entrada in entradas:
            self.entradas.append(Entrada(entrada, "t"))

        ##### OUTROS NODOS #####
        nodos_nomes = list()
        ignorados_true = ["t" + entrada.nome for entrada in self.entradas]
        ignorados_false = ["f" + entrada.nome for entrada in self.entradas]
        with open(self.arquivo, "r") as circuito:
            for linha in circuito:
                if "M" in linha:
                    transistor, coletor, base, emissor, bulk, modelo, nfin = linha.split()
                    for nodo in [coletor, base, emissor]:
                        if nodo not in ["vdd", "gnd", *nodos_nomes, *ignorados_true, *ignorados_false]:
                            nodo = Nodo(nodo)
                            nodos_nomes.append(nodo.nome)
                            for saida in self.saidas:
                                nodo.LETth[saida.nome] = {"rr": [9999, []],
                                                          "rf": [9999, []],
                                                          "fr": [9999, []],
                                                          "ff": [9999, []]}
                                nodo.atraso[saida.nome] = 1111
                            self.nodos.append(nodo)

    def __escolher_validacao(self, validacao):
        if len(validacao) != len(self.entradas): print("VALIDACAO INCOMPATIVEL")
        for indice, entrada in enumerate(self.entradas):
            entrada.sinal = validacao[indice]

    def __configurar_LET(self):
        # Configuracao de pulso
        nodo, saida = input("nodo e saida do LET: ").split()
        pulso_in, pulso_out = input("pulsos na entrada e saida do LET: ").split()
        chave = alternar_combinacao([pulso_in, pulso_out])
        nodo = self.__encontrar_nodo(nodo)
        corrente = nodo.LETth[saida][chave][0]
        saida = self.__encontrar_nodo(saida)
        SR.set_pulse(nodo, corrente, saida, pulso_in)

        # Configuracao do vetor de entrada
        # vetor = [int(sinal) for sinal in input("vetor de entrada do LET (irrelevante pra MC): ").split()]
        # for i in range(len(self.entradas)):
        #     self.entradas[i].sinal = vetor[i]
        # SR.set_signals(self.vdd, self.entradas)

        print("LET configurado com sucesso")

    def __resetar_LETths(self):
        for nodo in self.nodos:
            nodo.validacao = {}
            nodo.LETth_critico = 9999
            for saida in self.saidas:
                nodo.LETth[saida.nome] = {"rr": [9999, []],
                                          "rf": [9999, []],
                                          "fr": [9999, []],
                                          "ff": [9999, []]}
                nodo.validacao[saida.nome] = []
                for entrada in self.entradas:
                    nodo.validacao[saida.nome].append("x")

    def __determinar_LETths(self):
        self.SM.set_monte_carlo(0)
        self.__instanciar_nodos()
        self.__resetar_LETths()
        self.simulacoes_feitas = 0
        self.sets_validos = []
        self.sets_invalidos = []
        ##### BUSCA DO LETth DO CIRCUITO #####
        for nodo in self.nodos:
            for saida in self.saidas:
                ##### FAZ A CONTAGEM DE VARIAVEIS NUMA VALIDACAO  #####
                variaveis = 0
                val = list(nodo.validacao[saida.nome])
                for x in range(len(val)):
                    if val[x] == "x": variaveis += 1
                if variaveis:
                    for k in range(2 ** variaveis):  # PASSA POR TODAS AS COMBINACOES DE ENTRADA

                        final = converter_binario(bin(k), val, variaveis)
                        ##### DECOBRE OS LETth PARA TODAS AS COBINACOES DE rise E fall #####
                        for combinacao in [["rise", "rise"], ["rise", "fall"], ["fall", "fall"], ["fall", "rise"]]:

                            ##### ENCONTRA O LET PARA AQUELA COMBINACAO #####
                            chave = alternar_combinacao(combinacao)  # Faz coisa tipo ["rise","fall"] virar "rf"
                            print(nodo.nome, saida.nome, combinacao[0], combinacao[1], final)
                            current, simulacoes = definir_corrente(self,
                                                                   combinacao[0], combinacao[1], nodo, saida,
                                                                   final)
                            self.simulacoes_feitas += simulacoes

                            # if current < 1111:
                            #     let_analisado = LET(current, self.vdd, nodo.nome, saida.nome, chave)
                            #
                            #     for let in nodo.LETth:
                            #         if let_analisado == let:
                            #             let.validacoes.append(final)
                            #             break
                            #     else:
                            #         nodo.LETth.append(let_analisado)

                            ##### DETERMINA LETth minimo pra aquela saida ####
                            if current < nodo.LETth[saida.nome][chave][0]:
                                ##### SE O LETth EH MENOR DO QUE UM JA EXISTENTE
                                nodo.LETth[saida.nome][chave][0] = current
                                nodo.LETth[saida.nome][chave][1] = [final]

                            elif current == nodo.LETth[saida.nome][chave][0]:
                                ##### SE O LETth EH IGUAL A UM JA EXISTENTE
                                nodo.LETth[saida.nome][chave][1].append(final)

                            if current < nodo.LETth_critico:
                                nodo.LETth_critico = current

                            #### ADMINISTRACAO DE SETS VALIDOS E INVALIDOS PRA DEBUG
                            if current < 1000:
                                self.sets_validos.append(
                                    [nodo.nome, saida.nome, combinacao[0], combinacao[1], current, final])
                                break  # Se ja encontrou a combinacao valida praquela validacao nao tem pq repetir
                            else:
                                self.sets_invalidos.append(
                                    [nodo.nome, saida.nome, combinacao[0], combinacao[1], current, final])

    def __atualizar_LETths(self):
        self.SM.set_monte_carlo(0)
        self.simulacoes_feitas = 0
        ##### BUSCA DO LETth DO CIRCUITO #####
        for nodo in self.nodos:
            for saida in self.saidas:
                ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                for orientacao in nodo.LETth[saida.nome]:
                    if nodo.LETth[saida.nome][orientacao][0] > 1000: pass
                    else:
                        combinacao = alternar_combinacao(orientacao)

                        print(nodo.nome, saida.nome, combinacao[0], combinacao[1], nodo.LETth[saida.nome][orientacao][1][0])
                        nodo.LETth[saida.nome][orientacao][0], simulacoes = definir_corrente(self, combinacao[0],
                                                                                             combinacao[1], nodo, saida,
                                                                                             nodo.LETth[saida.nome][orientacao][1][0])
                        self.simulacoes_feitas += simulacoes
                        if nodo.LETth[saida.nome][orientacao][0] < nodo.LETth_critico:
                            nodo.LETth_critico = nodo.LETth[saida.nome][orientacao][0]

        self.JM.codificar(self)

    def __escrever_csv_total(self):
        linha = 2
        tabela = self.nome + ".csv"
        with open(tabela, "w") as sets:
            sets.write("Nodo,Saida,Pulso,Pulso,Corrente,LETth,Num Val,Validacoes->\n")
            for nodo in self.nodos:
                # print(nodo.LETth)
                for saida in nodo.LETth:
                    for chave, combinacao in zip(["rr", "ff", "rf", "fr"],
                                                 [["rise", "rise"],
                                                  ["fall", "fall"],
                                                  ["rise", "fall"],
                                                  ["fall", "rise"]]):
                        # print(saida, comb, nodo.LETth[saida])
                        if nodo.LETth[saida][chave][0] < 1111:
                            sets.write(nodo.nome + "," + saida + "," + combinacao[0] + "," + combinacao[1] + ",")
                            sets.write(str(nodo.LETth[saida][chave][0]) + ",")
                            sets.write('{:.2e}'.format(
                                (nodo.LETth[saida][chave][0] * 10 ** -6) * (0.000000000164 - (5 * 10 ** -11)) / (
                                        (1.08 * 10 ** -14) * 0.000000021)))
                            sets.write("," + str(len(nodo.LETth[saida][chave][1])))  # Numero de validacoes
                            for validacao in nodo.LETth[saida][chave][1]:
                                sets.write(",'")
                                for num in validacao:
                                    sets.write(str(num))
                            sets.write("\n")
                            linha += 1
        print(f"\nTabela {tabela} gerada com sucesso\n")

    def __escrever_csv_comparativo(self, lista_comparativa):
        with open(f"{self.nome}_compara.csv", "w") as tabela:
            for chave in lista_comparativa:
                tabela.write(chave + "," + "{:.2f}".format(lista_comparativa[chave]) + "\n")

        print(f"\nTabela {self.nome}_compara.csv" + " gerada com sucesso\n")
