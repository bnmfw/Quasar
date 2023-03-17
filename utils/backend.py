from .circuito import Circuito
from .circuitManager import CircuitManager
from .mcManager import MCManager
from .arquivos import JManager, CManager

class Backend:

    def __init__(self) -> None:
        self.circuito = None
        self.vdd = None

    def set(self, circuito: Circuito, vdd: float):
        self.circuito = circuito
        self.vdd = vdd

    # def __exit__(self, type, value, traceback):
    #     self.circuito = None
    #     self.vdd = None

    def check_circuit(self):
        if self.circuito is None:
            raise ValueError("Circuito nao informado")

    def determinar_lets(self, delay: bool = False):
        self.check_circuit()
        CircuitManager(self.circuito).determinar_LETths(delay=delay)
        JManager.codificar(self.circuito)
    
    def atualizar_lets(self, delay: bool = False):
        self.check_circuit()
        CircuitManager(self.circuito).atualizar_LETths(delay=delay)
        JManager.codificar(self.circuito)

    def criar_let_csv(self):
        self.check_circuit()
        CManager.escrever_csv_total(self.circuito)
    
    def analise_mc(self, n_simu: int, continuar:bool = False, delay:bool = False, progress_report = None):
        self.check_circuit()
        MCManager(self.circuito).analise_monte_carlo_total(n_simu, continuar=continuar, delay=delay, progress_report=progress_report)