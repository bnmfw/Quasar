from matematica import *

analise_manual = False

class SpiceManager():
    def __init__(self):
        pass

    # Maneja a leitura de linhas no arquivo spice
    def split_spice(self, linha):
        split_nativo = linha.split()
        # Ajuse de leitura
        for index, palavra in enumerate(split_nativo):
            if "=-" in palavra:
                index_atual = len(split_nativo)
                split_nativo.append("lixo")
                while index_atual > index+1:
                    split_nativo[index_atual] = split_nativo[index_atual-1]
                    index_atual -= 1
                termos = palavra.split("=-")
                split_nativo[index + 1] = "-"+termos[1]
                split_nativo[index] = termos[0]
        return split_nativo

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

    # Altera o arquivo "largura_pulso.txt"
    def set_pulse_width_param(self, nodo, saida, vdd, dir_nodo, dir_saida):
        with open("largura_pulso.txt", "w") as larg:
            larg.write("*Arquivo com a leitura da largura dos pulsos\n")
            tensao = str(vdd * 0.5)
            larg.write(
                ".meas tran atraso TRIG v(" + nodo + ") val='" + tensao + "' " + dir_nodo + "=1 TARG v(" + saida + ") val='" + tensao + "' " + dir_saida + "=1\n"
                ".meas tran larg TRIG v(" + nodo + ") val='" + tensao + "' rise=1 TARG v(" + nodo + ") val='" + tensao + "' fall=1\n")

    # Altera o valor de simulacoes monte carlo a serem feitas
    def set_monte_carlo(self, simulacoes):
        with open("monte_carlo.txt", "w") as mc:
            mc.write("*Arquivo Analise Monte Carlo\n")
            mc.write(".tran 0.01n 4n")
            if simulacoes: mc.write(" sweep monte="+str(simulacoes))

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
                linhas_de_atraso.append(self.split_spice(text.readline()))

                #Retorno por erro
                if linhas_de_atraso[i][0][0] == "*":
                    # print(linhas_de_atraso[i][0])
                    return [0, 0, 0, 0]

                atrasos.append(linhas_de_atraso[i][1])  # salva os 4 atrasos
                atrasos[i] = ajustar_valor(atrasos[i])

            # linhas_de_atraso.append(text.readline().split())
            # largura_pulso_saida = linhas_de_atraso[4][1]
            # largura_pulso_saida = abs(ajustar_valor(largura_pulso_saida))
            # if largura_pulso_saida < 1 * 10 ** -9:  # Largura de pulso menor que 1 nanosegundo
            #     # print("Pulso menor que 1 nano",largura_pulso_saida)
            #     return [0, 0, 0, 0]

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
        return larg - ajustar_valor("18.6p")
        #return larg - atraso
