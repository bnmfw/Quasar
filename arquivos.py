import pstats
from matematica import *
from components import Nodo, Entrada, LET, modo_debug
from statistics import stdev
from dataclasses import dataclass
import json
import os

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

    def __write_peak_meas(self, arquivo, label: str, peak: str, grandeza: str, node: str, start: float, finish: float):
        if not peak in {"min", "max"}:
            raise ValueError("pico eh min ou max")
        if not grandeza in {"i", "V"}:
            raise ValueError("grandeza nao esta em i ou V")
         
        arquivo.write(f".meas tran {label} {peak} {grandeza}({node}) from={start}n to={finish}n\n")

    def __write_trig_meas(self, arquivo, label: str, trig: str, trig_value: float, trig_inclin: str,
     targ: str, targ_value: float, targ_inclin: str):

        arquivo.write(f".meas tran {label} TRIG v({trig}) val='{trig_value}' {trig_inclin}=1 TARG v({targ}) val='{targ_value}' {targ_inclin}=1\n")
    
    def set_pulse_measure(self, nodo: str, saida: str):
        with open("measure.cir", "w") as arquivo:
            arquivo.write("*Arquivo com os measures usados\n")

            self.__write_peak_meas(arquivo, "minout", "min", "V", saida, 1.0, 3.8)
            self.__write_peak_meas(arquivo, "maxout", "max", "V", saida, 1.0, 3.8)
            self.__write_peak_meas(arquivo, "minnod", "min", "V", nodo, 1.0, 3.8)
            self.__write_peak_meas(arquivo, "maxnod", "max", "V", nodo, 1.0, 3.8)
    
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
    def set_pulse(self, let: LET, corrente = None):
        if not let.orientacao[0] in {"f", "r"}:
            raise ValueError("Nao recebi f ou r como inclincacao do pulso")
        if corrente == None:
            corrente = let.corrente

        self.set_pulse_measure(let.nodo_nome, let.saida_nome)

        with open("SETs.cir", "w") as sets:
            sets.write("*SETs para serem usados nos benchmarks\n")
            if let.orientacao[0] == "f": sets.write("*")
            sets.write(f"Iseu gnd {let.nodo_nome} EXP(0 {corrente}u 2n 50p 164p 200p) //rise\n")
            if let.orientacao[0] == "r": sets.write("*")
            sets.write(f"Iseu {let.nodo_nome} gnd EXP(0 {corrente}u 2n 50p 164p 200p) //fall\n")

    # Altera o arquivo "measure.cir"
    def set_delay_measure(self, input: str, out: str, vdd: float):
        with open("measure.cir", "w") as arquivo:
            arquivo.write("*Arquivo com atraso a ser medido\n")
            tensao = str(vdd / 2)
            self.__write_trig_meas(arquivo, "atraso_rr", input, tensao, "rise", out, tensao, "rise")
            self.__write_trig_meas(arquivo, "atraso_rf", input, tensao, "rise", out, tensao, "fall")
            self.__write_trig_meas(arquivo, "atraso_ff", input, tensao, "fall", out, tensao, "fall")
            self.__write_trig_meas(arquivo, "atraso_fr", input, tensao, "fall", out, tensao, "rise")
            # self.__write_trig_meas(arquivo, "largura", out, tensao, "fall", out, tensao, "rise")

    # Altera o arquivo "measure.cir"
    def set_pulse_width_measure(self, let: LET):
        # print(let.vdd)
        dir_nodo, dir_saida = alternar_combinacao(let.orientacao)
        with open("measure.cir", "w") as arquivo:
            arquivo.write("*Arquivo com a leitura da largura dos pulsos\n")
            tensao = str(let.vdd * 0.5)
            self.__write_trig_meas(arquivo, "atraso", let.nodo_nome, tensao, dir_nodo, let.saida_nome, tensao, dir_saida)
            self.__write_trig_meas(arquivo, "larg", let.nodo_nome, tensao, "rise", let.nodo_nome, tensao, "fall")

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
        # print(linha)
        if "not found" in linha:
            label, *_ = linha.split("=")
            return self.Meas_targ(label.strip(), None, None, None)

        label_value_targ, trig = linha.split("trig=")  
        label_value, targ= label_value_targ.split("targ=")
        label, value = label_value.split("=")
        return self.Meas_targ(label.strip(), ajustar(value), ajustar(targ), ajustar(trig))
    
    def __format_output_line(self, linha: str, saida: dict) -> None:
        measure = None
        if "at=" in linha:
            measure = self.__format_measure_from(linha)
        elif "trig=" in linha:
            measure = self.__format_measure_trig(linha)
        elif "**warning**" in linha:
            return
        saida[measure.label] = measure

    # Le measures no arquivo output.txt e retorna um dicionario
    def get_output(self, saida: dict) -> None:
        with open("output.txt", "r") as output:
            for linha in output:
                # print(f"linha: {linha}")
                self.__format_output_line(linha, saida) 
    
    # Recupera a tensao de pico
    def get_peak_tension(self, inclinacao: str, nodMeas: bool = False) -> float:
        if not inclinacao in {"f", "r"}:
            raise ValueError(f"Inclinacao com valor nao admitido: {inclinacao}")

        output: dict = {}
        self.get_output(output)

        if nodMeas:
            if inclinacao == "f":
                return output["minnod"].value
            else:
                return output["maxnod"].value
        else:
            if inclinacao == "f":
                return output["minout"].value
            else:
                return output["maxout"].value
    
    # Le um arquivo csv como mc0.csv e mt0.csv e retorna um dicionario com as colunas
    def __get_csv_data(self, filename: str, stop: str = None) -> dict:
        
        dados: dict = {}
        
        with open(f"{filename}", "r") as arquivo:
            while stop != None and not stop in arquivo.readline():
                pass

            # criacao do padrao do dicionario
            cabecalho = arquivo.readline().split(",")
            for label in cabecalho:
                if "\n" in label:
                    label = label[:-1]
                dados[label] = []

            for linha in arquivo:
                valores = linha.split(",")
                for index, chave in enumerate(dados):
                    valor = None if valores[index].strip() == "failed" else ajustar(valores[index])
                    dados[chave].append(valor)
        
        return dados

    def get_monte_carlo_results(self, circuito, num_analises: int, inclinacao_saida: str) -> int:
        
        falhas: int = 0
        casos_validos: list = []

        dados: dict = self.__get_csv_data(f"{circuito.nome}.mt0.csv", ".TITLE")

        inclinacao_corr = "mincor" if inclinacao_saida == "fall" else "maxcor"
        inclinacao_tens = "minout" if inclinacao_saida == "fall" else "maxout"

        for i in range(num_analises):
            corrente_pico = dados[inclinacao_corr][i]
            tensao_pico = dados[inclinacao_tens][i]

            if inclinacao_saida == "fall" and tensao_pico < circuito.vdd / 2 or\
                inclinacao_saida == "rise" and tensao_pico > circuito.vdd / 2:
                falhas += 1
                casos_validos.append(corrente_pico)

        print(f"Proporcao de flips: {100*falhas/num_analises:.2f}% do total")
        return falhas

    # Le o atraso do nodo a saida no arquivo "output.txt"
    def get_delay(self) -> float:

        output: dict = {}
        self.get_output(output)

        atrasos: list = [output["atraso_rr"].value, output["atraso_ff"].value, output["atraso_rf"].value, output["atraso_fr"].value]
        # Erro
        if None in atrasos:
            return 0
        
        # Sorting
        for i, atraso in enumerate(atrasos):
            atrasos[i] = abs(atraso)
        # print(f"not sorted: {atrasos}")
        atrasos.sort()
        # print(f"sorted: {atrasos}")
        return atrasos[1]
    
    # Leitura das instancias do arquivo "<circuito>.mc0.csv"
    def get_mc_instances(self, circuito_nome: str, simulacoes: int) -> dict:
        instancias: dict = {}

        dados = self.__get_csv_data(f"{circuito_nome}.mc0.csv", "$ IRV")

        ps: str = "pmos_rvt:@:phig_var_p:@:IGNC"
        ns: str = "nmos_rvt:@:phig_var_n:@:IGNC"

        for i, pmos, nmos in zip(dados["index"], dados[ps], dados[ns]):
            instancias[i] = (float(pmos), float(nmos))
        return instancias

    # Substitui o valor da corrente no arquivo "SETs.cir"
    def change_pulse_value(self, nova_corrente: float) -> float:
        with open("SETs.cir", "r") as arquivo_set:
            arquivo_set.readline()
            linha_rise = arquivo_set.readline()
            _, _, nodo_nome, _, corrente, *_ = linha_rise.split()
            corrente = ajustar(corrente)
            inclinacao = "ft" if "*" in linha_rise else "rt"
            
            self.set_pulse(LET(nova_corrente, 0, nodo_nome, "setup", inclinacao))
            return corrente

SM = SpiceManager()

class SpiceRunner():
    def __init__(self) -> None:
        pass

    def run_delay(self, filename: str, entrada_nome: str, saida_nome: str, vdd: float, entradas: list) -> float:
        SM.set_delay_measure(entrada_nome, saida_nome, vdd)
        SM.set_signals(vdd, entradas)
        os.system(f"hspice {filename}| grep \"atraso_rr\|atraso_rf\|atraso_fr\|atraso_ff\" > output.txt")
        return SM.get_delay()

    def run_SET(self, filename: str, let: LET, corrente = None):
        # print("run SET")
        if corrente == None:
            corrente = let.corrente
        SM.set_pulse(let, corrente)
        os.system(f"hspice {filename} | grep \"minout\|maxout\|minnod\|maxnod\" > output.txt")
        pico_nodo = SM.get_peak_tension(let.orientacao[0], True)
        pico_saida = SM.get_peak_tension(let.orientacao[1])
        return (pico_nodo, pico_saida)

HSRunner = SpiceRunner()

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
