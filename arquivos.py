import os
import time

analise_manual = False

class ManejadorArquivo():
    def __init__(self):
        pass

    # Escreve vdd no arquivo "vdd.txt"
    def set_vdd(self, vdd):
        with open("vdd.txt", "w") as arquivo_vdd:
            arquivo_vdd.write("*Arquivo com a tensao usada por todos os circuitos\n")
            arquivo_vdd.write("Vvdd vdd gnd " + str(vdd) + "\n")
            arquivo_vdd.write("Vvcc vcc gnd " + str(vdd) + "\n")
            arquivo_vdd.write("Vclk clk gnd PULSE(0 " + str(vdd) + " 1n 0.01n 0.01n 1n 2n)")

    # Escreve os sinais no arquivo "fontes.txt"
    def set_signals(self, vdd, entradas):
        with open("fontes.txt", "w") as sinais:
            sinais.write("*Fontes de sinal a serem editadas pelo roteiro\n")

            #Escreve o sinal analogico a partir do sinal logico
            for i in range(len(entradas)):
                sinais.write("V" + entradas[i].nome + " " + entradas[i].nome + " gnd ")
                if entradas[i].sinal == 1: sinais.write(str(vdd) + "\n")
                elif entradas[i].sinal == 0: sinais.write("0.0\n")
                elif entradas[i].sinal == "atraso":
                    sinais.write("PWL(0n 0 1n 0 1.01n " + str(vdd) + " 3n " + str(vdd) + " 3.01n 0)\n")
                else:
                    print("ERRO SINAL NAO IDENTIFICADO RECEBIDO: ", entradas[i].sinal)

    # Escreve informacoes no arquivo "SETs.txt"
    def set_pulse(self, nodo, corrente, saida, direcao_pulso_nodo):
        with open("SETs.txt", "w") as sets:
            sets.write("*SETs para serem usados nos benchmarks\n")
            if direcao_pulso_nodo == "fall": sets.write("*")
            sets.write("Iseu gnd " + nodo.nome + " EXP(0 " + str(corrente) + "u 2n 50p 164p 200p) //rise\n")
            if direcao_pulso_nodo == "rise": sets.write("*")
            sets.write("Iseu " + nodo.nome + " gnd EXP(0 " + str(corrente) + "u 2n 50p 164p 200p) //fall\n")
            sets.write(".meas tran minout min V(" + saida.nome + ") from=1.0n to=4.0n\n")
            sets.write(".meas tran maxout max V(" + saida.nome + ") from=1.0n to=4.0n\n")
            # Usado apenas na verificacao de validacao:
            sets.write(".meas tran minnod min V(" + nodo.nome + ") from=1.0n to=4.0n\n")
            sets.write(".meas tran maxnod max V(" + nodo.nome + ") from=1.0n to=4.0n\n")

    # Altera o arquivo "atraso.txt"
    def set_delay_param(self, entrada, saida, vdd):
        with open("atraso.txt", "w") as atraso:
            atraso.write("*Arquivo com atraso a ser medido\n")
            tensao = str(vdd * 0.5)
            saida = saida.nome
            atraso.write(
                ".meas tran atraso_rr TRIG v(" + entrada.nome + ") val='" + tensao + "' rise=1 TARG v(" + saida + ") val='" + tensao + "' rise=1\n")
            atraso.write(
                ".meas tran atraso_rf TRIG v(" + entrada.nome + ") val='" + tensao + "' rise=1 TARG v(" + saida + ") val='" + tensao + "' fall=1\n")
            atraso.write(
                ".meas tran atraso_ff TRIG v(" + entrada.nome + ") val='" + tensao + "' fall=1 TARG v(" + saida + ") val='" + tensao + "' fall=1\n")
            atraso.write(
                ".meas tran atraso_fr TRIG v(" + entrada.nome + ") val='" + tensao + "' fall=1 TARG v(" + saida + ") val='" + tensao + "' rise=1\n")
            atraso.write(
                ".meas tran largura TRIG v(" + saida + ") val='" + tensao + "' fall=1 TARG v(" + saida + ") val='" + tensao + "' rise=1\n")

    # Le a resposta do pulso no arquivo "texto.txt"
    def get_peak_tension(self, direcao_pulso_saida, offset):
        linha_texto = list(range(4))
        tensao_pico = 3333
        with open("texto.txt", "r") as text:
            if offset:
                linha_texto[0] = text.readline()
                linha_texto[1] = text.readline()

            linha_texto[0 + offset] = text.readline()
            linha_de_tensao = linha_texto[0 + offset].split()
            if len(linha_de_tensao[0]) != 7:
                min_tensao = linha_de_tensao[0][7:]
            else:
                min_tensao = linha_de_tensao[1]

            linha_texto[1 + offset] = text.readline()
            linha_de_tensao = linha_texto[1 + offset].split()
            if len(linha_de_tensao[0]) != 7:
                max_tensao = linha_de_tensao[0][7:]
            else:
                max_tensao = linha_de_tensao[1]

        # Converte as strings lidas em floats
        max_tensao = ajustar_valor(max_tensao)
        min_tensao = ajustar_valor(min_tensao)
        if analise_manual: print("Tensao max: " + str(max_tensao) + " Tensao min: " + str(min_tensao))

        # Identifica se o pico procurado e do tipo rise ou fall
        if direcao_pulso_saida == "rise":
            tensao_pico = max_tensao
        elif direcao_pulso_saida == "fall":
            tensao_pico = min_tensao
        else:
            print("ERRO: O TIPO DE PULSO NAO FOI IDENTIFICADO")

        # retorna a tensao de pico lida
        return tensao_pico

    # Le o atraso do nodo a saida no arquivo "texto.txt"
    def get_delay(self):
        linhas_de_atraso = list()
        atrasos = list()  # 0 rr, 1 rf, 2 ff, 3 fr
        with open("texto.txt", "r") as text:
            # Leitura das 4 linhas com atraso
            for i in range(4):
                linhas_de_atraso.append(text.readline().split())
                if linhas_de_atraso[i][0][0] == "*":
                    # print(linhas_de_atraso[i][0])
                    return [0, 0, 0, 0]

                atrasos.append(linhas_de_atraso[i][1])  # salva os 4 atrasos
                atrasos[i] = ajustar_valor(atrasos[i])
            linhas_de_atraso.append(text.readline().split())
            largura_pulso_saida = linhas_de_atraso[4][1]
            largura_pulso_saida = abs(ajustar_valor(largura_pulso_saida))
            if largura_pulso_saida < 1 * 10 ** -9:  # Largura de pulso menor que 1 nanosegundo
                # print("Pulso menor que 1 nano",largura_pulso_saida)
                return [0, 0, 0, 0]
        return atrasos

    # Leitura do arquivo "leitura_pulso.txt"
    def get_pulse_delay_validation(self):
        with open("texto.txt", "r") as texto:
            atraso = texto.readline().split()
            larg = texto.readline().split()
        # if analise_manual: print(atraso)
        if atraso[0][0] == "*":
            return "pulso_muito_pequeno"  # pulso muito pequeno
        if "-" in atraso[0]:
            atraso = atraso[0].split("-")
        atraso = ajustar_valor(atraso[1])

        if larg[0][0] == "*":
            return "pulso_muito_pequeno"  # pulso muito pequeno
        if "-" in larg[0]:
            larg = larg[0].split("-")
        larg = ajustar_valor(larg[1])
        return larg - atraso

