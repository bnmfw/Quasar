from .matematica import ajustar
from .components import LET
from dataclasses import dataclass
import os

# This is the Spice Interface. This is the only file in Quasar where interaction with Spice occurs.
# The interaction with Spice is always done through SpiceRunner.
# No other file in the Project should know how to interact with Spice.
# Both classes in this file are stateless, therefore the classes are instantiated and its instances are accessed


# Defines the start and end of the measuring window, must have only 2 elements
measure_window = (1.0, 3.8)

# Spice Manager is the class that is responsible for altering the .cir files used by Spice.
# This class also is responsible for reading Spice output.
class SpiceFileManager():
    def __init__(self, path_to_folder = "circuitos"):
        self.path_to_folder = path_to_folder
        self.output: dict = None

    def __write_peak_meas(self, arquivo, label: str, peak: str, grandeza: str, node: str, start: float, finish: float):
        if not peak in {"min", "max"}:
            raise ValueError("pico eh min ou max")
        if not grandeza in {"i", "V"}:
            raise ValueError("grandeza nao esta em i ou V")
         
        arquivo.write(f".meas tran {label} {peak} {grandeza}({node}) from={start}n to={finish}n\n")

    def __write_trig_meas(self, arquivo, label: str, trig: str, trig_value: float, trig_inclin: str,
     targ: str, targ_value: float, targ_inclin: str):

        arquivo.write(f".meas tran {label} TRIG v({trig}) val='{trig_value}' {trig_inclin}=1 TARG v({targ}) val='{targ_value}' {targ_inclin}=1\n")
    
    # Alters the file "measure.cir" used to define wich node tensions will be measured
    def measure_pulse(self, node: str, output: str):
        with open(f"{self.path_to_folder}/include/measure.cir", "w") as file:
            file.write("*File with measures of lowest and highest values in node and output\n")
            self.__write_peak_meas(file, "minout", "min", "V", output, *measure_window)
            self.__write_peak_meas(file, "maxout", "max", "V", output, *measure_window)
            self.__write_peak_meas(file, "minnod", "min", "V", node, *measure_window)
            self.__write_peak_meas(file, "maxnod", "max", "V", node, *measure_window)

    # Alters the file "measure.cir" used to define wich node tensions will be measured
    def measure_tension(self, node: str):
        with open(f"{self.path_to_folder}/include/measure.cir", "w") as file:
            file.write("*File with measures of lowest and highets values in node\n")
            self.__write_peak_meas(file, "minnod", "min", "V", node, *measure_window)
            self.__write_peak_meas(file, "maxnod", "max", "V", node, *measure_window) 
    
    # Alters the file "vdd.cir" wich defines the vdd of the simulation
    def set_vdd(self, vdd: float):
        with open(f"{self.path_to_folder}/include/vdd.cir", "w") as file:
            file.write("*Arquivo com a tensao usada por todos os circuitos\n")
            file.write(f"Vvdd vdd gnd {vdd}\n")
            file.write(f"Vvcc vcc gnd {vdd}\n")
            file.write(f"Vclk clk gnd PULSE(0 {vdd} 1n 0.01n 0.01n 1n 2n)")

    # Alters the file "fontes.cir" wich defines the inputs of the simulation that might be low, high or a simple PWL
    def set_signals(self, vdd: float, inputs: dict):
        with open(f"{self.path_to_folder}/include/fontes.cir", "w") as file:
            file.write("*Input signals to be altered by Quasar\n")

            # Escreve o sinal analogico a partir do sinal logico
            for entrada, level in inputs.items():
                file.write(f"V{entrada} {entrada} gnd ")
                if level == 1:
                    file.write(f"{vdd}\n")
                elif level == 0:
                    file.write("0.0\n")
                elif level == "atraso":
                    file.write(f"PWL(0n 0 1n 0 1.01n {vdd} 3n {vdd} 3.01n 0)\n")
                else:
                    raise ValueError("Invalid signal type recieved: ", level)

    # Defines the fault modeled as a current pusle in "SETs.cir"
    def set_pulse(self, let: LET, current = None):
        if not let.orientacao[0] in {"fall", "rise", None}:
            raise ValueError(f"Recieved: {let.orientacao[0]} instead of a inclination")
        if current == None:
            current = let.corrente

        with open(f"{self.path_to_folder}/include/SETs.cir", "w") as sets:
            sets.write("*SET faults\n")
            if not let.orientacao[0] == "rise": sets.write("*")
            sets.write(f"Iseu gnd {let.nodo_nome} EXP(0 {current}u 2n 50p 164p 200p) //rise\n")
            if not let.orientacao[0] == "fall": sets.write("*")
            sets.write(f"Iseu {let.nodo_nome} gnd EXP(0 {current}u 2n 50p 164p 200p) //fall\n")

    # Alters the file "measure.cir" to measure the delays
    def measure_delay(self, input: str, out: str, vdd: float):
        with open(f"{self.path_to_folder}/include/measure.cir", "w") as arquivo:
            arquivo.write("*File with the dealys to be measured\n")
            half_vdd = str(vdd / 2)
            self.__write_trig_meas(arquivo, "atraso_rr", input, half_vdd, "rise", out, half_vdd, "rise")
            self.__write_trig_meas(arquivo, "atraso_rf", input, half_vdd, "rise", out, half_vdd, "fall")
            self.__write_trig_meas(arquivo, "atraso_ff", input, half_vdd, "fall", out, half_vdd, "fall")
            self.__write_trig_meas(arquivo, "atraso_fr", input, half_vdd, "fall", out, half_vdd, "rise")
            # self.__write_trig_meas(arquivo, "largura", out, half_vdd, "fall", out, half_vdd, "rise")

    # Alters the file "measure.cir" to measure fault width
    def measure_pulse_width(self, let: LET):
        with open(f"{self.path_to_folder}/include/measure.cir", "w") as arquivo:
            arquivo.write("*File with the fault width to be measured\n")
            tensao = str(let.vdd * 0.5)
            self.__write_trig_meas(arquivo, "larg", let.nodo_nome, tensao, "rise", let.nodo_nome, tensao, "fall")

    # Sets the monte carlo parameter
    def set_monte_carlo(self, simulacoes: int = 0):
        with open(f"{self.path_to_folder}/include/monte_carlo.cir", "w") as mc:
            mc.write("*Arquivo Analise Monte Carlo\n")
            mc.write(".tran 0.01n 4n")
            if simulacoes: mc.write(f" sweep monte={simulacoes}")

    # Alters the file "mc.cir" wich defines variability parameters
    def set_variability(self, pvar = None, nvar = None):
        with open (f"{self.path_to_folder}/include/mc.cir","w") as mc:
            if pvar == None or nvar == None:
                mc.write("* Analise MC\n"
                ".param phig_var_p = gauss(4.8108, 0.05, 3)\n"
                ".param phig_var_n = gauss(4.372, 0.05, 3)")
            else:
                mc.write("* Analise MC\n"
                f".param phig_var_p = {pvar}\n"
                f".param phig_var_n = {nvar}")

    ################### ^ SETS | GETS v ################################

    @dataclass
    class Meas_from:
        label: str
        value: float
        time: float

    @dataclass
    class Meas_targ:
        label: str
        value: float
        targ: float
        trig: float
    
    # Recieves a line and returns values measured
    def __format_measure_from(self, linha: str) -> Meas_from:
        label_value, time = linha.split("at=")
        label, value = label_value.split("=")
        return self.Meas_from(label.strip(), ajustar(value), ajustar(time))

    # Recieves a line with measured values in trig targ form and returns values measured
    def __format_measure_trig(self, linha: str) -> Meas_targ:
        if "not found" in linha:
            label, *_ = linha.split("=")
            return self.Meas_targ(label.strip(), None, None, None)

        label_value_targ, trig = linha.split("trig=")  
        label_value, targ= label_value_targ.split("targ=")
        label, value = label_value.split("=")
        return self.Meas_targ(label.strip(), ajustar(value), ajustar(targ), ajustar(trig))
    
    # Recieves a measure line, identifies its kind and returns its information
    def __format_output_line(self, linha: str, saida: dict) -> None:
        measure = None
        if "at=" in linha:
            measure = self.__format_measure_from(linha)
        elif "trig=" in linha:
            measure = self.__format_measure_trig(linha)
        elif "**warning**" in linha:
            return
        saida[measure.label] = measure

    # Gets all the nodes from the circuit file
    def get_nodes(self, circuit_name: str) -> set:
        nodos = {"vdd", "gnd"}
        critical_region = False
        with open(f"{self.path_to_folder}/{circuit_name}/{circuit_name}.cir", "r") as file:
            for linha in file:

                # Identifies the quasar region of the circuit file
                if "START QUASAR" in linha:
                    critical_region = True
                    continue
                elif "END QUASAR" in linha:
                    critical_region = False
                    continue
                if not critical_region:
                    continue

                # A line starting with M identifies a transistor, wich means its connected to availabel nodes
                if "M" in linha[0]:
                    # Im not sure if those are actually source and drain, but doesent matter to identifing them
                    _, source, gate, drain, *_ = linha.split()
                    for nodo in [source, gate, drain]:
                        nodos.add(nodo)
        return {nodo for nodo in nodos if nodo not in {"vcc", "vdd", "gnd"}}

    # Reads measures in the output.txt file and return a dict with all outputs
    def get_output(self) -> dict:
        saida: dict = {"None": None}
        # print("-- START --")
        with open(f"{self.path_to_folder}/output.txt", "r") as output:
            for linha in output:
                # print(linha)
                self.__format_output_line(linha, saida)
        
        # print("-- END --")
        self.output = saida
        return saida
    
    # Reads the peak tension of a simulation from the output file
    def get_peak_tension(self, inclinacao: str, nodMeas: bool = False) -> float:
        if not inclinacao in {"fall", "rise"}:
            raise ValueError(f"Inclination value not accepted: {inclinacao}")

        output = self.get_output()

        if nodMeas:
            if inclinacao == "fall":
                return output["minnod"].value
            else:
                return output["maxnod"].value
        else:
            if inclinacao == "fall":
                return output["minout"].value
            else:
                return output["maxout"].value

    # Returns the min and max value measured in taget node
    def get_tension(self) -> float:
        output = self.get_output()
        max: float = output["maxnod"].value
        min: float = output["minnod"].value
        # if max - min > 0.05:
        #     raise RuntimeError(f"Circuito sem pulsos tem muita variacao {max} {min}")
        return (max, min)
    
    # Reads csv file like mc0.csv or mt0.csv and returns a column dict
    def __get_csv_data(self, filename: str, stop: str = None) -> dict:
        
        data: dict = {}
        
        with open(f"{filename}", "r") as file:
            while stop != None and not stop in file.readline():
                pass

            # criacao do padrao do dicionario
            header = file.readline().split(",")
            for label in header:
                if "\n" in label:
                    label = label[:-1]
                data[label] = []

            for linha in file:
                valores = linha.split(",")
                for index, chave in enumerate(data):
                    valor = None if valores[index].strip() == "failed" else ajustar(valores[index])
                    data[chave].append(valor)
        
        return data

    # TODO: Not sure here
    def get_mc_faults(self, path: str, circuit_name: str, num_analises: int, inclinacao_saida: str, vdd: float) -> int:
        
        falhas: int = 0

        dados: dict = self.__get_csv_data(f"{self.path_to_folder}{path}{circuit_name}.mt0.csv", ".TITLE")

        inclinacao_corr = "mincor" if inclinacao_saida == "fall" else "maxcor"
        inclinacao_tens = "minout" if inclinacao_saida == "fall" else "maxout"

        for i in range(num_analises):
            # corrente_pico = dados[inclinacao_corr][i]
            tensao_pico = dados[inclinacao_tens][i]

            if inclinacao_saida == "fall" and tensao_pico < vdd / 2 or\
                inclinacao_saida == "rise" and tensao_pico > vdd / 2:
                falhas += 1
        return falhas

    # Reads the delay measured from "output.txt"
    def get_delay(self) -> float:

        output = self.get_output()
        # print(output)

        atrasos: list = [output["atraso_rr"].value, output["atraso_ff"].value, output["atraso_rf"].value, output["atraso_fr"].value]
        # Erro
        if None in atrasos:
            return 0
        
        # Sorting
        for i, atraso in enumerate(atrasos):
            atrasos[i] = abs(atraso)
        atrasos.sort()
        return atrasos[1]
    
    # Reads the instances in "<circuit>.mc0.csv"
    def get_mc_instances(self, path, filename: str, simulacoes: int) -> dict:
        instancias: dict = {}

        data = self.__get_csv_data(f"{self.path_to_folder}{path}{filename}.mc0.csv", "$ IRV")

        ps: str = "pmos_rvt:@:phig_var_p:@:IGNC"
        ns: str = "nmos_rvt:@:phig_var_n:@:IGNC"

        for i, pmos, nmos in zip(data["index"], data[ps], data[ns]):
            instancias[int(float(i))] = [float(pmos), float(nmos)]
        return instancias

