from arquivos import *
from matematica import converter_binario, converter_binario_lista, ajustar_valor
from corrente import *
import json

class Entrada():
    def __init__(self, nome, sinal):
        self.nome = nome
        self.sinal = sinal
        self.atraso = [0, "saida.nome", ["Vetor de validacao"]]


class Nodo():
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
        self.LETth_critico = 9999
        self.atraso = {}


class Circuito():
    def __init__(self, nome):
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = nome
        self.arquivo = self.nome + ".txt"
        self.entradas = []
        self.saidas = []
        self.nodos = []
        self.vdd = 0
        self.atrasoCC = 0

        ##### RELATORIO DO CIRCUITO #####
        self.simulacoes_feitas = 0
        self.sets_validos = []
        self.sets_invalidos = []

        ##### MONTAGEM DO CIRCUITO #####
        self.__instanciar_nodos()

    def analise_total(self, vdd):
        self.vdd = vdd
        SR.set_vdd(vdd)
        SR.set_monte_carlo(0)
        #self.__get_atrasoCC()
        self.__ler_validacao()
        self.__determinar_LETths()
        self.__gerar_relatorio_csv()
        self.__codificar_para_json()

    def analise_tensao_comparativa(self, minvdd, maxvdd):
        SR.set_monte_carlo(0)
        self.__ler_validacao()
        lista_comparativa = {}
        while minvdd <= maxvdd + 0.0001:
            LETth_critico = 9999
            self.vdd = minvdd
            SR.set_vdd(minvdd)
            self.__determinar_LETths()
            for nodo in self.nodos:
                if nodo.LETth_critico < LETth_critico:
                    LETth_critico = nodo.LETth_critico
            lista_comparativa[str(minvdd)] = LETth_critico
            minvdd += 0.05
        self.__escrever_csv_comparativo(lista_comparativa)

    def analise_manual(self):
        analise_manual = True
        SR.set_monte_carlo(0)
        self.vdd = input("vdd: ")
        SR.set_vdd(float(self.vdd))
        nodo, saida = input("nodo e saida analisados: ").split()
        pulso_in, pulso_out = input("pulsos na entrada e saida: ").split()
        nodo = Nodo(nodo)
        saida = Nodo(saida)
        vetor = [int(sinal) for sinal in input("vetor analisado: ").split()]
        current, simulacoes_feitas = definir_corrente(self, pulso_in, pulso_out,
                                                      nodo, saida, vetor)
        print("Corrente final: " + str(current))

    def analise_monte_carlo(self):
        # self.vdd = input("vdd: ")
        # SR.set_vdd(float(self.vdd))
        SR.set_monte_carlo(10)
        os.system("hspice " + self.arquivo)

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
                    SR.set_delay_param(entrada_analisada, saida, self.vdd)
                    SR.set_signals(self.vdd, self.entradas)
                    os.system(
                        "hspice " + self.arquivo + " | grep \"atraso_rr\|atraso_rf\|atraso_fr\|atraso_ff\|largura\" > texto.txt")
                    simulacoes_feitas += 1
                    atraso = SR.get_delay()
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

                print("Atraso encontrado para " + entrada_analisada.nome + " em " + saida.nome)
        print("Atraso CC do arquivo: ", self.atrasoCC)
        return maior_atraso

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

    def __resetar_LETths(self):
        for nodo in self.nodos:
            nodo.LETth_critico = 9999
            for saida in self.saidas:
                nodo.LETth[saida.nome] = {"rr": [9999, []],
                                          "rf": [9999, []],
                                          "fr": [9999, []],
                                          "ff": [9999, []]}

    # Le a validacao de um arquivo
    def __ler_validacao(self):
        arq_validacao = "val" + self.arquivo
        linhas = list()
        # Leitura das linhas
        # try:
        #     with open(arq_validacao, "r") as arquivo:
        #         for linha in arquivo:
        #             linhas.append(linha)
        #     atraso = float(linhas[0].split()[1]) * 10 ** -12
        #     for nodo in self.nodos:
        #         validacao = {}
        #         for linha in linhas:
        #             nome, resto = linha.split(" ", 1)
        #             if nome == nodo.nome:
        #                 sinais_de_entrada = resto.split()
        #                 for saida in self.saidas:
        #                     sinais_de_entrada.remove(saida.nome)
        #                 sinais_de_entrada_1 = sinais_de_entrada[:5]
        #                 for i in range(len(sinais_de_entrada_1)):
        #                     try:
        #                         sinais_de_entrada_1[i] = int(sinais_de_entrada_1[i])
        #                     except ValueError:
        #                         pass
        #                 validacao[self.saidas[0].nome] = sinais_de_entrada_1
        #                 sinais_de_entrada_2 = sinais_de_entrada[-5:]
        #                 # Conversao de string pra inteiro
        #                 for i in range(len(sinais_de_entrada_2)):
        #                     try:
        #                         sinais_de_entrada_2[i] = int(sinais_de_entrada_2[i])
        #                     except ValueError:
        #                         pass
        #                 validacao[self.saidas[1].nome] = sinais_de_entrada_2
        #                 break
        #         # FAILSAFE QUE TEM QUE ARRUMAR DEPOIS
        #         # if not len(validacao):
        #         #     for saida in saidas:
        #         #         validacao.append([saida.nome, ["x", "x", "x", "x", "x"]])
        #         nodo.validacao = validacao
        # except FileNotFoundError:
        print(len(self.nodos))
        print(len(self.saidas))
        print(len(self.entradas))
        for nodo in self.nodos:
            nodo.validacao = {}
            for saida in self.saidas:
                nodo.validacao[saida.nome] = []
                for entrada in self.entradas:
                    nodo.validacao[saida.nome].append("x")
        #return None

        #self.atrasoCC = atraso

    def __determinar_LETths(self):
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

                            ##### ENCONTRA O LETth PARA AQUELA COMBINACAO #####
                            chave = combinacao[0][0] + combinacao[1][0]  # Faz coisa tipo ["rise","fall"] virar "rf"
                            print(nodo.nome, saida.nome, combinacao[0], combinacao[1], final)
                            current, simulacoes = definir_corrente(self,
                                                                   combinacao[0], combinacao[1], nodo, saida,
                                                                   final)
                            self.simulacoes_feitas += simulacoes

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

    def __gerar_relatorio_csv(self):
        for sets in self.sets_validos: print(sets)
        print("\n")
        for sets in self.sets_invalidos: print(sets)

        print("\n1111-SET invalidado em analise de tensao")
        print("2222-SET invalidado em analise de pulso")
        print("3333-SET Passou validacoes anteriores mas foi mal concluido")
        print("4444-SET invalidado em validacao de largura de pulso")
        print("5555-SET Aproximou indeterminadamente de um limite")

        # Retorno do numero de simulacoes feitas e de tempo de execucao
        print("\n" + str(self.simulacoes_feitas) + " simulacoes feitas\n")
        # for nodo in self.nodos:
        #     for saida in nodo.LETth:
        #         for orientacao in nodo.LETth[saida]:
        #             pass
        self.__escrever_csv_total()

    def __escrever_csv_total(self):
        linha = 2
        tabela = self.nome + ".csv"
        with open(tabela, "w") as sets:
            sets.write("Nodo,Saida,Pulso,Pulso,Corrente,LETth,Num Val,Validacoes->\n")
            for nodo in self.nodos:
                print(nodo.LETth)
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
        print("\nTabela " + tabela + " gerada com sucesso\n")

    def __escrever_csv_comparativo(self, lista_comparativa):
        with open(self.nome + "_compara.csv", "w") as tabela:
            for chave in lista_comparativa:
                tabela.write(chave + "," + "{:.2f}".format(lista_comparativa[chave]) + "\n")

        print("\nTabela " + self.nome + "_compara.csv" + " gerada com sucesso\n")

    def __codificar_para_json(self):
        #Codificacao dos nodos
        dicionario_de_nodos = {} #criacao do dicionario que tera o dicionario de todos os nodos
        for nodo in self.nodos:
            este_nodo = {} #dicionario contendo as informacoes deste nodo
            este_nodo["nome"] = nodo.nome
            este_nodo["validacao"] = nodo.validacao
            este_nodo["LETth"] = nodo.LETth
            este_nodo["LETth_critico"] = nodo.LETth_critico
            este_nodo["atraso"] = nodo.atraso
            dicionario_de_nodos[nodo.nome] = este_nodo

        #Codificacao de entradas
        lista_de_saidas = []
        for saida in self.saidas:
            lista_de_saidas.append(saida.nome)

        #Codificacao de saidas
        lista_de_entradas = []
        for entrada in self.entradas:
            lista_de_entradas.append(entrada.nome)

        circuito_codificado = {}
        circuito_codificado["nome"] = self.nome
        circuito_codificado["entradas"] = lista_de_entradas
        circuito_codificado["saidas"] = lista_de_saidas
        circuito_codificado["nodos"] = dicionario_de_nodos
        circuito_codificado["vdd"] = self.vdd
        circuito_codificado["atrasoCC"] = self.atrasoCC

        json.dump(circuito_codificado, open(self.nome+".json","w"))