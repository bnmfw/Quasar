from os import path
from ..spiceInterface.spiceRunner import HSRunner, HSpiceRunner, NGSpiceRunner
from ..variability.distribution import SpiceGaussianDist
from ..simconfig.simulationConfig import sim_config
from progress.bar import Bar

barra_comprida = "---------------------------"


class Progress_Bar:
    def __init__(self):
        self.alive: bool = False

    def start(self):
        self.bar = Bar("Processing...")
        self.progress: int = 0
        self.alive = True
        self.bar.next(0)

    def update(self, progress: float):
        if not self.alive:
            self.start()
        floor = int(100 * progress)
        for _ in range(floor - self.progress):
            self.bar.next()
        self.progress = floor


class TXTUI:
    def __init__(self) -> None:
        self.bar = Progress_Bar()

    # Progress bar
    def progress(self, value: float):
        if value == -1:
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
        inputs["circ"] = input("Analyzed Circuit: ")
        while not path.exists(path.join("project", "circuits", f"{inputs['circ']}")):
            inputs["circ"] = input(
                "Circuit not found on 'project circuito' folder, please insert a valid circuit name:\n"
            )

        # Informacao sobre o cadastro
        inputs["cadastro"] = path.exists(
            path.join(
                "project", "circuits", f"{inputs['circ']}", f"{inputs['circ']}.json"
            )
        )
        if inputs["cadastro"]:
            print("\nCircuit log found")
        else:
            print("\nCircuit log not found, input bacis info")
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
        inputs["entradas"] = [
            entrada.lower() for entrada in input("Signal Inputs: ").split()
        ]
        inputs["saidas"] = [
            entrada.lower() for entrada in input("Outputs analyzed: ").split()
        ]
        inputs["nodos"] = [nodo for nodo in HSRunner.get_nodes(circ_nome)[0]]
        return "main", inputs

    def tela_principal(self, circuito):
        acao = {
            0: "atualizar",
            1: "csv",
            2: "mc",
            3: "single_let",
            4: "config_sim",
            5: None,
        }
        inputs = {"acao": None}
        print(barra_comprida)
        if sim_config.runner_type == NGSpiceRunner:
            print("Using NGSPICE")
        elif (
            sim_config.runner_type == HSpiceRunner
            and not sim_config.runner.test_spice()
        ):
            print("Using HSPICE")
        else:
            print("HSPICE NOT WORKING, SIMULATOR MUST BE CHANGED")
        inputs["acao"] = acao[
            int(
                input(
                    f"Working with {circuito.name} in {sim_config.vdd} volts\n"
                    f"Fault Model: alpha={sim_config.fault_model.colect_time} beta={sim_config.fault_model.track_estab}\n"
                    f"Transistor colection depth: {sim_config.transistor_model.charge_collection_depth_nano}\n"
                    "What to do?\n"
                    "0. Update LETs\n"
                    "1. Generate LETs CSV\n"
                    "2. Variability Analysis\n"
                    "3. Analyze a single Fault Configuration\n"
                    "4. Configure Simulation\n"
                    "5. Exit\n"
                    "Choice: "
                )
            )
        ]

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
        inputs = {
            "progress": None,
            "n_sim": 2000,
            "distribution": [],
            "continue": False,
            "window": None,
        }

        # Allows to continue from backup
        if path.exists(
            path.join("project", "circuits", f"{circuito.name}", "MC_jobs.json")
        ):
            print("\nOngoing simulation found, continuing from where it stopped...\n")
            inputs["continue"] = True
            return "main", inputs

        # Number of points
        n_sim = input(f"Simulation Number ({inputs['n_sim']} Recomended): ")
        if n_sim != "":
            inputs["n_sim"] = int(n_sim)

        while True:
            this_dist: SpiceGaussianDist = None
            model = (
                input(f"Model {[m for m in sim_config.model_manager.models]}: ")
                .strip()
                .lower()
            )
            available_params = list(
                map(
                    lambda line: list(map(lambda a: a["name"], line)),
                    sim_config.model_manager[model].model_atributes,
                )
            )
            available_params = sorted(
                [item for sublist in available_params for item in sublist]
            )

            param = input(f"Parameter: ").strip().lower()
            if param not in available_params:
                print("Invalid Parameter! These are the valid paremeters:")
                for i, var in enumerate(available_params):
                    print(var.ljust(10), end="" if i % 7 else "\n")
                print()
            while param not in available_params:
                param = input(f"Parameter: ").strip().lower()

            mean = input(
                f"Distribution Mean ({sim_config.model_manager[model][param]}): "
            ).strip()
            if mean == "":
                mean = sim_config.model_manager[model][param]
            mean = float(mean)

            std_dev = 0.05
            std_dev_in = input(f"Distribution StdDev ({std_dev}): ").strip()
            if std_dev_in != "":
                std_dev = float(std_dev_in)

            sigmas = 3
            sigmas_in = input(f"Distribution Sigmas ({sigmas}): ").strip()
            if sigmas_in != "":
                sigmas = int(sigmas_in)

            inputs["distribution"].append(
                SpiceGaussianDist(model, param, mean, sigmas, std_dev)
            )

            if input("New Distribution? [Y/n]: ").strip().lower() in {
                "y",
                "",
                "yes",
                "true",
            }:
                continue
            else:
                break

        return "main", inputs

    def tela_single_let(self, circuit):
        inputs = {
            "node": None,
            "output": None,
            "input": None,
            "pulses": [None, None],
            "pmos": 4.8108,
            "nmos": 4.372,
            "report": True,
            "window": None,
        }
        # Node
        inputs["node"] = input(
            f"Nodo atingido {list(map(lambda n: n.name, circuit.nodes))}: "
        )
        while inputs["node"] not in list(map(lambda n: n.name, circuit.nodes)):
            inputs["node"] = input("Invalido node, insert again: ")
        # Output
        inputs["output"] = input(
            f"Nodo propagado {list(map(lambda n: n.name, circuit.nodes))}: "
        )
        while inputs["output"] not in list(map(lambda n: n.name, circuit.nodes)):
            inputs["output"] = input("Invalid node, insert again: ")
        # Input signals
        inputs["input"] = [
            int(s)
            for s in input(
                f"Input signals in 0s and 1s <{', '.join(map(lambda n: n.name, circuit.inputs))}>: "
            ).split()
        ]
        # Pulses
        pulse = input("Pulses [rise or fall]: ")
        if pulse != "":
            inputs["pulses"] = pulse.split()
        # Pmos e Nmos
        # var = input(f"Pmos and Nmos Var (4.8108, 4.372): ")
        # if var != "":
        #     inputs["pmos"], inputs["nmos"] = [float(v) for v in var.split()]
        print(barra_comprida + "\n")
        return "main", inputs

    def tela_config_sim(self, vdd, colect_time, track_estab, depth, spice):
        inputs = {
            "vdd": vdd,
            "alpha": colect_time,
            "beta": track_estab,
            "depth": depth,
            "spice": spice,
        }
        vdd = input(f"Vdd [V] ({vdd}): ")
        if vdd != "":
            inputs["vdd"] = float(vdd)
        colect_time = input(f"Charge Collect Time [ps] ({colect_time}): ")
        if colect_time != "":
            inputs["alpha"] = float(colect_time)
        track_estab = input(f"Track Establishment Time [ps] ({track_estab}): ")
        if track_estab != "":
            inputs["beta"] = float(track_estab)
        depth = input(f"Transistor Collection Depth [nm] ({depth}): ")
        if depth != "":
            inputs["depth"] = float(depth)
        spice = input(
            f"Simulator to be used ({'NGSPICE' if sim_config.runner_type == NGSpiceRunner else 'HSPICE'}): "
        )
        spice = spice.upper()
        if spice not in {"NGSPICE", "HSPICE"}:
            raise ValueError("Spice Simulator not supported")
        if spice != "":
            inputs["spice"] = NGSpiceRunner if spice == "NGSPICE" else HSpiceRunner
        return "main", inputs
