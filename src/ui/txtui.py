from os import path
from typing import Any
from ..spiceInterface.spiceRunner import HSRunner, HSpiceRunner, NGSpiceRunner
from ..simconfig.simulationConfig import sim_config
from progress.bar import Bar

barra_comprida = "---------------------------"

class Progress_Bar:
    def __init__(self):
        self.alive: bool = False

    def start(self):
        self.bar = Bar('Processing...')
        self.progress: int = 0
        self.alive = True
        self.bar.next(0)

    def update(self, progress: float):
        if not self.alive: self.start()
        floor = int(100*progress)
        for _ in range(floor-self.progress):
            self.bar.next()
        self.progress = floor

class TXTUI:
    def __init__(self) -> None:
        self.bar = Progress_Bar()

    # Progress bar
    def progress(self, value: float):
        if (value == -1):
            print()
            self.bar = Progress_Bar()
        else:
            self.bar.update(value)
    
    # Tela inicial onde um circuito é escolhido
    def tela_inicial(self):
        # Inputs do usuario que serao retornados
        next_screen = None
        inputs = {"vdd": None, "circ": None, "cadastro": None}

        # Circuito a ser analisado
        print(barra_comprida)
        inputs["circ"] = input("Circuito a ser analisado: ")
        while not path.exists(path.join("project","circuits",f"{inputs['circ']}")):
            inputs["circ"] = input("Circuito nao encontrado na pasta 'circuitos' por favor insira um circuito valido:\n")

        # Informacao sobre o cadastro
        inputs["cadastro"] = path.exists(path.join("project","circuits",f"{inputs['circ']}",f"{inputs['circ']}.json"))
        if inputs["cadastro"]:    
            print("\nCadastro do circuito encontrado")
        else:
            print("\nCadastro do circuito nao encontrado, tera de ser feito")
            print("Configure simulation before determining SETs:")
        
        # Requisita o vdd
        # default_voltage = 0.7
        # voltage = input(f"Vdd [V] ({default_voltage}): ")
        # inputs["vdd"] = default_voltage if voltage == "" else float(voltage)

        # Retorna as informacoes pertinentes
        next_screen = "main" if inputs["cadastro"] else "cadastro"
        return next_screen, inputs
    
    def tela_cadastro(self, circ_nome):
        inputs = {"nodos": None, "entradas": None, "saidas": None}
        print(barra_comprida)
        inputs["entradas"] = [entrada.lower() for entrada in input("Entradas de sinal: ").split()]
        inputs["saidas"] = [entrada.lower() for entrada in input("Saidas analisadas: ").split()]
        inputs["nodos"] = [nodo for nodo in HSRunner.get_nodes(circ_nome)[0]]
        return "main", inputs
    
    def tela_principal(self, circuito):
        acao = {0: "atualizar", 1: "csv", 2: "mc", 3: "single_let", 4: "config_sim", 5: None}
        inputs = {"acao": None}
        print(barra_comprida)
        if sim_config.runner_type == NGSpiceRunner: print("Using NGSPICE")
        elif sim_config.runner_type == HSpiceRunner and not sim_config.runner.test_spice(): print("Using HSPICE")
        else: print("HSPICE NOT WORKING, SIMULATOR MUST BE CHANGED")
        inputs["acao"] = acao[int(input(
                    f"Trabalhando com o {circuito.name} em {sim_config.vdd} volts\n"
                    f"Modelo de falhas: alpha={sim_config.fault_model.colect_time} beta={sim_config.fault_model.track_estab}\n"
                    f"Transistor com profundidade em {sim_config.transistor_model.charge_collection_depth_nano}\n"
                    "O que deseja fazer?\n"
                    "0. Atualizar LETs\n"
                    "1. Gerar CSV de LETs\n"
                    "2. Analise Monte Carlo\n"
                    "3. Analisar LET unico\n"
                    "4. Configurar Simulacao\n"
                    "5. Sair\n"
                    "Resposta: "))]

        # Encerra o Quasar
        if inputs["acao"] is None:
            return None, inputs
        
        # Atualiza os LETs do circuito
        if inputs["acao"] == "atualizar":
            return "main", inputs

        # Escreve um CSV com os LETs do circuito
        if inputs["acao"] == "csv":
            return "main", inputs

        if inputs["acao"] == "single_let":
            return "single_let", inputs
        
        # Analise Monte Carlo
        if inputs["acao"] == "mc":
            return "mc", inputs
        
        if inputs["acao"] == "config_sim":
            return "config_sim", inputs
    
    def tela_mc(self, circuito):
        inputs = {"progress": None, "n_sim": 2000, "continue": False, "window": None}

        # Continua simulacao onde parou se ha backup
        if path.exists(path.join("project","circuits",f"{circuito.name}","MC_jobs.json")): 
            print("\nSimulacao em andamento encontrada, continuando de onde parou...\n")
            inputs["continue"] = True
            return "main", inputs
        
        n_sim = input(f"Numero de simulacoes ({inputs['n_sim']} recomendado): ")
        if n_sim != "": inputs["n_sim"] = int(n_sim)
        return "main", inputs

    def tela_single_let(self, circuit):
        inputs = {"node": None, "output": None, "input": None, "pulses": [None, None],"pmos": 4.8108, "nmos": 4.372, "report": True, "window": None}
        # Node
        inputs["node"] = input(f"Nodo atingido {list(map(lambda n: n.name, circuit.nodes))}: ")
        while inputs["node"] not in list(map(lambda n: n.name, circuit.nodes)):  inputs["node"] = input("Nodo invalido, insira novamente: ")
        # Output
        inputs["output"] = input(f"Nodo propagado {list(map(lambda n: n.name, circuit.nodes))}: ")
        while inputs["output"] not in list(map(lambda n: n.name, circuit.nodes)):  inputs["output"] = input("Nodo invalido, insira novamente: ")
        # Input signals
        inputs["input"] = [int(s) for s in input(f"Sinais de entrada em 0s e 1s <{', '.join(map(lambda n: n.name, circuit.inputs))}>: ").split()]
        # Pulses
        pulse = input("Pulses [rise or fall]: ")
        if pulse != "": inputs["pulses"] = pulse.split()
        # Pmos e Nmos
        var = input(f"Pmos e Nmos Var (4.8108, 4.372): ")
        if var != "": inputs["pmos"], inputs["nmos"] = [float(v) for v in var.split()]
        print(barra_comprida + "\n")
        return "main", inputs
    
    def tela_config_sim(self, vdd, colect_time, track_estab, depth, spice):
        inputs = {"vdd": vdd, "alpha": colect_time, "beta": track_estab, "depth": depth, "spice": spice}
        vdd = input(f"Vdd [V] ({vdd}): ")
        if vdd != "": inputs["vdd"] = float(vdd)
        colect_time = input(f"Charge Collect Time [ps] ({colect_time}): ")
        if colect_time != "": inputs["alpha"] = float(colect_time)
        track_estab = input(f"Track Establishment Time [ps] ({track_estab}): ")
        if track_estab != "": inputs["beta"] = float(track_estab)
        depth = input(f"Transistor Collection Depth [nm] ({depth}): ")
        if depth != "": inputs["depth"] = float(depth)
        spice = input(f"Simulator to be used ({'NGSPICE' if sim_config.runner_type == NGSpiceRunner else 'HSPICE'}): ")
        if spice != "": inputs["spice"] = NGSpiceRunner if spice == "NGSPICE" else HSpiceRunner
        return "main", inputs