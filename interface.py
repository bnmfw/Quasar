# O python acha que tem um erro nesses imports, mas nao tem, deixa quieto
from utils.backend import Backend
from utils.runner import HSRunner
from utils.circuito import Circuito
from utils.arquivos import CManager
from psgui import PSGUI, psgui_is_working, gui_error
from txtui import TXTUI

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
                    self.circuito = Circuito(circ_nome, vdd).from_json()
                    self.backend.set(self.circuito,vdd)
                    with HSRunner.Vdd(vdd):
                        self.backend.atualizar_lets()

            # TELA DE CADASTRO
            elif current_screen == "cadastro":
                
                current_screen, inputs = self.ui.tela_cadastro(circ_nome)
                self.circuito = Circuito(circ_nome, vdd).from_nodes(inputs["nodos"], inputs["entradas"], inputs["saidas"])    
                self.backend.set(self.circuito,vdd)
                with HSRunner.Vdd(vdd):
                    self.backend.determinar_lets()

            # TELA PRINCIPAL
            elif current_screen == "main":
                current_screen, inputs = self.ui.tela_principal(self.circuito)
                if inputs["acao"] == "atualizar":
                    with HSRunner.Vdd(vdd):
                        self.backend.atualizar_lets()
                elif inputs["acao"] == "csv":
                        CManager.escrever_csv_total(self.circuito)

            # TELA MONTE CARLO
            elif current_screen == "mc":
                current_screen, inputs = self.ui.tela_mc(self.circuito)
                with HSRunner.Vdd(vdd):
                    self.backend.analise_mc(inputs["n_sim"], inputs["continue"], inputs["progress"])
                if not inputs["window"] is None:
                    inputs["window"].close()

            elif current_screen is None:
                break

g = GUI()