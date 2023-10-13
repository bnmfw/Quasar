from os import path
from typing import Any
from utils.spiceInterface import HSRunner
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
        while not path.exists(f"circuitos/{inputs['circ']}"):
            inputs["circ"] = input("Circuito nao encontrado na pasta 'circuitos' por favor insira um circuito valido:\n")

        # Informacao sobre o cadastro
        inputs["cadastro"] = path.exists(f"circuitos/{inputs['circ']}/{inputs['circ']}.json")
        if inputs["cadastro"]:    
            print("\nCadastro do circuito encontrado")
        else:
            print("\nCadastro do circuito nao encontrado, tera de ser feito")
        
        # Requisita o vdd
        default_voltage = 0.7
        voltage = input(f"Vdd [V] ({default_voltage}): ")
        inputs["vdd"] = default_voltage if voltage == "" else float(voltage)

        # Retorna as informacoes pertinentes
        next_screen = "main" if inputs["cadastro"] else "cadastro"
        return next_screen, inputs
    
    def tela_cadastro(self, circ_nome):
        inputs = {"nodos": None, "entradas": None, "saidas": None}
        print(barra_comprida)
        inputs["entradas"] = [entrada for entrada in input("Entradas de sinal: ").split()]
        inputs["saidas"] = [entrada for entrada in input("Saidas analisadas: ").split()]
        inputs["nodos"] = [nodo for nodo in HSRunner.get_nodes(circ_nome)[0]]
        return "main", inputs
    
    def tela_principal(self, circuito):
        acao = {0: "atualizar", 1: "csv", 2: "mc", 3: None}
        inputs = {"acao": None}
        print(barra_comprida)
        inputs["acao"] = acao[int(input(f"{barra_comprida}\n"
                    f"Trabalhando com o {circuito.name} em {circuito.vdd} volts\n"
                     "O que deseja fazer?\n"
                     "0. Atualizar LETs\n"
                     "1. Gerar CSV de LETs\n"
                     "2. Analise Monte Carlo\n"
                     "3. Sair\n"
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

        # Analise Monte Carlo
        elif inputs["acao"] == "mc":
            return "mc", inputs
    
    def tela_mc(self, circuito):
        inputs = {"progress": None, "n_sim": None, "continue": False, "window": None}

        # Continua simulacao onde parou se ha backup
        if path.exists(f"circuitos/{circuito.name}/MC_jobs.json"): 
            print("\nSimulacao em andamento encontrada, continuando de onde parou...\n")
            inputs["continue"] = True
            return "main", inputs
        
        default_n_sim = 2000
        n_sim = input(f"Numero de simulacoes ({default_n_sim} recomendado): ")
        inputs["n_sim"] = default_n_sim if n_sim == "" else int(n_sim)
        return "main", inputs