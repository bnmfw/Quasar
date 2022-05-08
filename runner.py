from arquivos import HSManager
from components import LET
import os

class SpiceRunner():
    def __init__(self) -> None:
        pass

    class Monte_Carlo(object):
        def __init__ (self, num_testes):
            self.num = num_testes

        def __enter__(self):
            HSManager.set_monte_carlo(self.num)

        def __exit__(self, type, value, traceback):
            HSManager.set_monte_carlo(0)

    class MC_Instance(object):
        def __init__ (self, pmos = None, nmos = None):
            self.pmos = pmos
            self.nmos = nmos

        def __enter__(self):
            HSManager.set_variability(self.pmos, self.nmos)

        def __exit__(self, type, value, traceback):
            HSManager.set_variability(None, None)

    class SET(object):
        def __init__ (self, let: LET, corrente: float = None):
            self.let = let
            if corrente == None:
                self.corrente = let.corrente
            else:
                self.corrente = corrente

        def __enter__(self):
            HSManager.set_pulse(self.let, self.corrente)

        def __exit__(self, type, value, traceback):
            HSManager.set_pulse(self.let, 0)

    def default(self, vdd: float) -> None:
        HSManager.set_vdd(vdd)
        HSManager.set_pulse(LET(0, vdd, "none", "none", "fr"))
        HSManager.set_monte_carlo(0)

    def configure_pulse(self, let: LET, corrente = None) -> None:
        HSManager.set_pulse(let, corrente)
        HSManager.set_pulse_measure(let.nodo_nome, let.saida_nome)

    def configure_input(self, vdd: float, entradas: list):
        HSManager.set_signals(vdd, entradas)

    def configure_SET(self, let: LET, vdd: float, entradas: list, corrente: float = None):
        self.configure_input(vdd, entradas)
        self.configure_pulse(let, corrente)

    def run_delay(self, path: str, filename: str, entrada_nome: str, saida_nome: str, vdd: float, entradas: list) -> float:
        HSManager.set_delay_measure(entrada_nome, saida_nome, vdd)
        HSManager.set_signals(vdd, entradas)
        os.system(f"cd {path} ; hspice {filename}| grep \"atraso_rr\|atraso_rf\|atraso_fr\|atraso_ff\" > ../../output.txt")
        return HSManager.get_delay()

    def run_SET(self, path: str, filename: str, let: LET, corrente = None) -> tuple:
        with self.SET(let, corrente):
            HSManager.set_pulse_measure(let.nodo_nome, let.saida_nome)
            os.system(f"cd {path} ; hspice {filename} | grep \"minout\|maxout\|minnod\|maxnod\" > ../../output.txt")
            pico_nodo = HSManager.get_peak_tension(let.orientacao[0], True)
            pico_saida = HSManager.get_peak_tension(let.orientacao[1])
        return (pico_nodo, pico_saida)

    def run_pulse_width(self, path:str, filename: str, let: LET, corrente: float):
        HSManager.set_pulse(let, corrente)
        HSManager.set_pulse_width_measure(let)

        os.system(f"cd {path} ; hspice {filename} | grep \"larg\" > ../../output.txt")

        output: dict = {}
        HSManager.get_output(output)

        if output["larg"].value == None:
            return None

        return abs(output["larg"].value)

    def run_simple_MC(self, path: str, circuit_name: str, nodo_nome: str, saida_nome: str, analises: int, pulso_out: str, vdd: float) -> int:
        HSManager.set_pulse_measure(nodo_nome, saida_nome)
        with self.Monte_Carlo(analises):
            os.system(f"cd {path} ; hspice {circuit_name}.cir| grep \"minout\|maxout\" > ../../output.txt")
        return HSManager.get_mc_faults(path, circuit_name, analises, pulso_out, vdd)

    def run_MC_var(self, path: str, filename: str, cir_nome: str, analises: int) -> dict:
        with self.Monte_Carlo(analises):
            os.system(f"cd {path} ; hspice {filename} > ../../output.txt")
        return HSManager.get_mc_instances(path, cir_nome, analises)


HSRunner = SpiceRunner()