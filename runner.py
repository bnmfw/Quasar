from arquivos import HSManager
from components import LET, Entrada
import os

class SpiceRunner():
    def __init__(self) -> None:
        self.test_spice()
        pass

    class Monte_Carlo():
        def __init__ (self, num_testes):
            self.num = num_testes

        def __enter__(self):
            HSManager.set_monte_carlo(self.num)

        def __exit__(self, type, value, traceback):
            HSManager.set_monte_carlo(0)

    class MC_Instance():
        def __init__ (self, pmos = None, nmos = None):
            self.pmos = pmos
            self.nmos = nmos

        def __enter__(self):
            HSManager.set_variability(self.pmos, self.nmos)

        def __exit__(self, type, value, traceback):
            HSManager.set_variability(None, None)

    class SET():
        def __init__ (self, let: LET, corrente: float = None):
            self.let = let
            if corrente == None:
                self.corrente = let.corrente
            else:
                self.corrente = corrente

        def __enter__(self):
            HSManager.set_pulse(self.let, self.corrente)
            HSManager.measure_pulse(self.let.nodo_nome, self.let.saida_nome)

        def __exit__(self, type, value, traceback):
            HSManager.set_pulse(self.let, 0)

    class Vdd():
        def __init__ (self, vdd: float, main_enviroment = False):
            self.vdd = vdd
            self.main = main_enviroment

        def __enter__(self):
            HSManager.set_vdd(self.vdd, main = self.main)

        def __exit__(self, type, value, traceback):
            pass

    class Inputs():
        def __init__ (self, vdd: float, entradas: list):
            self.vdd = vdd
            self.entradas = {}
            for entrada in entradas:
                self.entradas[entrada.nome] = entrada.sinal

        def __enter__(self):
            HSManager.set_signals(self.vdd, self.entradas)

        def __exit__(self, type, value, traceback):
            pass

    def test_spice(self) -> bool:
        print("Python OK")
        os.system(f"hspice empty.cir > output.txt")
        with open("output.txt", "r") as file:
            for linha in file:
                if "Cannot connect to license server system" in linha:
                    exit("HSPICE LicenseError: Cannot connect to license server system")
        print("HSPICE OK")
    
    def default(self, vdd: float) -> None:
        HSManager.set_vdd(vdd, main=True)
        HSManager.set_pulse(LET(0, vdd, "none", "none", [None, None]), main = True)
        HSManager.set_monte_carlo(0, main=True)

    def get_nodes(self, circ_name: str):
        return HSManager.get_nodes(circ_name)

    def run_delay(self, path: str, filename: str, entrada_nome: str, saida_nome: str, vdd: float, entradas: list) -> float:
        HSManager.measure_delay(entrada_nome, saida_nome, vdd)
        entradas_dicionario = {}
        for entrada in entradas:
            entradas_dicionario[entrada.nome] = entrada.sinal
        HSManager.set_signals(vdd, entradas_dicionario)
        os.system(f"cd circuitos_{os.getpid()}{path} ; hspice {filename}| grep \"atraso_rr\|atraso_rf\|atraso_fr\|atraso_ff\" > ../output.txt")
        delay = HSManager.get_delay()
        return delay

    def run_SET(self, path: str, filename: str, let: LET, corrente = None) -> tuple:
        with self.SET(let, corrente):
            os.system(f"cd circuitos_{os.getpid()}{path} ; hspice {filename} | grep \"minout\|maxout\|minnod\|maxnod\" > ../output.txt")
            pico_nodo = HSManager.get_peak_tension(let.orientacao[0], True)
            pico_saida = HSManager.get_peak_tension(let.orientacao[1])
        return (pico_nodo, pico_saida)
    
    def run_tensions(self, path: str, filename: str, nodo_nome: str) -> float:
        HSManager.measure_tension(nodo_nome)
        os.system(f"cd circuitos_{os.getpid()}{path} ; hspice {filename} | grep \"minnod\|maxnod\" > ../output.txt")
        tensao = HSManager.get_tension()
        return tensao

    def run_pulse_width(self, path:str, filename: str, let: LET, corrente: float):
        output: dict = {}
        # print(f"corrente: {corrente}")
        with self.SET(let, corrente):
            HSManager.measure_pulse_width(let)
            os.system(f"cd circuitos_{os.getpid()}{path} ; hspice {filename} | grep \"larg\" > ../output.txt")
            output = HSManager.get_output()
        # print(f"output: {output}")

        try:
            if output["larg"].value == None:
                return None

            return abs(output["larg"].value)
        except KeyError:
            return None

    def run_simple_MC(self, path: str, circuit_name: str, nodo_nome: str, saida_nome: str, analises: int, pulso_out: str, vdd: float) -> int:
        HSManager.measure_pulse(nodo_nome, saida_nome)
        with self.Monte_Carlo(analises):
            os.system(f"cd circuitos_{os.getpid()}{path} ; hspice {circuit_name}.cir| grep \"minout\|maxout\" > ../output.txt")
        return HSManager.get_mc_faults(path, circuit_name, analises, pulso_out, vdd)

    def run_MC_var(self, path: str, filename: str, cir_nome: str, analises: int) -> dict:
        with self.Monte_Carlo(analises):
            os.system(f"cd circuitos_{os.getpid()}{path} ; hspice {filename} > ../output.txt")
        return HSManager.get_mc_instances(path, cir_nome, analises)

HSRunner = SpiceRunner()