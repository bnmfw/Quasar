from matematica import *

analise_manual = False

class SpiceManager():
    def __init__(self):
        pass

    # Maneja a leitura de linhas no arquivo spice
    @staticmethod
    def split_spice(linha):
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
    @staticmethod
    def set_vdd(vdd):
        with open("vdd.txt", "w") as arquivo_vdd:
            arquivo_vdd.write("*Arquivo com a tensao usada por todos os circuitos\n")
            arquivo_vdd.write(f"Vvdd vdd gnd {vdd}\n")
            arquivo_vdd.write(f"Vvcc vcc gnd {vdd}\n")
            arquivo_vdd.write(f"Vclk clk gnd PULSE(0 {vdd} 1n 0.01n 0.01n 1n 2n)")

    # Escreve os sinais no arquivo "fontes.txt"
    @staticmethod
    def set_signals(vdd, entradas):
        with open("fontes.txt", "w") as sinais:
            sinais.write("*Fontes de sinal a serem editadas pelo roteiro\n")

            #Escreve o sinal analogico a partir do sinal logico
            for i in range(len(entradas)):
                sinais.write(f"V{entradas[i].nome} {entradas[i].nome} gnd ")
                if entradas[i].sinal == 1: sinais.write(f"{vdd}\n")
                elif entradas[i].sinal == 0: sinais.write("0.0\n")
                elif entradas[i].sinal == "atraso":
                    sinais.write(f"PWL(0n 0 1n 0 1.01n {vdd} 3n {vdd} 3.01n 0)\n")
                else:
                    print("ERRO SINAL NAO IDENTIFICADO RECEBIDO: ", entradas[i].sinal)

    # Escreve informacoes no arquivo "SETs.txt"
    @staticmethod
    def set_pulse(nodo_nome: str, corrente: float, saida_nome: str, direcao_pulso_nodo: str):
        with open("SETs.txt", "w") as sets:
            sets.write("*SETs para serem usados nos benchmarks\n")
            if direcao_pulso_nodo == "fall": sets.write("*")
            sets.write(f"Iseu gnd {nodo_nome} EXP(0 {corrente}u 2n 50p 164p 200p) //rise\n")
            if direcao_pulso_nodo == "rise": sets.write("*")
            sets.write(f"Iseu {nodo_nome} gnd EXP(0 {corrente}u 2n 50p 164p 200p) //fall\n")
            sets.write(f".meas tran minout min V({saida_nome}) from=1.0n to=4.0n\n")
            sets.write(f".meas tran maxout max V({saida_nome}) from=1.0n to=4.0n\n")
            # Usado apenas na verificacao de validacao:
            sets.write(f".meas tran minnod min V({nodo_nome}) from=1.0n to=4.0n\n")
            sets.write(f".meas tran maxnod max V({nodo_nome}) from=1.0n to=4.0n\n")

    # Altera o arquivo "atraso.txt"
    @staticmethod
    def set_delay_param(inp, out, vdd):
        with open("atraso.txt", "w") as at:
            at.write("*Arquivo com atraso a ser medido\n")
            tensao = str(vdd/2)
            at.write(f".meas tran atraso_rr TRIG v({inp}) val='{tensao}' rise=1 TARG v({out}) val='{tensao}' rise=1\n")
            at.write(f".meas tran atraso_rf TRIG v({inp}) val='{tensao}' rise=1 TARG v({out}) val='{tensao}' fall=1\n")
            at.write(f".meas tran atraso_ff TRIG v({inp}) val='{tensao}' fall=1 TARG v({out}) val='{tensao}' fall=1\n")
            at.write(f".meas tran atraso_fr TRIG v({inp}) val='{tensao}' fall=1 TARG v({out}) val='{tensao}' rise=1\n")
            at.write(f".meas tran largura TRIG v({out}) val='{tensao}' fall=1 TARG v({out}) val='{tensao}' rise=1\n")

    # Altera o arquivo "largura_pulso.txt"
    @staticmethod
    def set_pulse_width_param(nodo_nome:str, saida_nome:str, vdd:float, dir_nodo:str, dir_saida:str):
        with open("largura_pulso.txt", "w") as larg:
            larg.write("*Arquivo com a leitura da largura dos pulsos\n")
            tensao = str(vdd * 0.5)
            larg.write(
                f".meas tran atraso TRIG v({nodo_nome}) val='{tensao}' {dir_nodo}=1 TARG v({saida_nome}) val='{tensao}' {dir_saida}=1\n"
                f".meas tran larg TRIG v({nodo_nome}) val='{tensao}' rise=1 TARG v({nodo_nome}) val='{tensao}' fall=1\n")

    # Altera o valor de simulacoes monte carlo a serem feitas
    @staticmethod
    def set_monte_carlo(simulacoes:int):
        with open("monte_carlo.txt", "w") as mc:
            mc.write("*Arquivo Analise Monte Carlo\n")
            mc.write(".tran 0.01n 4n")
            if simulacoes: mc.write(f" sweep monte={simulacoes}")

    ################### SEPARACAO SETS E GETS ################################

    # Le a resposta do pulso no arquivo "texto.txt"
    @staticmethod
    def get_peak_tension(dir_pulso_saida:str, offset:int) -> float:
        if dir_pulso_saida != "rise" and dir_pulso_saida != "fall": raise ValueError("direcao pulso_saida nao esta entre rise e fall")
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
        if analise_manual: print(f"Tensao max: {max_tensao} Tensao min: {min_tensao}")

        # Identifica se o pico procurado e do tipo rise ou fall
        tensao_pico = max_tensao if (dir_pulso_saida == "rise") else min_tensao

        # retorna a tensao de pico lida
        return tensao_pico

    @staticmethod
    def get_monte_carlo_results(circuito, num_analises:int, dir_pulso_saida:str) -> int:
        if dir_pulso_saida != "rise" and dir_pulso_saida != "fall": raise ValueError("direcao pulso_saida nao esta entre rise e fall")
        analises_validas = 0
        with open(f"{circuito.nome}.mt0.csv", "r") as mc:
            for i in range(3): _ = mc.readline() # Decarte das 3 linhas iniciais
            cabecalho = mc.readline().split(",")
            orientacao = "minout" if (dir_pulso_saida == "fall") else "maxout"
            tensao_pico_indice = cabecalho.index(orientacao)
            tensao_min = cabecalho.index("minout")
            tensao_max = cabecalho.index("maxout")
            largura_indice = cabecalho.index("larg")

            for i in range(num_analises):
                linha_lida = mc.readline().split(",")
                tp = ajustar_valor(linha_lida[tensao_pico_indice].strip())
                print(f"{i}"
                      f"\tpico: {tp:.2f}"
                      f"\tmin: {ajustar_valor(linha_lida[tensao_min].strip()):.2f}"
                      f"\tmax: {ajustar_valor(linha_lida[tensao_max].strip()):.2f}"
                      f"\tlarg: {linha_lida[largura_indice].strip()}", end="")
                if (orientacao == 'minout' and tp < circuito.vdd/2) or (orientacao == 'maxout' and tp > circuito.vdd/2):
                    print("\tSatisfez!")
                # if float(linha_lida[largura_indice]) == condicao_satisfatoria:
                #     if dir_pulso_saida == "rise":
                #         if float(linha_lida[tensao_pico_indice]) < circuito.vdd / 2:
                #             analises_validas += 1
                #     else:
                #         if float(linha_lida[tensao_pico_indice]) > circuito.vdd / 2:
                #             analises_validas += 1
        return analises_validas


    # Le o atraso do nodo a saida no arquivo "texto.txt"
    def get_delay(self) -> list:
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
    @staticmethod
    def get_pulse_delay_validation() -> float:
        with open("texto.txt", "r") as texto:
            atraso = texto.readline().split()
            larg = texto.readline().split()
        # if analise_manual: print(atraso)
        if atraso[0][0] == "*":
            return -1.0  # pulso muito pequeno
        if "-" in atraso[0]:
            atraso = atraso[0].split("-")
        atraso = ajustar_valor(atraso[1])

        if larg[0][0] == "*":
            return -1.0  # pulso muito pequeno
        if "-" in larg[0]:
            larg = larg[0].split("-")
        larg = ajustar_valor(larg[1])
        return larg - ajustar_valor("18.6p")
        #return larg - atraso
