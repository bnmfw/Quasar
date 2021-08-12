from matematica import *
from components import Nodo, Entrada, LET
from statistics import stdev
import json

analise_manual = False


def alternar_combinacao(combinacao):
    if type(combinacao) == str:
        if combinacao == "rr":
            return ["rise", "rise"]
        elif combinacao == "rf":
            return ["rise", "fall"]
        elif combinacao == "fr":
            return ["fall", "rise"]
        else:
            return ["fall", "fall"]
    elif type(combinacao) == list:
        if combinacao == ["rise", "rise"]:
            return "rr"
        elif combinacao == ["rise", "fall"]:
            return "rf"
        elif combinacao == ["fall", "rise"]:
            return "fr"
        else:
            return "ff"
    else:
        raise TypeError("Entrada nao foi uma lista (ex: [\"rise\",\"fall\"]) ou uma string (ex: \"rf\"")


class SpiceManager():
    def __init__(self):
        pass

    # Maneja a leitura de linhas no arquivo spice
    @staticmethod
    def split_spice(linha: str) -> list:
        split_nativo: list = linha.split()
        # Ajuse de leitura
        for index, palavra in enumerate(split_nativo):
            if "=-" in palavra:
                index_atual = len(split_nativo)
                split_nativo.append("lixo")
                while index_atual > index + 1:
                    split_nativo[index_atual] = split_nativo[index_atual - 1]
                    index_atual -= 1
                termos = palavra.split("=-")
                split_nativo[index + 1] = "-" + termos[1]
                split_nativo[index] = termos[0]
        return split_nativo

    # Escreve vdd no arquivo "vdd.txt"
    @staticmethod
    def set_vdd(vdd: float):
        with open("vdd.txt", "w") as arquivo_vdd:
            arquivo_vdd.write("*Arquivo com a tensao usada por todos os circuitos\n")
            arquivo_vdd.write(f"Vvdd vdd gnd {vdd}\n")
            arquivo_vdd.write(f"Vvcc vcc gnd {vdd}\n")
            arquivo_vdd.write(f"Vclk clk gnd PULSE(0 {vdd} 1n 0.01n 0.01n 1n 2n)")

    # Escreve os sinais no arquivo "fontes.txt"
    @staticmethod
    def set_signals(vdd: float, entradas: list):
        with open("fontes.txt", "w") as sinais:
            sinais.write("*Fontes de sinal a serem editadas pelo roteiro\n")

            # Escreve o sinal analogico a partir do sinal logico
            for i in range(len(entradas)):
                sinais.write(f"V{entradas[i].nome} {entradas[i].nome} gnd ")
                if entradas[i].sinal == 1:
                    sinais.write(f"{vdd}\n")
                elif entradas[i].sinal == 0:
                    sinais.write("0.0\n")
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
    def set_delay_param(inp: str, out: str, vdd: float):
        with open("atraso.txt", "w") as at:
            at.write("*Arquivo com atraso a ser medido\n")
            tensao = str(vdd / 2)
            at.write(f".meas tran atraso_rr TRIG v({inp}) val='{tensao}' rise=1 TARG v({out}) val='{tensao}' rise=1\n")
            at.write(f".meas tran atraso_rf TRIG v({inp}) val='{tensao}' rise=1 TARG v({out}) val='{tensao}' fall=1\n")
            at.write(f".meas tran atraso_ff TRIG v({inp}) val='{tensao}' fall=1 TARG v({out}) val='{tensao}' fall=1\n")
            at.write(f".meas tran atraso_fr TRIG v({inp}) val='{tensao}' fall=1 TARG v({out}) val='{tensao}' rise=1\n")
            at.write(f".meas tran largura TRIG v({out}) val='{tensao}' fall=1 TARG v({out}) val='{tensao}' rise=1\n")

    # Altera o arquivo "largura_pulso.txt"
    @staticmethod
    def set_pulse_width_param(nodo_nome: str, saida_nome: str, vdd: float, dir_nodo: str, dir_saida: str):
        with open("largura_pulso.txt", "w") as larg:
            larg.write("*Arquivo com a leitura da largura dos pulsos\n")
            tensao = str(vdd * 0.5)
            larg.write(
                f".meas tran atraso TRIG v({nodo_nome}) val='{tensao}' {dir_nodo}=1 TARG v({saida_nome}) val='{tensao}' {dir_saida}=1\n"
                f".meas tran larg TRIG v({nodo_nome}) val='{tensao}' rise=1 TARG v({nodo_nome}) val='{tensao}' fall=1\n")

    # Altera o valor de simulacoes monte carlo a serem feitas
    @staticmethod
    def set_monte_carlo(simulacoes: int):
        with open("monte_carlo.txt", "w") as mc:
            mc.write("*Arquivo Analise Monte Carlo\n")
            mc.write(".tran 0.01n 4n")
            if simulacoes: mc.write(f" sweep monte={simulacoes}")

    ################### SEPARACAO SETS E GETS ################################

    # Le a resposta do pulso no arquivo "texto.txt"
    @staticmethod
    def get_peak_tension(dir_pulso_saida: str, offset: int) -> float:
        if dir_pulso_saida != "rise" and dir_pulso_saida != "fall":
            raise ValueError("direcao pulso_saida nao esta entre rise e fall")
        linha_texto = list(range(4))
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
    def get_monte_carlo_results(circuito, num_analises: int, dir_pulso_saida: str) -> int:
        if dir_pulso_saida != "rise" and dir_pulso_saida != "fall": raise ValueError(
            "direcao pulso_saida nao esta entre rise e fall")
        analises_validas: int = 0
        casos_validos: list = []
        with open(f"{circuito.nome}.mt0.csv", "r") as mc:
            for i in range(3): _ = mc.readline()  # Decarte das 3 linhas iniciais
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
                if (orientacao == 'minout' and tp < circuito.vdd / 2) or (orientacao == 'maxout' and tp > circuito.vdd / 2):
                    print("\tSatisfez!")
                    analises_validas += 1
                    casos_validos.append(tp)
                else:
                    print("")
                # if float(linha_lida[largura_indice]) == condicao_satisfatoria:
                #     if dir_pulso_saida == "rise":
                #         if float(linha_lida[tensao_pico_indice]) < circuito.vdd / 2:
                #             analises_validas += 1
                #     else:
                #         if float(linha_lida[tensao_pico_indice]) > circuito.vdd / 2:
                #             analises_validas += 1
            print(f"Media: {media(casos_validos)}")
            print(f"Desvio padrao: {stdev(casos_validos)}")
            print(f"Analises validas: {100*analises_validas/num_analises:.2f}%")
        return analises_validas

    # Le o atraso do nodo a saida no arquivo "texto.txt"
    def get_delay(self) -> float:
        linhas_de_atraso = list()
        atrasos = list()  # 0 rr, 1 rf, 2 ff, 3 fr
        with open("texto.txt", "r") as text:
            # Leitura das 4 linhas com atraso
            for i in range(4):
                linhas_de_atraso.append(self.split_spice(text.readline()))

                # Retorno por erro
                if linhas_de_atraso[i][0][0] == "*":
                    # print(linhas_de_atraso[i][0])
                    return 0

                atrasos.append(linhas_de_atraso[i][1])  # salva os 4 atrasos
                atrasos[i] = abs(ajustar_valor(atrasos[i]))
        atrasos.sort()
        return atrasos[1]

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
        # return larg - atraso


