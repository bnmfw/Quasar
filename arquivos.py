from matematica import *
from components import Nodo, Entrada, LET, modo_debug
from statistics import stdev
from dataclasses import dataclass
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

    # Escreve vdd no arquivo "vdd.cir"
    @staticmethod
    def set_vdd(vdd: float):
        with open("vdd.cir", "w") as arquivo_vdd:
            arquivo_vdd.write("*Arquivo com a tensao usada por todos os circuitos\n")
            arquivo_vdd.write(f"Vvdd vdd gnd {vdd}\n")
            arquivo_vdd.write(f"Vvcc vcc gnd {vdd}\n")
            arquivo_vdd.write(f"Vclk clk gnd PULSE(0 {vdd} 1n 0.01n 0.01n 1n 2n)")

    # Escreve os sinais no arquivo "fontes.cir"
    @staticmethod
    def set_signals(vdd: float, entradas: list):
        with open("fontes.cir", "w") as sinais:
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

    # Escreve informacoes no arquivo "SETs.cir"
    @staticmethod
    def set_pulse(nodo_nome: str, corrente: float, saida_nome: str, direcao_pulso_nodo: str, let: LET = None):
        with open("SETs.cir", "w") as sets:
            sets.write("*SETs para serem usados nos benchmarks\n")
            if direcao_pulso_nodo == "fall": sets.write("*")
            sets.write(f"Iseu gnd {nodo_nome} EXP(0 {corrente}u 2n 50p 164p 200p) //rise\n")
            if direcao_pulso_nodo == "rise": sets.write("*")
            sets.write(f"Iseu {nodo_nome} gnd EXP(0 {corrente}u 2n 50p 164p 200p) //fall\n")
            sets.write(f".meas tran minout min V({saida_nome}) from=1.0n to=3.8n\n")
            sets.write(f".meas tran maxout max V({saida_nome}) from=1.0n to=3.8n\n")
            # Usado apenas na verificacao de validacao:
            sets.write(f".meas tran minnod min V({nodo_nome}) from=1.0n to=3.8n\n")
            sets.write(f".meas tran maxnod max V({nodo_nome}) from=1.0n to=3.8n\n")
            # Corrente para analise MC:
            sets.write(f".meas tran mincor min i(Vmeas{saida_nome}) from=1.0n to=3.8n\n")
            sets.write(f".meas tran maxcor max i(Vmeas{saida_nome}) from=1.0n to=3.8n\n")

    # Altera o arquivo "atraso.cir"
    @staticmethod
    def set_delay_param(inp: str, out: str, vdd: float):
        with open("atraso.cir", "w") as at:
            at.write("*Arquivo com atraso a ser medido\n")
            tensao = str(vdd / 2)
            at.write(f".meas tran atraso_rr TRIG v({inp}) val='{tensao}' rise=1 TARG v({out}) val='{tensao}' rise=1\n")
            at.write(f".meas tran atraso_rf TRIG v({inp}) val='{tensao}' rise=1 TARG v({out}) val='{tensao}' fall=1\n")
            at.write(f".meas tran atraso_ff TRIG v({inp}) val='{tensao}' fall=1 TARG v({out}) val='{tensao}' fall=1\n")
            at.write(f".meas tran atraso_fr TRIG v({inp}) val='{tensao}' fall=1 TARG v({out}) val='{tensao}' rise=1\n")
            at.write(f".meas tran largura TRIG v({out}) val='{tensao}' fall=1 TARG v({out}) val='{tensao}' rise=1\n")

    # Altera o arquivo "largura_pulso.cir"
    @staticmethod
    def set_pulse_width_param(nodo_nome: str, saida_nome: str, vdd: float, dir_nodo: str, dir_saida: str):
        with open("largura_pulso.cir", "w") as larg:
            larg.write("*Arquivo com a leitura da largura dos pulsos\n")
            tensao = str(vdd * 0.5)
            larg.write(
                f".meas tran atraso TRIG v({nodo_nome}) val='{tensao}' {dir_nodo}=1 TARG v({saida_nome}) val='{tensao}' {dir_saida}=1\n"
                f".meas tran larg TRIG v({nodo_nome}) val='{tensao}' rise=1 TARG v({nodo_nome}) val='{tensao}' fall=1\n")

    # Altera o valor de simulacoes monte carlo a serem feitas
    @staticmethod
    def set_monte_carlo(simulacoes: int):
        with open("monte_carlo.cir", "w") as mc:
            mc.write("*Arquivo Analise Monte Carlo\n")
            mc.write(".tran 0.01n 4n")
            if simulacoes: mc.write(f" sweep monte={simulacoes}")

    # Altera o arquivo "mc.cir"
    @staticmethod
    def set_variability(pvar = None, nvar = None):
        pmedia: float = 4.8108
        nmedia: float = 4.372
        with open ("mc.cir","w") as mc:
            if pvar == None or nvar == None:
                mc.write("* Analise MC\n"
                ".param phig_var_p = gauss(4.8108, 0.05, 3)\n"
                ".param phig_var_n = gauss(4.372, 0.05, 3)")
            else:
                mc.write("* Analise MC\n"
                f".param phig_var_p = {pmedia+pvar}\n"
                f".param phig_var_n = {nmedia+nvar}")

    ################### SEPARACAO SETS E GETS ################################

    @dataclass
    class Meas_from:
        label: str
        value: float
        time: float

    @dataclass
    class Meas_targ:
        label: str
        value: float
        targ: float
        trig: float
    
    def __format_measure_from(self, linha: str) -> Meas_from:
        label_value, time = linha.split("at=")
        label, value = label_value.split("=")
        return self.Meas_from(label.strip(), ajustar(value), ajustar(time))

    def __format_measure_trig(self, linha: str) -> Meas_targ:
        label_value, targ_trig = linha.split("targ=")
        label, value = label_value.split("=")
        targ, trig = targ_trig.split("trig=")
        return self.Meas_targ(label.strip(), ajustar(value), ajustar(targ), ajustar(trig))
    
    def __format_output_line(self, linha: str, saida: dict) -> None:
        measure = None
        if "at=" in linha:
            measure = self.__format_measure_from(linha)
        elif "targ=" in linha:
            measure = self.__format_measure_trig(linha)
        saida[measure.label] = measure

    # Le measures no arquivo output.txt e retorna um dicionario
    def get_output(self, saida: dict) -> None:
        with open("output.txt", "r") as output:
            for linha in output:
                self.__format_output_line(linha, saida) 
    
    # Recupera a tensao de pico
    def get_peak_tension(self, inclinacao: str, nodMeas: bool = False) -> float:
        if not inclinacao in {"rise","fall"}:
            raise ValueError("direcao pulso_saida nao esta entre rise e fall")
        
        output: dict = {}
        self.get_output(output)

        if nodMeas:
            if inclinacao == "fall":
                return output["minnod"].value
            else:
                return output["maxnod"].value
        else:
            if inclinacao == "fall":
                return output["minout"].value
            else:
                return output["maxout"].value

        # with open("output.txt", "r") as text:

        #     minout_line = text.readline()
        #     maxout_line = text.readline()
        #     minnod_line = text.readline()
        #     maxnod_line = text.readline()

        # if not nodMeas:
        #     min, max = minout_line, maxout_line
        # else:
        #     min, max = minnod_line, maxnod_line

        # peak = min if inclinacao == "fall" else max
        
        # return ajustar(peak.split('at=')[0].split('=')[1])
    
    @staticmethod
    def get_monte_carlo_results(circuito, num_analises: int, dir_pulso_saida: str) -> int:
        if not dir_pulso_saida in {"rise","fall"}: 
            raise ValueError("direcao pulso_saida nao esta entre rise e fall")
        analises_flip: int = 0
        casos_validos: list = []
        with open(f"{circuito.nome}.mt0.csv", "r") as mc:
            for i in range(4): _ = mc.readline()  # Decarte das 3 linhas iniciais
            cabecalho = mc.readline().split(",")
            # print(cabecalho)
            orientacao = "mincor" if (dir_pulso_saida == "fall") else "maxcor"
            orien_ten = "minout" if (dir_pulso_saida == "fall") else "maxout"
            corrente_pico_indice = cabecalho.index(orientacao)
            tensao_pico_indice = cabecalho.index(orien_ten)
            tensao_min = cabecalho.index("minout")
            tensao_max = cabecalho.index("maxout")
            largura_indice = cabecalho.index("larg")
            corrente_min = cabecalho.index("mincor")
            corrente_max = cabecalho.index("maxcor")

            for i in range(num_analises):
                linha_lida = mc.readline().split(",")
                cp = ajustar(linha_lida[corrente_pico_indice].strip())
                tp = ajustar(linha_lida[tensao_pico_indice].strip())
                # print(f"{i}"
                #       f"\tten pico: {tp}"
                #       f"\tcorr pico: {cp}"
                #       # f"\tcorr min: {ajustar(linha_lida[corrente_min].strip())}"
                #       # f"\tcorr max: {ajustar(linha_lida[corrente_max].strip())}"
                #       f"\tlarg: {linha_lida[largura_indice].strip()}", end="")
                if (orientacao == 'mincor' and tp < circuito.vdd / 2) or (orientacao == 'maxcor' and tp > circuito.vdd / 2):
                    # print("\tSatisfez!")
                    analises_flip += 1
                    casos_validos.append(cp)
                # else:
                    # print("")
                # if float(linha_lida[largura_indice]) == condicao_satisfatoria:
                #     if dir_pulso_saida == "rise":
                #         if float(linha_lida[tensao_pico_indice]) < circuito.vdd / 2:
                #             analises_validas += 1
                #     else:
                #         if float(linha_lida[tensao_pico_indice]) > circuito.vdd / 2:
                #             analises_validas += 1
            if casos_validos:
                # print(f"\nMedia da corrente: {media(casos_validos)}")
                # print(f"Desvio padrao da corrente: {stdev(casos_validos)}")
                pass
            print(f"Proporcao de flips: {100*analises_flip/num_analises:.2f}% do total")
        return analises_flip

    # Le o atraso do nodo a saida no arquivo "output.txt"
    def get_delay(self) -> float:
        linhas_de_atraso = list()
        atrasos = list()  # 0 rr, 1 rf, 2 ff, 3 fr
        with open("output.txt", "r") as text:
            # Leitura das 4 linhas com atraso
            for i in range(4):
                linhas_de_atraso.append(self.split_spice(text.readline()))

                # Retorno por erro
                if linhas_de_atraso[i][0][0] == "*":
                    # print(linhas_de_atraso[i][0])
                    return 0

                atrasos.append(linhas_de_atraso[i][1])  # salva os 4 atrasos
                atrasos[i] = abs(ajustar(atrasos[i]))
        atrasos.sort()
        return atrasos[1]

    # Leitura do arquivo "output.txt"
    @staticmethod
    def get_pulse_delay_validation(atraso: float) -> float:
        with open("output.txt", "r") as texto:
            _ = texto.readline().split()
            larg = texto.readline().split()
        # if analise_manual: print(atraso)
        # if atraso[0][0] == "*":
        #     return -1.0  # pulso muito pequeno
        # if "-" in atraso[0]:
        #     atraso = atraso[0].split("-")
        # atraso = ajustar(atraso[1])

        if larg[0][0] == "*" or larg[1] == "failed":
            return -1  # pulso muito pequeno
        if "-" in larg[0]:
            larg = larg[0].split("-")

        if modo_debug: print(f"larguras: {larg}")
        larg = ajustar(larg[1])
        return larg - atraso
        # return larg - atraso

    # Leitura das instancias do arquivo "<circuito>.mc0.csv"
    @staticmethod
    def get_mc_instances(circuito_nome: str, simulacoes: int) -> dict:
        instancias: dict = {}
        with open(f"{circuito_nome}.mc0.csv","r") as mc:
            
            # Eliminacao de informacao inutil
            while mc.readline()[:5] != "index":
                pass

            for i in range(1, simulacoes + 1):
                _, nmos, pmos, _ = mc.readline().split(",")
                nmos = float(nmos[:-1])
                pmos = float(pmos[:-1])
                instancias[i] = (pmos, nmos)
        
        return instancias 

    # Substitui o valor da corrente no arquivo "SETs.cir"
    def change_pulse_value(self, nova: float) -> float:
        with open("SETs.cir", "r") as arquivo_set:
            arquivo_set.readline()
            linha_rise = arquivo_set.readline().split()
            linha_fall = arquivo_set.readline().split()
            saida_nome = arquivo_set.readline().split()[4]
            saida_nome = saida_nome[:-1]
            saida_nome = saida_nome[2:]
            corrente = ajustar(linha_rise[4][:-1])
            if linha_fall[0][0] == "*":
                cod = "rise"
                nodo_nome = linha_rise[2]
            else:
                cod = "fall"
                nodo_nome = linha_fall[1]
            self.set_pulse(nodo_nome, nova, saida_nome, cod)
            return corrente


class CSVManager():
    def __init__(self):
        pass

    @staticmethod
    def tup_dict_to_csv(filename: str, dicionario: dict):
        with open(filename, "w") as tabela:
            for chave, tupla in dicionario.items():
                tabela.write(f"{chave}")
                for valor in tupla:
                    tabela.write(f",{valor}")
                tabela.write("\n")

        print(f"\nTabela {filename} gerada com sucesso\n")

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
        circuito.saidas = [Nodo(saida) for saida in lista_de_saidas]

        # Carregamento das entradas
        circuito.entradas = [Entrada(entrada) for entrada in lista_de_entradas]

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
