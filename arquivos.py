from matematica import *
from components import Nodo, Entrada, LET
from dataclasses import dataclass
import json
import os

analise_manual = False

class SpiceManager():
    def __init__(self):
        self.output: dict = None

    def __write_peak_meas(self, arquivo, label: str, peak: str, grandeza: str, node: str, start: float, finish: float):
        if not peak in {"min", "max"}:
            raise ValueError("pico eh min ou max")
        if not grandeza in {"i", "V"}:
            raise ValueError("grandeza nao esta em i ou V")
         
        arquivo.write(f".meas tran {label} {peak} {grandeza}({node}) from={start}n to={finish}n\n")

    def __write_trig_meas(self, arquivo, label: str, trig: str, trig_value: float, trig_inclin: str,
     targ: str, targ_value: float, targ_inclin: str):

        arquivo.write(f".meas tran {label} TRIG v({trig}) val='{trig_value}' {trig_inclin}=1 TARG v({targ}) val='{targ_value}' {targ_inclin}=1\n")
    
    def measure_pulse(self, nodo: str, saida: str):
        with open("circuitos/include/measure.cir", "w") as arquivo:
            arquivo.write("*Arquivo com os measures usados\n")

            self.__write_peak_meas(arquivo, "minout", "min", "V", saida, 1.0, 3.8)
            self.__write_peak_meas(arquivo, "maxout", "max", "V", saida, 1.0, 3.8)
            self.__write_peak_meas(arquivo, "minnod", "min", "V", nodo, 1.0, 3.8)
            self.__write_peak_meas(arquivo, "maxnod", "max", "V", nodo, 1.0, 3.8)

    def measure_tension(self, nodo: str):
        with open("circuitos/include/measure.cir", "w") as arquivo:
            arquivo.write("*Arquivo com os measures usados\n")
            self.__write_peak_meas(arquivo, "minnod", "min", "V", nodo, 1.0, 3.8)
            self.__write_peak_meas(arquivo, "maxnod", "max", "V", nodo, 1.0, 3.8) 
    
    # Escreve vdd no arquivo "vdd.cir"
    @staticmethod
    def set_vdd(vdd: float):
        with open("circuitos/include/vdd.cir", "w") as arquivo_vdd:
            arquivo_vdd.write("*Arquivo com a tensao usada por todos os circuitos\n")
            arquivo_vdd.write(f"Vvdd vdd gnd {vdd}\n")
            arquivo_vdd.write(f"Vvcc vcc gnd {vdd}\n")
            arquivo_vdd.write(f"Vclk clk gnd PULSE(0 {vdd} 1n 0.01n 0.01n 1n 2n)")

    # Escreve os sinais no arquivo "fontes.cir"
    @staticmethod
    def set_signals(vdd: float, entradas: dict):
        with open("circuitos/include/fontes.cir", "w") as sinais:
            sinais.write("*Fontes de sinal a serem editadas pelo roteiro\n")

            # Escreve o sinal analogico a partir do sinal logico
            for entrada, nivel in entradas.items():
                sinais.write(f"V{entrada} {entrada} gnd ")
                if nivel == 1:
                    sinais.write(f"{vdd}\n")
                elif nivel == 0:
                    sinais.write("0.0\n")
                elif nivel == "atraso":
                    sinais.write(f"PWL(0n 0 1n 0 1.01n {vdd} 3n {vdd} 3.01n 0)\n")
                else:
                    raise ValueError("ERRO SINAL NAO IDENTIFICADO RECEBIDO: ", nivel)

    # Escreve informacoes no arquivo "SETs.cir"
    def set_pulse(self, let: LET, corrente = None):
        if not let.orientacao[0] in {"fall", "rise", None}:
            raise ValueError("Nao recebi fall ou rise como inclincacao do pulso")
        if corrente == None:
            corrente = let.corrente

        with open("circuitos/include/SETs.cir", "w") as sets:
            sets.write("*SETs para serem usados nos benchmarks\n")
            if not let.orientacao[0] == "rise": sets.write("*")
            sets.write(f"Iseu gnd {let.nodo_nome} EXP(0 {corrente}u 2n 50p 164p 200p) //rise\n")
            if not let.orientacao[0] == "fall": sets.write("*")
            sets.write(f"Iseu {let.nodo_nome} gnd EXP(0 {corrente}u 2n 50p 164p 200p) //fall\n")

    # Altera o arquivo "measure.cir"
    def measure_delay(self, input: str, out: str, vdd: float):
        with open("circuitos/include/measure.cir", "w") as arquivo:
            arquivo.write("*Arquivo com atraso a ser medido\n")
            tensao = str(vdd / 2)
            self.__write_trig_meas(arquivo, "atraso_rr", input, tensao, "rise", out, tensao, "rise")
            self.__write_trig_meas(arquivo, "atraso_rf", input, tensao, "rise", out, tensao, "fall")
            self.__write_trig_meas(arquivo, "atraso_ff", input, tensao, "fall", out, tensao, "fall")
            self.__write_trig_meas(arquivo, "atraso_fr", input, tensao, "fall", out, tensao, "rise")
            # self.__write_trig_meas(arquivo, "largura", out, tensao, "fall", out, tensao, "rise")

    # Altera o arquivo "measure.cir"
    def measure_pulse_width(self, let: LET):
        with open("circuitos/include/measure.cir", "w") as arquivo:
            arquivo.write("*Arquivo com a leitura da largura dos pulsos\n")
            tensao = str(let.vdd * 0.5)
            self.__write_trig_meas(arquivo, "larg", let.nodo_nome, tensao, "rise", let.nodo_nome, tensao, "fall")

    # Altera o valor de simulacoes monte carlo a serem feitas
    @staticmethod
    def set_monte_carlo(simulacoes: int):
        with open("circuitos/include/monte_carlo.cir", "w") as mc:
            mc.write("*Arquivo Analise Monte Carlo\n")
            mc.write(".tran 0.01n 4n")
            if simulacoes: mc.write(f" sweep monte={simulacoes}")

    # Altera o arquivo "mc.cir"
    @staticmethod
    def set_variability(pvar = None, nvar = None):
        with open ("circuitos/include/mc.cir","w") as mc:
            if pvar == None or nvar == None:
                mc.write("* Analise MC\n"
                ".param phig_var_p = gauss(4.8108, 0.05, 3)\n"
                ".param phig_var_n = gauss(4.372, 0.05, 3)")
            else:
                mc.write("* Analise MC\n"
                f".param phig_var_p = {pvar}\n"
                f".param phig_var_n = {nvar}")

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

    # Le nodos de um circuito
    def get_nodes(self, circuit_name: str) -> set:
        nodos = {"vdd", "gnd"}
        with open(f"circuitos/{circuit_name}/{circuit_name}.cir", "r") as file:
            for linha in file:
                if "M" in linha:
                    _, coletor, base, emissor, _, _, _ = linha.split()
                    for nodo in [coletor, base, emissor]:
                        nodos.add(nodo)
        return nodos

    # Le measures no arquivo output.txt e retorna um dicionario
    def get_output(self) -> dict:
        saida: dict = {"None": None}
        with open("output.txt", "r") as output:
            for linha in output:
                self.__format_output_line(linha, saida)
        self.output = saida
        return saida
    
    # Recupera a tensao de pico
    def get_peak_tension(self, inclinacao: str, nodMeas: bool = False) -> float:
        if not inclinacao in {"fall", "rise"}:
            raise ValueError(f"Inclinacao com valor nao admitido: {inclinacao}")

        output = self.get_output()

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

    def get_tension(self) -> float:
        output = self.get_output()
        max: float = output["maxnod"].value
        min: float = output["minnod"].value
        # if max - min > 0.05:
        #     raise RuntimeError(f"Circuito sem pulsos tem muita variacao {max} {min}")
        return (max, min)
    
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

    def get_mc_faults(self, path: str, circuit_name: str, num_analises: int, inclinacao_saida: str, vdd: float) -> int:
        
        falhas: int = 0

        dados: dict = self.__get_csv_data(f"{path}{circuit_name}.mt0.csv", ".TITLE")

        inclinacao_corr = "mincor" if inclinacao_saida == "fall" else "maxcor"
        inclinacao_tens = "minout" if inclinacao_saida == "fall" else "maxout"

        for i in range(num_analises):
            # corrente_pico = dados[inclinacao_corr][i]
            tensao_pico = dados[inclinacao_tens][i]

            if inclinacao_saida == "fall" and tensao_pico < vdd / 2 or\
                inclinacao_saida == "rise" and tensao_pico > vdd / 2:
                falhas += 1
        return falhas

    # Le o atraso do nodo a saida no arquivo "output.txt"
    def get_delay(self) -> float:

        output = self.get_output()
        # print(output)

        atrasos: list = [output["atraso_rr"].value, output["atraso_ff"].value, output["atraso_rf"].value, output["atraso_fr"].value]
        # Erro
        if None in atrasos:
            return 0
        
        # Sorting
        for i, atraso in enumerate(atrasos):
            atrasos[i] = abs(atraso)
        atrasos.sort()
        return atrasos[1]
    
    # Leitura das instancias do arquivo "<circuito>.mc0.csv"
    def get_mc_instances(self, path, filename: str, simulacoes: int) -> dict:
        instancias: dict = {}

        dados = self.__get_csv_data(f"{path}{filename}.mc0.csv", "$ IRV")

        ps: str = "pmos_rvt:@:phig_var_p:@:IGNC"
        ns: str = "nmos_rvt:@:phig_var_n:@:IGNC"

        for i, pmos, nmos in zip(dados["index"], dados[ps], dados[ns]):
            instancias[i] = [float(pmos), float(nmos)]
        return instancias