class CSVManager():
    def __init__(self):
        pass

    @staticmethod
    def escrever_csv_total(circuito):
        linha = 2
        tabela = circuito.nome + ".csv"
        with open(tabela, "w") as sets:
            sets.write("Nodo,Saida,Pulso,Pulso,Corrente,LETs,Num Val,Validacoes->\n")
            for nodo in circuito.nodos:
                for let in nodo.LETs:
                    c0, c1 = alternar_combinacao(let.orientacao)
                    sets.write(f"{nodo.nome},{let.saida_nome},{c0},{c1},{let.corrente:.2f},{let.valor:.2e},{len(let)}")
                    for validacao in let.validacoes:
                        sets.write(",'")
                        for num in validacao: sets.write(f"{num}")
                    sets.write("\n")
                    linha += 1
        print(f"\nTabela {tabela} gerada com sucesso\n")

    @staticmethod
    def escrever_csv_comparativo(circuito, lista_comparativa):
        with open(f"{circuito.nome}_compara.csv", "w") as tabela:
            for chave in lista_comparativa:
                tabela.write(chave + "," + "{:.2f}".format(lista_comparativa[chave]) + "\n")

        print(f"\nTabela {circuito.nome}_compara.csv" + " gerada com sucesso\n")


class JsonManager():
    def __init__(self):
        pass

    def codificar(self, circuito):
        # Codificacao dos nodos
        dicionario_de_nodos = {}  # criacao do dicionario que tera o dicionario de todos os nodos
        lista_de_nodos = []
        for nodo in circuito.nodos:
            lista_de_nodos.append(nodo.codec())

        # Codificacao de entradas
        lista_de_saidas = []
        for saida in circuito.saidas:
            lista_de_saidas.append(saida.nome)

        # Codificacao de saidas
        lista_de_entradas = []
        for entrada in circuito.entradas:
            lista_de_entradas.append(entrada.nome)

        circuito_codificado = {}
        circuito_codificado["nome"] = circuito.nome
        circuito_codificado["vdd"] = circuito.vdd
        circuito_codificado["atrasoCC"] = circuito.atrasoCC
        circuito_codificado["entradas"] = lista_de_entradas
        circuito_codificado["saidas"] = lista_de_saidas
        circuito_codificado["nodos"] = lista_de_nodos

        json.dump(circuito_codificado, open(f"{circuito.nome}_{circuito.vdd}.json", "w"))

        try:
            with open(circuito.nome + ".json", "r"):
                pass
        except FileNotFoundError:
            json.dump(circuito_codificado, open(circuito.nome + ".json", "w"))

        print("Carregamento do Json realizado com sucesso")

    def decodificar(self, circuito, tensao, nao_usar_template):
        circuito_codificado = []
        if nao_usar_template:
            circuito_codificado = json.load(open(circuito.nome + "_" + str(tensao) + ".json", "r"))
            circuito.vdd = circuito_codificado["vdd"]
        else:
            circuito_codificado = json.load(open(circuito.nome + ".json", "r"))
            circuito.vdd = tensao

        # Desempacotamento dos dados
        circuito.atrasoCC = circuito_codificado["atrasoCC"]
        lista_de_nodos: list = circuito_codificado["nodos"]
        lista_de_saidas: list = circuito_codificado["saidas"]
        lista_de_entradas: list = circuito_codificado["entradas"]

        # Carregamento das saidas
        for saida in lista_de_saidas:
            circuito.saidas.append(Nodo(saida))

        # Carregamento das entradas
        for entrada in lista_de_entradas:
            circuito.entradas.append(Entrada(entrada, "t"))

        # Carregamento dos nodos
        for nodo_dict in lista_de_nodos:
            nodo = Nodo("nome")
            nodo.decodec(nodo_dict, circuito.vdd)
            circuito.nodos.append(nodo)

        print("Leitura do Json realizada com sucesso")