MA = ManejadorArquivo()

def converter_binario(binario, validacao, variaveis):  # Converte o binario esquisito numa lista
    final = list(validacao)
    flag = 0
    binary = list()
    # Transforma binario em uma lista de verdade e ajusta a validacao
    for i in range(variaveis - (len(binario) - 2)): binary.append(0)
    for i in range(len(binario) - 2): binary.append(int(binario[i + 2]))
    for i in range(len(final)):
        if final[i] == "x":
            final[i] = binary[flag]
            flag += 1
    return final

# Esta funcao recebe uma sting do tipo numeroEscala como 10.0p ou 24.56m e retorna um float ajustando as casas decimais
def ajustar_valor(tensao):
    grandeza = 0
    if tensao[-1] == "m":
        grandeza = -3
    elif tensao[-1] == "u":
        grandeza = -6
    elif tensao[-1] == "n":
        grandeza = -9
    elif tensao[-1] == "p":
        grandeza = -12
    elif tensao[-1] == "f":
        grandeza = -15
    tensao = tensao[:-1]
    tensao = float(tensao)
    tensao = tensao * 10 ** grandeza
    return tensao

# Funcao que verifica se aquela analise de radiacao eh valida (ou seja, se tem o efeito desejado na saida)
def verificar_validacao(circuito, nodo, direcao_pulso_nodo, saida, direcao_pulso_saida, vdd):
    MA.set_pulse(nodo, 0.0, saida, direcao_pulso_nodo)
    print("Verificacao de tensao: ", end='')
    os.system("hspice " + circuito + " | grep \"minout\|maxout\|minnod\|maxnod\" > texto.txt")
    tensao_pico_saida = MA.get_peak_tension(direcao_pulso_saida, 0)
    tensao_pico_nodo = MA.get_peak_tension(direcao_pulso_nodo, 2)

    if analise_manual:
        print("Verificacao de Sinal: Vpico nodo: " + str(tensao_pico_nodo) + " Vpico saida: " + str(
            tensao_pico_saida) + "\n")

    # Leitura sem pulso
    if direcao_pulso_saida == "rise" and tensao_pico_saida > vdd * 0.51: return [False, 1]
    elif direcao_pulso_saida == "fall" and tensao_pico_saida < vdd * 0.1: return [False, 1]
    elif direcao_pulso_nodo == "rise" and tensao_pico_nodo > vdd * 0.51: return [False, 1]
    elif direcao_pulso_nodo == "fall" and tensao_pico_nodo < vdd * 0.1: return [False, 1]

    MA.set_pulse(nodo, 499.0, saida, direcao_pulso_nodo)
    print("Verificacao de pulso: ", end='')
    os.system("hspice " + circuito + " | grep \"minout\|maxout\|minnod\|maxnod\" > texto.txt")
    tensao_pico_saida = MA.get_peak_tension(direcao_pulso_saida, 0)
    tensao_pico_nodo = MA.get_peak_tension(direcao_pulso_nodo, 2)
    if analise_manual:
        print("Verificacao de Pulso: Vpico nodo: " + str(tensao_pico_nodo) + " Vpico saida: " + str(
            tensao_pico_saida) + "\n")
    # Leitura com pulso
    if direcao_pulso_saida == "rise" and tensao_pico_saida < vdd * 0.50:
        return [False, 2]
    elif direcao_pulso_saida == "fall" and tensao_pico_saida > vdd * 0.50:
        return [False, 2]
    elif direcao_pulso_nodo == "rise" and tensao_pico_nodo < vdd * 0.50:
        return [False, 2]
    elif direcao_pulso_nodo == "fall" and tensao_pico_nodo > vdd * 0.50:
        return [False, 2]

    return [True, 2]

