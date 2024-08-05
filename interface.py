# O python acha que tem um erro nesses imports, mas nao tem, deixa quieto
from src.backend import Backend
from src.spiceInterface.spiceInterface import HSRunner
from src.circuit.circuito import Circuito
from src.utils.arquivos import CManager
from src.simconfig.simulationConfig import sim_config
from os import sep, path
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
                circ_nome = inputs["circ"]
                cadastro = inputs["cadastro"]
                config_log = sim_config.load(f"circuitos{sep}{circ_nome}")
                if cadastro:
                    self.circuito = Circuito(circ_nome).from_json()
                    self.backend.set_circuit(self.circuito)
                elif not config_log:
                    _, inputs = self.ui.tela_config_sim(sim_config.vdd, 
                                                        sim_config.fault_model.colect_time, 
                                                        sim_config.fault_model.track_estab, 
                                                        sim_config.transistor_model.charge_collection_depth_nano,
                                                        sim_config.runner)
                    self.backend.set_sim_config(inputs["vdd"], inputs["alpha"], inputs["beta"], inputs["depth"], inputs["spice"], f"circuitos{sep}{circ_nome}")
 

            # TELA DE CADASTRO
            elif current_screen == "cadastro":
                
                current_screen, inputs = self.ui.tela_cadastro(circ_nome)
                self.circuito = Circuito(circ_nome).from_nodes(inputs["entradas"], inputs["saidas"])    
                print(self.circuito.nodes)
                self.backend.set_circuit(self.circuito)
                with HSRunner.Vdd(sim_config.vdd):
                    self.backend.determine_LETs(progress_report=self.ui.progress, log_circuit=True)

            # TELA PRINCIPAL
            elif current_screen == "main":
                current_screen, inputs = self.ui.tela_principal(self.circuito)
                if inputs["acao"] == "atualizar":
                    with HSRunner.Vdd(sim_config.vdd):
                        self.backend.determine_LETs(progress_report=self.ui.progress)
                elif inputs["acao"] == "csv":
                        CManager.write_full_csv(self.circuito, self.circuito.path_to_circuits)

            # TELA MONTE CARLO
            elif current_screen == "mc":
                current_screen, inputs = self.ui.tela_mc(self.circuito)
                with HSRunner.Vdd(sim_config.vdd):
                    self.backend.mc_analysis(inputs["n_sim"], inputs["continue"], inputs["progress"], self.ui.progress)
                if not inputs["window"] is None:
                    inputs["window"].close()

            # SINGLE LET SCREEN
            elif current_screen == "single_let":
                current_screen, inputs = self.ui.tela_single_let(self.circuito)
                with HSRunner.Vdd(sim_config.vdd):
                    self.backend.find_single_let(inputs["node"], inputs["output"], inputs["input"], *inputs["pulses"], inputs["pmos"], inputs["nmos"], inputs["report"])
            
            elif current_screen == "config_sim":
                current_screen, inputs = self.ui.tela_config_sim(sim_config.vdd, 
                                                                 sim_config.fault_model.colect_time, 
                                                                 sim_config.fault_model.track_estab, 
                                                                 sim_config.transistor_model.charge_collection_depth_nano,
                                                                 sim_config.runner)
                self.backend.set_sim_config(inputs["vdd"], inputs["alpha"], inputs["beta"], inputs["depth"], inputs["spice"], self.circuito.path_to_my_dir)
            
            # EXIT
            elif current_screen is None:
                break