JM = JsonManager()

if __name__ == "__main__":
    print("Rodando Teste de Codificacao...")

    let1 = LET(154.3, 0.7, "nodo1", "saida1", "fr")
    let2 = LET(300, 0.7, "nodo1", "saida1", "rf")
    let3 = LET(190.8, 0.7, "nodo2", "saida1", "fr")
    let4 = LET(156.9, 0.7, "nodo2", "saida1", "ff")
    let5 = LET(7.4, 0.7, "saida", "saida1", "rr")
    let6 = LET(288.1, 0.7, "saida", "saida1", "rf")

    nodo1 = Nodo("nodo1")
    nodo1.validacao = {"saida1": ["x", "x", "x", "x", "x"]}
    nodo1.LETs = [let1, let2]
    nodo1.LETth = 154.3

    nodo2 = Nodo("nodo2")
    nodo2.validacao = {"saida1": ["x", "x", "x", "x", "x"]}
    nodo2.LETs = [let2, let3]
    nodo2.LETth = 156.9

    nodo3 = Nodo("saida1")
    nodo3.validacao = {"saida1": ["x", "x", "x", "x", "x"]}
    nodo3.LETs = [let4, let5]
    nodo3.LETth = 7.4


    class FakeCircuit:
        def __init__(self):
            self.nome = "teste_circuito"
            self.entradas = [Entrada("a", "t"), Entrada("b", "t")]
            self.saidas = [nodo3]
            self.nodos = [nodo1, nodo2, nodo3]
            self.vdd = 0.7
            self.atrasoCC = 9999.0


    circuito = FakeCircuit()

    JM.codificar(circuito)
    JM.decodificar(circuito, 0.7, True)

    print("Testes realizados com sucesso!")