# Altera o arquivo "largura_pulso.txt"
def escrever_largura_pulso(nodo, saida, vdd, dir_nodo, dir_saida):
    with open("largura_pulso.txt", "w") as larg:
        larg.write("*Arquivo com a leitura da largura dos pulsos\n")
        tensao = str(vdd * 0.5)
        larg.write(
            ".meas tran atraso TRIG v("+nodo+") val='"+tensao+"' "+dir_nodo+"=1 TARG v("+saida+") val='"+tensao+"' "+dir_saida+"=1\n"
            ".meas tran larg TRIG v("+nodo+") val='"+tensao+"' rise=1 TARG v("+nodo+") val='"+tensao+"' fall=1\n")

def largura_pulso(circuito, nodo, nodo_saida, vdd, corrente, direcao_pulso_nodo, direcao_pulso_saida):  ##### REALIZA A MEDICAO DE LARGURA DE PULSO #####
    escrever_largura_pulso(nodo.nome, nodo_saida.nome, vdd, direcao_pulso_nodo, direcao_pulso_saida)  # Determina os parametros no arquivo de leitura de largura de pulso
    MA.set_pulse(nodo, corrente, nodo_saida, direcao_pulso_nodo)
    os.system("hspice " + circuito + " | grep \"atraso\|larg\" > texto.txt")
    return MA.get_pulse_delay_validation()