# Spice Manager is the class responsible for providing the interface for Spice
# This is the only class that should run Spice
# If a class wants to acces SpiceFileManager it should do through SpiceRunner be it from a context manager or a direct call
class SpiceRunner():

    # This is a huge problem, this variable is a class variable not a object variable
    # I want you to be able to call with SpiceRunner().Vdd(0.5) for example but for that the Vdd context manager
    # Must know path_to_folder of the SpiceRunner instance, wich seems to be very hard to do
    file_manager = None

    def __init__(self, path_to_folder = "circuitos") -> None:
        self.path_to_folder = path_to_folder
        SpiceRunner.file_manager = SpiceFileManager(path_to_folder=path_to_folder)
        self.test_spice()

    # Context manager that sets the number of MC simulations
    class Monte_Carlo():

        def __init__(self, num_testes):
            self.num = num_testes

        def __enter__(self):
            SpiceRunner.file_manager.set_monte_carlo(self.num)

        def __exit__(self, type, value, traceback):
            SpiceRunner.file_manager.set_monte_carlo(0)

    # Context manager that sets a single variability point in the MC simulation
    class MC_Instance():
        def __init__ (self, pmos = None, nmos = None):
            self.pmos = pmos
            self.nmos = nmos

        def __enter__(self):
            SpiceRunner.file_manager.set_variability(self.pmos, self.nmos)

        def __exit__(self, type, value, traceback):
            SpiceRunner.file_manager.set_variability(None, None)

    # Context manager that configure a single SET
    class SET():
        def __init__ (self, let: LET, corrente: float = None):
            self.let = let
            if corrente == None:
                self.corrente = let.corrente
            else:
                self.corrente = corrente

        def __enter__(self):
            SpiceRunner.file_manager.set_pulse(self.let, self.corrente)
            SpiceRunner.file_manager.measure_pulse(self.let.nodo_nome, self.let.saida_nome)

        def __exit__(self, type, value, traceback):
            SpiceRunner.file_manager.set_pulse(self.let, 0)

    # Context manager thar sets the VDD of the simulation
    class Vdd():
        def __init__ (self, vdd: float):
            self.vdd = vdd

        def __enter__(self):
            SpiceRunner.file_manager.set_vdd(self.vdd)

        def __exit__(self, type, value, traceback):
            pass

    # Context manager that sets the input signals of the circuit
    class Inputs():
        def __init__ (self, vdd: float, entradas: list):
            self.vdd = vdd
            self.entradas = {}
            for entrada in entradas:
                self.entradas[entrada.nome] = entrada.sinal

        def __enter__(self):
            SpiceRunner.file_manager.set_signals(self.vdd, self.entradas)

        def __exit__(self, type, value, traceback):
            pass

    # Simply testes if spice is working or not
    def test_spice(self) -> bool:
        os.system(f"hspice debug/empty.cir > output.txt")
        with open("output.txt", "r") as file:
            for linha in file:
                if "Cannot connect to license server system" in linha:
                    exit("HSPICE LicenseError: Cannot connect to license server system")
    
    # Set the default configurations of the ciruit
    def default(self, vdd: float) -> None:
        SpiceRunner.file_manager.set_vdd(vdd)
        SpiceRunner.file_manager.set_pulse(LET(0, vdd, "none", "none", [None, None]))
        SpiceRunner.file_manager.set_monte_carlo(0)

    # Passes the same call to HSManger, this is because only Spice Runner can see SpiceRunner.file_manager as it acts as the interface to Spice
    def get_nodes(self, circ_name: str):
        return SpiceRunner.file_manager.get_nodes(circ_name)

    # Runs a single delay simulation
    def run_delay(self, path: str, filename: str, input_name: str, output_name: str, vdd: float, inputs: list) -> float:
        # Set the signals to be simualted
        SpiceRunner.file_manager.measure_delay(input_name, output_name, vdd)
        SpiceRunner.file_manager.set_signals(vdd, {input.nome: input.sinal for input in inputs})
        # Runs the simulation in the respective folder
        os.system(f"cd {self.path_to_folder}{path} ; hspice {filename}| grep \"atraso_rr\|atraso_rf\|atraso_fr\|atraso_ff\" > ../output.txt")
        # Gets and returns the results
        delay = SpiceRunner.file_manager.get_delay()
        return delay

    # Runs a single fault simulation
    def run_SET(self, path: str, filename: str, let: LET, current = None, path_to_root = "../../../..") -> tuple:
        # Sets the SET
        with self.SET(let, current):
            # Runs the simulation
            try:
                os.system(f"cd {self.path_to_folder}{path} ; hspice {filename} | grep \"minout\|maxout\|minnod\|maxnod\" > ../output.txt")
                # Gets the peak tensions in the node and output
                peak_node = SpiceRunner.file_manager.get_peak_tension(let.orientacao[0], True)
                peak_output = SpiceRunner.file_manager.get_peak_tension(let.orientacao[1])
            except Exception:
                print(f"*** ERROR IN SET SIMULATION! FULL REPORT GENERATED AT DEBUG/CRASH_REPORT/{os.getpid()}_REPORT.TXT ***")
                os.system(f"cd {self.path_to_folder}{path} ; hspice {filename} > {'/'.join(['..']*(self.path_to_folder.count('/')+path.count('/')))}/debug/crash_report/{os.getpid()}_report.txt")
                exit()
        return (peak_node, peak_output)
    
    # TODO: Finds the tesion range of the simulation, I think
    def run_tensions(self, path: str, filename: str, nodo_nome: str) -> float:
        SpiceRunner.file_manager.measure_tension(nodo_nome)
        os.system(f"cd {self.path_to_folder}{path} ; hspice {filename} | grep \"minnod\|maxnod\" > ../output.txt")
        tensao = SpiceRunner.file_manager.get_tension()
        return tensao

    # Runs a single simulation and returns the fault width
    def run_pulse_width(self, path:str, filename: str, let: LET, corrente: float):
        output: dict = {}
        # print(f"corrente: {corrente}")
        with self.SET(let, corrente):
            SpiceRunner.file_manager.measure_pulse_width(let)
            os.system(f"cd {self.path_to_folder}{path} ; hspice {filename} | grep \"larg\" > ../output.txt")
            output = SpiceRunner.file_manager.get_output()
        # print(f"output: {output}")

        try:
            if output["larg"].value == None:
                return None

            return abs(output["larg"].value)
        except KeyError:
            return None

    # Run a bunch of MC simulation and gets the proportion of faults
    def run_simple_MC(self, path: str, circuit_name: str, nodo_nome: str, saida_nome: str, analises: int, pulso_out: str, vdd: float) -> int:
        SpiceRunner.file_manager.measure_pulse(nodo_nome, saida_nome)
        with self.Monte_Carlo(analises):
            os.system(f"cd {self.path_to_folder}{path} ; hspice {circuit_name}.cir| grep \"minout\|maxout\" > ../output.txt")
        return SpiceRunner.file_manager.get_mc_faults(path, circuit_name, analises, pulso_out, vdd)

    # TODO: Not sure
    def run_MC_var(self, path: str, filename: str, cir_nome: str, analises: int) -> dict:
        with self.Monte_Carlo(analises):
            os.system(f"cd {self.path_to_folder}{path} ; hspice {filename} > ../output.txt")
        return SpiceRunner.file_manager.get_mc_instances(path, cir_nome, analises)

HSRunner = SpiceRunner()

# Runs a bunch of routine checks to see if the Spice Interface is running accordingly
if __name__ == "__main__":
    print("Testing SET simulation with known SET value ...")
    ptf = "debug/test_circuits"
    from .circuito import Circuito
    TestRunner = SpiceRunner(path_to_folder=ptf)
    nand_teste = Circuito("nand", 0.7).from_json(path_to_folder=ptf)
    valid_input = [0, 1] 
    valid_let = LET(156.25, 0.7, "g1", "g1", ["fall", "fall"], valid_input)
    expected_let_value = 0.36585829999999997
    for vi, entrada in zip(valid_input, nand_teste.entradas): entrada.sinal = vi
    with TestRunner.Vdd(0.7), TestRunner.Inputs(0.7, nand_teste.entradas), TestRunner.MC_Instance(4.7443, 4.3136):
        peak_node, peak_output = TestRunner.run_SET(nand_teste.path, nand_teste.arquivo, valid_let, path_to_root="debug/..")
        assert abs(peak_node-expected_let_value) <= 10e-6 