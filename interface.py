# O python acha que tem um erro nesses imports, mas nao tem, deixa quieto
from utils.backend import Backend
from utils.spiceInterface import HSRunner
from utils.circuito import Circuito
from utils.arquivos import CManager
# module_error = False
try:
    from psgui import PSGUI, psgui_is_working, gui_error
except ModuleNotFoundError:
    psgui_is_working = True
from txtui import TXTUI

psgui_is_working = False
gui_error = "Manual Error"

class GUI:
    def __init__(self) -> None:
        self.backend = Backend()

        # Determina a interface a ser usada
        if psgui_is_working:
            self.ui = PSGUI()
        else:
            print("\nUm problema foi encontrado com o modulo psgui:\n"
                  f"{gui_error}\n"
                  "portanto a interface de texto sera usada em seu lugar")
            self.ui = TXTUI()

        current_screen = "start"

        circ_nome: str = None
        self.circuito: Circuito = None
        vdd: float = None
        cadastro: bool = None

        # Loop de execucao para um circuito
        while True:

            # TELA INICIAL
            if current_screen == "start":

                # Inputs: vdd, circ, cadastro
                current_screen, inputs = self.ui.tela_inicial()
                vdd = inputs["vdd"]
                circ_nome = inputs["circ"]
                cadastro = inputs["cadastro"]
                if cadastro:
                    self.circuito = Circuito(circ_nome, vdd=vdd).from_json()
                    self.backend.set_circuit(self.circuito,vdd)

            # TELA DE CADASTRO
            elif current_screen == "cadastro":
                
                current_screen, inputs = self.ui.tela_cadastro(circ_nome)
                self.circuito = Circuito(circ_nome, vdd=vdd).from_nodes(inputs["entradas"], inputs["saidas"])    
                print(self.circuito.nodes)
                self.backend.set_circuit(self.circuito,vdd)
                with HSRunner.Vdd(vdd):
                    self.backend.determine_LETs()

            # TELA PRINCIPAL
            elif current_screen == "main":
                current_screen, inputs = self.ui.tela_principal(self.circuito)
                if inputs["acao"] == "atualizar":
                    with HSRunner.Vdd(vdd):
                        self.backend.update_lets()
                elif inputs["acao"] == "csv":
                        CManager.write_full_csv(self.circuito, self.circuito.path_to_circuits)

            # TELA MONTE CARLO
            elif current_screen == "mc":
                current_screen, inputs = self.ui.tela_mc(self.circuito)
                with HSRunner.Vdd(vdd):
                    self.backend.mc_analysis(inputs["n_sim"], inputs["continue"], inputs["progress"], self.ui.progress)
                if not inputs["window"] is None:
                    inputs["window"].close()

            # EXIT
            elif current_screen is None:
                break