def encontrar_corrente_minima(circuito, vdd, nodo, saida, direcao_pulso_nodo, direcao_pulso_saida):
    # variaveis da busca binaria da corrente
    corrente_sup = 500
    corrente = 499
    corrente_inf = 0
    corrente_anterior = 0

    # Reseta os valores no arquivo de radiacao. (Se nao fizer isso o algoritmo vai achar a primeira coisa como certa)
    MA.set_pulse(nodo, corrente, saida, direcao_pulso_nodo)

    # Busca binaria para largura de pulso
    diferenca_largura = 100
    precisao_largura = 0.05
    precisao_largura = precisao_largura * 10 ** -9
    while (diferenca_largura == "pulso_muito_pequeno") or not (
            -precisao_largura < diferenca_largura < precisao_largura):
        #
        diferenca_largura = largura_pulso(circuito, nodo, saida, vdd, corrente, direcao_pulso_nodo, direcao_pulso_saida)
        if abs(corrente - corrente_anterior) < 5:
            print("PULSO MINIMO ENCONTRADO")
            return corrente
        elif diferenca_largura == "pulso_muito_pequeno":  # Caso que o pulso foi tao pequeno que o atraso sequer foi medido
            corrente_inf = corrente
        elif diferenca_largura > precisao_largura:
            corrente_sup = corrente
        elif diferenca_largura < -precisao_largura:
            corrente_inf = corrente
        corrente_anterior = corrente
        corrente = float((corrente_sup + corrente_inf) / 2)

    print("PULSO MINIMO ENCONTRADO")
    return corrente

