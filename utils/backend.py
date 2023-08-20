from .circuito import Circuito
from .circuitManager import CircuitManager
from .mcManager import MCManager
from .arquivos import JManager, CManager
from .matematica import InDir

class Backend:

    def __init__(self) -> None:
        self.circuito = None
        self.vdd = None

    def set(self, circuito: Circuito, vdd: float):
        self.circuito = circuito
        self.vdd = vdd
        return self

    # def __exit__(self, type, value, traceback):
    #     self.circuito = None
    #     self.vdd = None

    def check_circuit(self):
        if self.circuito is None:
            raise ValueError("Circuito nao informado")

    def determinar_lets(self, delay: bool = False, report: bool = False):
        self.check_circuit()
        CircuitManager(self.circuito, report=report).determinar_LETths(delay=delay)
        JManager.codificar(self.circuito, self.circuito.path_to_circuits)
    
    def atualizar_lets(self, delay: bool = False, report: bool = False):
        self.check_circuit()
        CircuitManager(self.circuito, report=report).atualizar_LETths(delay=delay)
        JManager.codificar(self.circuito, self.circuito.path_to_circuits)

    def criar_let_csv(self):
        self.check_circuit()
        CManager.escrever_csv_total(self.circuito)
    
    def analise_mc(self, n_simu: int, continuar:bool = False, delay:bool = False, progress_report = None):
        self.check_circuit()
        MCManager(self.circuito).analise_monte_carlo_total(n_simu, continue_backup=continuar, delay=delay, progress_report=progress_report)

if __name__ == "__main__":

    print("Testing Backend...")

    with InDir("debug"):

        # fadder: Circuito = Circuito("fadder", "test_crcuits", 0.7).from_json()
        # backend: Backend = Backend.set(fadder, 0.7)

        # print("\tTesting LETth determination...")
        # backend.determinar_lets()


        # fadder = Circuito("fadder", "test_circuits", 0.7).from_nodes(["a", "b", "cin"], ["cout", "sum"], {"na", "nb", "ncin", "gate_p16", "gate_p15", "gate_q16", "gate_q15", "drain_p16", "drain_p15", "drain_q16", "drain_q15", "ncout", "nsum", "a1", "b1", "cin1"})
        fadder = Circuito("fadder", "test_circuits", 0.7).from_json()
        fadder.nodos.sort(key=lambda e: e.nome)
        backend = Backend().set(fadder, 0.7)
        backend.analise_mc(1000)