class CSVManager():
    def __init__(self):
        pass

    @staticmethod
    def tup_dict_to_csv(path: str, filename: str, dicionario: dict):
        with open(f"{path}{filename}", "w") as tabela:
            for chave, tupla in dicionario.items():
                tabela.write(f"{chave}")
                for valor in tupla:
                    tabela.write(f",{valor}")
                tabela.write("\n")

        print(f"\nTabela {filename} gerada com sucesso\n")

    @staticmethod
    def escrever_csv_total(circuito):
        linha = 2
        with open(f"circuitos/{circuito.nome}/{circuito.nome}.csv", "w") as sets:
            sets.write("Nodo,Saida,Pulso,Pulso,Corrente,LETs,Num Val,Validacoes->\n")
            for nodo in circuito.nodos:
                for let in nodo.LETs:
                    c0, c1 = let.orientacao
                    sets.write(f"{nodo.nome},{let.saida_nome},{c0},{c1},{let.corrente:.2f},{let.valor:.2e},{len(let)}")
                    for validacao in let.validacoes:
                        sets.write(",'")
                        for num in validacao: sets.write(f"{num}")
                    sets.write("\n")
                    linha += 1
        print(f"\nTabela {circuito.nome}.csv gerada com sucesso\n")

    @staticmethod
    def escrever_csv_comparativo(circuito, lista_comparativa):
        with open(f"circuitos/{circuito.nome}/{circuito.nome}_compara.csv", "w") as tabela:
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

        if not os.path.exists(f"circuitos/{circuito.nome}/{circuito.nome}.json"):
            json.dump(circuito_codificado, open(f"circuitos/{circuito.nome}/{circuito.nome}.json", "w"))

        print("Carregamento do Json realizado com sucesso")

    def decodificar(self, circuito):
        circuito_codificado: dict = json.load(open(f"circuitos/{circuito.nome}/{circuito.nome}.json", "r"))

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

# Instancias

HSManager = SpiceManager()
JManager = JsonManager()
CManager = CSVManager()