def definir_corrente(circuito, vdd, entradas, direcao_pulso_nodo, direcao_pulso_saida, nodo, saida, validacao):

    precisao = 0.05

    # Escreve a validacao no arquivo de fontes
    for i in range(len(entradas)):
        entradas[i].sinal = validacao[i]
    MA.set_signals(vdd, entradas)

    # Verifica se as saidas estao na tensao correta pra analise de pulsos
    analise_valida, simulacoes_feitas = verificar_validacao(circuito, nodo, direcao_pulso_nodo, saida,
                                                            direcao_pulso_saida, vdd)
    if not analise_valida:
        if simulacoes_feitas == 1:
            print("Analise invalida - Tensoes improprias\n")
        elif simulacoes_feitas == 2:
            print("Analise invalida - Pulso sem efeito\n")
        else:
            print("Analise invalida - WTF?\n")
        return [1111 * simulacoes_feitas, simulacoes_feitas]

    tensao_pico = 0

    # variaveis da busca binaria da corrente
    corrente_sup = 500
    corrente_inf = encontrar_corrente_minima(circuito, vdd, nodo, saida, direcao_pulso_nodo, direcao_pulso_saida)
    corrente = corrente_inf

    # Busca binaria para dar bit flip
    while not ((1 - precisao) * vdd / 2 < tensao_pico < (1 + precisao) * vdd / 2):

        # Roda o HSPICE e salva os valores no arquivo de texto
        os.system("hspice " + circuito + " | grep \"minout\|maxout\" > texto.txt")
        simulacoes_feitas += 1

        # Le a o pico de tensao na saida do circuito
        tensao_pico = MA.get_peak_tension(direcao_pulso_saida, 0)

        if analise_manual:
            print("Corrente testada: " + str(corrente) + " Resposta na saida: " + str(tensao_pico) + "\n")

        # Encerramento por excesso de simulacoes
        if simulacoes_feitas >= 25:
            if 1 < corrente < 499:
                print("Encerramento por estouro de ciclos maximos - Corrente encontrada\n")
                return [corrente, simulacoes_feitas]
            else:
                print("Encerramento por estouro de ciclos maximos - Corrente nao encontrada\n")
                return [3333, simulacoes_feitas]

        # Encerramento por precisao satisfatoria
        elif corrente_sup-corrente_inf < 1:
            if 1 < corrente < 499:
                print("Corrente encontrada - Aproximacao nao convencional\n")
                return [corrente, simulacoes_feitas]
            else:
                print("Corrente nao encontrada - Aproximacao extrema\n")
                return [5555, simulacoes_feitas]

        # Busca binaria
        elif direcao_pulso_saida == "fall":
            if tensao_pico <= (1 - precisao) * vdd / 2:
                corrente_sup = corrente
            elif tensao_pico >= (1 + precisao) * vdd / 2:
                corrente_inf = corrente
            else:
                print("Corrente encontrada com sucesso\n")
                return [corrente, simulacoes_feitas]
        elif direcao_pulso_saida == "rise":
            if tensao_pico <= (1 - precisao) * vdd / 2:
                corrente_inf = corrente
            elif tensao_pico >= (1 + precisao) * vdd / 2:
                corrente_sup = corrente
            else:
                print("Corrente encontrada com sucesso\n")
                return [corrente, simulacoes_feitas]

        corrente = float((corrente_sup + corrente_inf) / 2)

        # Escreve os parametros no arquivo dos SETs
        MA.set_pulse(nodo, corrente, saida, direcao_pulso_nodo)


class Entrada():
    def __init__(self, nome, sinal):
        self.nome = nome
        self.sinal = sinal
        self.atraso = [0, "saida.nome", ["Vetor de validacao"]]


class Nodo():
    def __init__(self, nome):
        self.nome = nome
        self.validacao = {}
        self.LETth = {}
        self.LETth_critico = 9999
        self.atraso = {}


class Circuito():
    def __init__(self, nome):
        ##### ATRIBUTOS DO CIRCUITO #####
        self.nome = nome
        self.circuito = self.nome + ".txt"
        self.entradas = []
        self.saidas = []
        self.nodos = []
        self.vdd = 0

        self.atrasoCC = 0
        self.simulacoes_feitas = 0
        self.sets_validos = []
        self.sets_invalidos = []

        ##### MONTAGEM DO CIRCUITO #####
        self.__instanciar_nodos()

    def analise_total(self, vdd):
        self.vdd = vdd
        MA.set_vdd(vdd)
        self.__get_atrasoCC()
        self.__ler_validacao()
        self.__determinar_LETths()
        self.__gerar_relatorio_csv()

    def analise_tensao_comparativa(self, minvdd, maxvdd):
        self.__ler_validacao()
        lista_comparativa = {}
        while minvdd <= maxvdd + 0.0001:
            LETth_critico = 9999
            self.vdd = minvdd
            MA.set_vdd(minvdd)
            self.__determinar_LETths()
            for nodo in self.nodos:
                if nodo.LETth_critico < LETth_critico:
                    LETth_critico = nodo.LETth_critico
            lista_comparativa[str(minvdd)] = LETth_critico
            minvdd += 0.05
        self.__escrever_csv_comparativo(lista_comparativa)

    def analise_manual(self):
        analise_manual = True
        MA.set_vdd(float(input("vdd: ")))
        nodo, saida = input("nodo e saida analisados: ").split()
        pulso_in, pulso_out = input("pulsos na entrada e saida: ").split()
        nodo = Nodo(nodo)
        saida = Nodo(saida)
        vetor = [int(sinal) for sinal in input("vetor analisado: ").split()]
        current, simulacoes_feitas = definir_corrente(self.circuito, self.vdd, self.entradas, pulso_in, pulso_out,
                                                      nodo, saida, vetor)
        print("Corrente final: " + str(current))

    def __get_atrasoCC(self):
        simulacoes_feitas = 0
        maior_atraso = 0
        for entrada in self.entradas:
            for saida in self.saidas:
                for i in range(2 ** (len(self.entradas) - 1)):
                    # Atribui o sinal das entradas que nao estao em analise
                    binario = bin(i)
                    binary = list()
                    for j in range((len(self.entradas) - 1) - (len(binario) - 2)): binary.append(0)
                    for j in range(len(binario) - 2): binary.append(int(binario[j + 2]))
                    for index, entrada_qq in enumerate(self.entradas):
                        print(self.entradas, index)
                        if entrada_qq != entrada:
                            entrada_qq.sinal = binary[index]

                    for entrada in self.entradas:
                        print(entrada.sinal, end = " ")

                    # Etapa de medicao de atraso
                    entrada.sinal = "atraso"
                    MA.set_delay_param(entrada, saida, self.vdd)
                    MA.set_signals(self.vdd, self.entradas)
                    os.system(
                        "hspice " + self.circuito + " | grep \"atraso_rr\|atraso_rf\|atraso_fr\|atraso_ff\|largura\" > texto.txt")
                    simulacoes_feitas += 1
                    atraso = MA.get_delay()
                    paridade = 0
                    # if entradaAnalisada.nome == "a":
                    #    print(entradas[0].sinal,entradas[1].sinal,entradas[2].sinal,entradas[3].sinal,entradas[4].sinal)
                    if atraso[0] > atraso[1]: paridade = 1
                    maior_atraso = max(atraso[0 + paridade], atraso[2 + paridade])
                    print(maior_atraso, self.entradas[0].sinal, self.entradas[1].sinal, self.entradas[2].sinal,
                          self.entradas[3].sinal, self.entradas[4].sinal)
                    if maior_atraso > entrada.atraso[0]:
                        entrada.atraso[0] = maior_atraso
                        entrada.atraso[1] = saida
                        entrada.atraso[1] = [self.entradas[0].sinal, self.entradas[1].sinal, self.entradas[2].sinal,
                                                       self.entradas[3].sinal, self.entradas[4].sinal]
                print("Atraso encontrado para " + entrada.nome + " em " + saida)
        print(maior_atraso)
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
        with open(self.circuito, "r") as circuito:
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
        arq_validacao = "val" + self.circuito
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
                            current, simulacoes = definir_corrente(self.circuito, self.vdd, self.entradas,
                                                                   combinacao[0], combinacao[1], nodo, saida,
                                                                   final)
                            self.simulacoes_feitas += simulacoes

                            ##### DETERMINA LETth minimo pra aquela saida ####
                            if current < nodo.LETth[saida.nome][chave][
                                0]:  ##### SE O LETth EH MENOR DO QUE UM JA EXISTENTE
                                nodo.LETth[saida.nome][chave][0] = current
                                nodo.LETth[saida.nome][chave][1] = [final]

                            elif current == nodo.LETth[saida.nome][chave][
                                0]:  ##### SE O LETth EH IGUAL A UM JA EXISTENTE
                                nodo.LETth[saida.nome][chave][1].append(final)

                            if current < nodo.LETth_critico:
                                nodo.LETth_critico = current

                            ##### VALIDACAO DE LARGURA DE PULSO #####
                            # if current < 1000:
                            #     pulso = largura_pulso(circuito, nodo, saida, vdd, atraso)
                            #     simulacoes_feitas += 1
                            #     if pulso == 4444:
                            #         print("Corrente invalidada por lagura de pulso\n")
                            #         current = 4444  # Invalida corrente de pulso muito pequeno
                            #     else:
                            #         print("Corrente validada\n")

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
                                                 [["rise", "rise"], ["fall", "fall"], ["rise", "fall"],
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