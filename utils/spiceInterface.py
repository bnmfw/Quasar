"""
Spice Interface.
The interaction with Spice is always done through SpiceRunner.
No other file in the Project should know how to interact with Spice.
Both classes in this file are stateless, therefore the classes are instantiated and its instances are accessed 
"""

from .matematica import ajustar
from .components import LET
from dataclasses import dataclass
import os

# Defines the start and end of the measuring window, must have only 2 elements
measure_window = (1.0, 3.8)

class SpiceFileManager():
    """
    Responsible for altering the .cir files used by Spice and reading its output.
    """

    def __init__(self, path_to_folder: str = "circuitos") -> None:
        """
        Constructor

            :param str path_to_folder: relative path into the folder that contain spice files.
        """
        self.path_to_folder = path_to_folder
        self.output: dict = None

    def __write_peak_meas(self, file, label: str, peak: str, quantity: str, node: str, start: float, finish: float) -> None:
        """
        Writes a peak measurement line in the measurement .cir file.

            :param type file: File object that is to be written to.
            :param str label: Label of the measurement.
            :param str peak: Type of peak to be measured. Either 'min' or 'max'.
            :param str grandeza: Physical quantity. Either 'V' or 'i'.
            :param str node: Name of the node to be measured.
            :param float start: Starting time of the measurement window.
            :param float finish: Finishing time of the measurement window.
        """
        if not peak in {"min", "max"}:
            raise ValueError(f"peak cannot be {peak}, must be min or max")
        if not quantity in {"i", "V"}:
            raise ValueError(f"quantity cannot be {quantity}, must be i or V")
         
        file.write(f".meas tran {label} {peak} {quantity}({node}) from={start}n to={finish}n\n")

    def __write_trig_meas(self, file, label: str, trig: str, trig_value: float, trig_inclin: str, targ: str, targ_value: float, targ_inclin: str) -> None:
        """
        Writes a trig measurement line in the measurement .cir file.

            :param type file: File object that is to be written to.
            :param str label: Label of the measurement.
            :param str trig: Name of the monitored triggering node.
            :param float trig_value: Value to trigger the measurement.
            :param str trig_inclin: Inclination of trigger. Must be 'rise' or 'fall'.
            :param str targ: Name of the monitored target node.
            :param float targ_value: Value of target node ot end the measurement.
            :param str targ_inclin: Inclination of target. Must be 'rise' or 'fall'.
        """

        file.write(f".meas tran {label} TRIG v({trig}) val='{trig_value}' {trig_inclin}=1 TARG v({targ}) val='{targ_value}' {targ_inclin}=1\n")
    
    def measure_pulse(self, node: str, output: str) -> None:
        """
        Alters the measure.cir file to track min and max tension on given node and output

            :param str node: Node with to have min and max tensions measured
            :param str output: Output to have min and max tensions measured
        """
        with open(f"{self.path_to_folder}/include/measure.cir", "w") as file:
            file.write("*File with measures of lowest and highest values in node and output\n")
            self.__write_peak_meas(file, "minout", "min", "V", output, *measure_window)
            self.__write_peak_meas(file, "maxout", "max", "V", output, *measure_window)
            self.__write_peak_meas(file, "minnod", "min", "V", node, *measure_window)
            self.__write_peak_meas(file, "maxnod", "max", "V", node, *measure_window)

    def measure_tension(self, node: str) -> None:
        """
        Alters the measure.cir file to track min and max tension on given node

            :param str node: Node with to have min and max tensions measured
        """
        with open(f"{self.path_to_folder}/include/measure.cir", "w") as file:
            file.write("*File with measures of lowest and highets values in node\n")
            self.__write_peak_meas(file, "minnod", "min", "V", node, *measure_window)
            self.__write_peak_meas(file, "maxnod", "max", "V", node, *measure_window) 
    
    def set_vdd(self, vdd: float) -> None:
        """
        Alters the vdd.cir file to set the vdd of the simulations

            :param float vdd: defines the vdd of the simulation
        """
        with open(f"{self.path_to_folder}/include/vdd.cir", "w") as file:
            file.write("*Arquivo com a tensao usada por todos os circuitos\n")
            file.write(f"Vvdd vdd gnd {vdd}\n")
            file.write(f"Vvcc vcc gnd {vdd}\n")
            file.write(f"Vclk clk gnd PULSE(0 {vdd} 1n 0.01n 0.01n 1n 2n)")

    def set_signals(self, vdd: float, inputs: dict) -> None:
        """
        Alters the fontes.cir file defining the input values of the simulation.
        
            :param float vdd: the vdd of the simulation.
            :param dict inputs: dict with input values in the form {input_name: input_value}
        """
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

    def set_pulse(self, let: LET, current: float = None) -> None:
        """
        Alters the SETs.cir file wich models the fault.

            :param LET let: let to be modeled.
            :param float current: current of the fault. If left as None let.current will be used.
        """

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

    def measure_delay(self, input: str, out: str, vdd: float) -> None:
        """
        Altes the measure.cir file to measure the delay from one input to one output.

            :param str input: name of the input node.
            :param str out: name of the output node.
            :param float vdd: value of the vdd of the simulation.
        """

        with open(f"{self.path_to_folder}/include/measure.cir", "w") as file:
            file.write("*File with the dealys to be measured\n")
            half_vdd = str(vdd / 2)
            self.__write_trig_meas(file, "atraso_rr", input, half_vdd, "rise", out, half_vdd, "rise")
            self.__write_trig_meas(file, "atraso_rf", input, half_vdd, "rise", out, half_vdd, "fall")
            self.__write_trig_meas(file, "atraso_ff", input, half_vdd, "fall", out, half_vdd, "fall")
            self.__write_trig_meas(file, "atraso_fr", input, half_vdd, "fall", out, half_vdd, "rise")
            # self.__write_trig_meas(file, "largura", out, half_vdd, "fall", out, half_vdd, "rise")

    def measure_pulse_width(self, let: LET) -> None:
        """
        Alters the measure.cir file to measure the fault width of the let on the output.
        The fault width is the time the output node is flipped by the fault.

            :param LET let: let modeled.
        """
        with open(f"{self.path_to_folder}/include/measure.cir", "w") as arquivo:
            arquivo.write("*File with the fault width to be measured\n")
            tensao = str(let.vdd * 0.5)
            self.__write_trig_meas(arquivo, "larg", let.nodo_nome, tensao, "rise", let.nodo_nome, tensao, "fall")

    def set_monte_carlo(self, simulations: int = 0) -> None:
        """
        Sets the monte carlo parameter in the monte_carlo.cir file.

            :param int simulations: number o Monte Carlo simulations.
        """
        with open(f"{self.path_to_folder}/include/monte_carlo.cir", "w") as mc:
            mc.write("*Arquivo Analise Monte Carlo\n")
            mc.write(".tran 0.01n 4n")
            if simulations: mc.write(f" sweep monte={simulations}")

    def set_variability(self, pvar: float = None, nvar: float = None) -> None:
        """
        Alterts the mc.cir file to set the variability parameters.

            :param float pvar: work function of pfet devices.
            :param float nvar: work function of nfer devices.

        """
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
        """
        Measure struct of the from type
        """
        label: str
        value: float
        time: float

    @dataclass
    class Meas_targ:
        """
        Measure struct of the trig targ type
        """
        label: str
        value: float
        targ: float
        trig: float
    
    def __format_measure_from(self, line: str) -> Meas_from:
        """
        Gatters the data from a measurement from the from type.

            :param str line: line containing the data
        """
        label_value, time = line.split("at=")
        label, value = label_value.split("=")
        return self.Meas_from(label.strip(), ajustar(value), ajustar(time))

    def __format_measure_trig(self, line: str) -> Meas_targ:
        """
        Gatters the data from a measurement from the trig trag type.

            :param str line: line containing the data
        """
        if "not found" in line:
            label, *_ = line.split("=")
            return self.Meas_targ(label.strip(), None, None, None)

        label_value_targ, trig = line.split("trig=")  
        label_value, targ= label_value_targ.split("targ=")
        label, value = label_value.split("=")
        return self.Meas_targ(label.strip(), ajustar(value), ajustar(targ), ajustar(trig))
    
    def __format_output_line(self, line: str) -> None:
        """
        Recieves a measurement line and outputs it data.

            :param line
        """
        measure = None
        if "at=" in line:
            measure = self.__format_measure_from(line)
        elif "trig=" in line:
            measure = self.__format_measure_trig(line)
        elif "**warning**" in line:
            return []
        return {measure.label: measure}

    def get_nodes(self, circuit_name: str) -> set:
        """
        Parse a <circut_name>.cir file and gets all nodes connected to transistor devices.

            :param str curcuit_name: name of the circuit to be parsed.
            :returns: a set containing the label of all nodes.
        """
        nodes = {"vdd", "gnd"}
        critical_region = False
        with open(f"{self.path_to_folder}/{circuit_name}/{circuit_name}.cir", "r") as file:
            for line in file:

                # Identifies the quasar region of the circuit file
                if "START QUASAR" in line:
                    critical_region = True
                    continue
                elif "END QUASAR" in line:
                    critical_region = False
                    continue
                if not critical_region:
                    continue

                # A line starting with M identifies a transistor, wich means its connected to availabel nodes
                if "M" in line[0]:
                    # Im not sure if those are actually source and drain, but doesent matter to identifing them
                    _, source, gate, drain, *_ = line.split()
                    for node in [source, gate, drain]:
                        nodes.add(node)
        return {node for node in nodes if node not in {"vcc", "vdd", "gnd"}}

    def get_output(self) -> dict:
        """
        Reads data in the output.txt file.

            :returns: a dict containing all data formatted as {'label': data}
        """
        data: dict = {}
        with open(f"{self.path_to_folder}/output.txt", "r") as output:
            for linha in output:
                data.update(self.__format_output_line(linha))
        self.output = data
        return data
    
    def get_peak_tension(self, inclination: str, nodMeas: bool = False) -> float:
        """
        Reads the peak tension of a node.

            :param str inclination: Inclination measured. Must be 'rise' or 'fall'
            :param bool nodMeas: Node measured is an output = False; is not an output = True.
            :returns: peak tension measured.
        """
        if not inclination in {"fall", "rise"}:
            raise ValueError(f"Inclination value not accepted: {inclination}")

        output = self.get_output()

        if nodMeas:
            if inclination == "fall":
                return output["minnod"].value
            else:
                return output["maxnod"].value
        else:
            if inclination == "fall":
                return output["minout"].value
            else:
                return output["maxout"].value

    def get_tension(self) -> tuple:
        """
        Reads the max and minimun tension of a node

            :returns: A tuple containing the max and min tensions.
        """
        output = self.get_output()
        return (output["maxnod"].value, output["minnod"].value)
    
    def __get_csv_data(self, filename: str, start: str = None) -> dict:
        """
        Reads a csv file (usually mc0.csv or mt0.csv) as returns its data.

            :param str filename: name of the file to be read.
            :param str start: substring which indicates the reading starts in the next line.
            :returns: a dict containing the columns of the csv of the form data[label] = [column vector]
        """
        
        data: dict = {}
        
        with open(f"{filename}", "r") as file:
            while start is not None and not start in file.readline():
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

    def get_mc_faults(self, path: str, circuit_name: str, sim_num: int, inclination: str, vdd: float) -> int:
        """
        Returns the number of simulations that resulted in a fault in a MC simulation.

            :param str path: Path from the circuits folder to the own circuit folder.
            :param str circuit_name: Name of the circuit.
            :param int sim_num: Number of Monte Carlo simulations done.
            :param str inclination: Inclination of fault on the output. Must be 'rise' or 'fall'.
            :param float vdd: Vdd of the simulations.
            :returns: Number of simulations that faulted.
        """

        faults: int = 0

        data: dict = self.__get_csv_data(f"{self.path_to_folder}{path}{circuit_name}.mt0.csv", ".TITLE")

        inclination_corr = "mincor" if inclination == "fall" else "maxcor"
        inclination_tens = "minout" if inclination == "fall" else "maxout"

        for i in range(sim_num):
            # corrente_pico = dados[inclinacao_corr][i]
            peak_tension = data[inclination_tens][i]

            if inclination == "fall" and peak_tension < vdd / 2 or inclination == "rise" and peak_tension > vdd / 2:
                faults += 1
        return faults

    def get_delay(self) -> float:
        """
        Reads the delay measured from the output.txt file.
            
            :returns: the delay measured.
        """

        output = self.get_output()

        delays: list = [output["atraso_rr"].value, output["atraso_ff"].value, output["atraso_rf"].value, output["atraso_fr"].value]
        if None in delays:
            return 0
        
        # Sorting
        for i, atraso in enumerate(delays):
            delays[i] = abs(atraso)
        delays.sort()

        # Basically because we are running all kinds of delay measures delays[2] and delays[3] contain nonsense so we get only delays[1] witch will be the gratest

        return delays[1]
    
    def get_mc_instances(self, path: str, circ_name: str) -> dict:
        """
        Reads the instances in <circuit>.mc0.csv.

            :param str path: Path from the circuits folder to the own circuit folder.
            :param str circ_name: Name of the circuit.
            :returns: Dict containing the instances of variability.
        """
        instances: dict = {}

        data = self.__get_csv_data(f"{self.path_to_folder}{path}{circ_name}.mc0.csv", "$ IRV")

        ps: str = "pmos_rvt:@:phig_var_p:@:IGNC"
        ns: str = "nmos_rvt:@:phig_var_n:@:IGNC"

        for i, pmos, nmos in zip(data["index"], data[ps], data[ns]):
            instances[int(float(i))] = [float(pmos), float(nmos)]
        return instances

class SpiceRunner():
    """ 
    Responsible for running spice. Used as a Interface for spice to the rest of the system.
    """

    # This is a huge problem, this variable is a class variable not a object variable
    # I want you to be able to call with SpiceRunner().Vdd(0.5) for example but for that the Vdd context manager
    # Must know path_to_folder of the SpiceRunner instance, wich seems to be very hard to do
    file_manager = None

    def __init__(self, path_to_folder = "circuitos") -> None:
        """
        Constructor

            :param str path_to_folder: relative path into the folder that contain spice files.
        """
        self.path_to_folder = path_to_folder
        SpiceRunner.file_manager = SpiceFileManager(path_to_folder=path_to_folder)
        self.test_spice()

    class Monte_Carlo():
        """
        Context Mangers that sets the number of MC simulations.
        """

        def __init__(self, num_testes):
            self.num = num_testes

        def __enter__(self):
            SpiceRunner.file_manager.set_monte_carlo(self.num)

        def __exit__(self, type, value, traceback):
            SpiceRunner.file_manager.set_monte_carlo(0)

    class MC_Instance():
        """
        Context Mangers that sets the variability instance of the circuit.
        """
        def __init__ (self, pmos = None, nmos = None):
            self.pmos = pmos
            self.nmos = nmos

        def __enter__(self):
            SpiceRunner.file_manager.set_variability(self.pmos, self.nmos)

        def __exit__(self, type, value, traceback):
            SpiceRunner.file_manager.set_variability(None, None)

    class SET():
        """
        Context Mangers that sets the number a single fault.
        """
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

    class Vdd():
        """
        Context Mangers that sets the vdd of the simulation.
        """
        def __init__ (self, vdd: float):
            self.vdd = vdd

        def __enter__(self):
            SpiceRunner.file_manager.set_vdd(self.vdd)

        def __exit__(self, type, value, traceback):
            pass

    class Inputs():
        """
        Context Mangers that sets the input signals of the simulation.
        """
        def __init__ (self, vdd: float, entradas: list):
            self.vdd = vdd
            self.entradas = {}
            for entrada in entradas:
                self.entradas[entrada.nome] = entrada.sinal

        def __enter__(self):
            SpiceRunner.file_manager.set_signals(self.vdd, self.entradas)

        def __exit__(self, type, value, traceback):
            pass

    def test_spice(self) -> None:
        """
        Testes if spice is working. If not will exit as nothing can be done without spice.
        """
        os.system(f"hspice debug/empty.cir > output.txt")
        with open("output.txt", "r") as file:
            for linha in file:
                if "Cannot connect to license server system" in linha:
                    exit("HSPICE LicenseError: Cannot connect to license server system")
    
    def default(self, vdd: float) -> None:
        """
        Sets circuit to default configuration, includind vdd, no fault and no MC.

            :param float vdd: Standard vdd of the simulation.
        """
        SpiceRunner.file_manager.set_vdd(vdd)
        SpiceRunner.file_manager.set_pulse(LET(0, vdd, "none", "none", [None, None]))
        SpiceRunner.file_manager.set_monte_carlo(0)

    def get_nodes(self, circ_name: str) -> set:
        """
        Parse a <circut_name>.cir file and gets all nodes connected to transistor devices.

            :param str curcuit_name: name of the circuit to be parsed.
            :returns: a set containing the label of all nodes.
        """
        return SpiceRunner.file_manager.get_nodes(circ_name)

    def run_delay(self, path: str, filename: str, input_name: str, output_name: str, vdd: float, inputs: list) -> float:
        """
        Returns the delay of shortest path from a input to and output.

            :param str path: Path from circuits file to circuit own file.
            :param str filename: Name of the file.
            :param str input_name: Name of the input node from where the delay is propagated.
            :param str output_name: Name of the output node where the delay propagates to.
            :param float vdd: Vdd of the simulation.
            :param list inputs: A list of Entrada objects.
            :returns: the delay of shortest path from the input to the output.
        """
        
        # Set the signals to be simualted
        SpiceRunner.file_manager.measure_delay(input_name, output_name, vdd)
        SpiceRunner.file_manager.set_signals(vdd, {input.nome: input.sinal for input in inputs})
        # Runs the simulation in the respective folder
        os.system(f"cd {self.path_to_folder}{path} ; hspice {filename}| grep \"atraso_rr\|atraso_rf\|atraso_fr\|atraso_ff\" > ../output.txt")
        # Gets and returns the results
        delay = SpiceRunner.file_manager.get_delay()
        return delay

    def run_SET(self, path: str, filename: str, let: LET, current: float = None, path_to_root = "../../../..") -> tuple:
        """
        Returns the peak voltage output for a given let.

            :param str path: Path from circuits file to circuit own file.
            :param str filename: Name of the file.
            :param LET let: let simulated.
            :param float current: current of the fault. If left as None let.current will be used.
            :param str path_to_root: path to root directory of the project.
            :returns: a tuple containing the peak tension at the node where the fault originated and output.
        """
        # Sets the SET
        with self.SET(let, current):
            # Runs the simulation
            try:
                os.system(f"cd {self.path_to_folder}{path} ; hspice {filename} | grep \"minout\|maxout\|minnod\|maxnod\" > ../output.txt")
                # Gets the peak tensions in the node and output
                peak_node = SpiceRunner.file_manager.get_peak_tension(let.orientacao[0], True)
                peak_output = SpiceRunner.file_manager.get_peak_tension(let.orientacao[1])
            except Exception as error:
                print(f"*** ERROR IN SET SIMULATION! FULL REPORT GENERATED AT DEBUG/CRASH_REPORT/{os.getpid()}_REPORT.TXT ***")
                print(f"*** ERROR: {error}")
                os.system(f"cd {self.path_to_folder}{path} ; hspice {filename} > {'/'.join(['..']*(self.path_to_folder.count('/')+path.count('/')))}/debug/crash_report/{os.getpid()}_report.txt")
                exit()
        return (peak_node, peak_output)
    
    def run_tensions(self, path: str, filename: str, node_name: str) -> float:
        """
            Returns the max and min tensions of a node.
            :param str path: Path from circuits file to circuit own file.
            :param str filename: Name of the file.
            :param str node_name: Name of the node from which voltage will be measures
            :returns: A tuple containing the max and min tensions.
        """
        SpiceRunner.file_manager.measure_tension(node_name)
        os.system(f"cd {self.path_to_folder}{path} ; hspice {filename} | grep \"minnod\|maxnod\" > ../output.txt")
        return SpiceRunner.file_manager.get_tension() 

    def run_pulse_width(self, path: str, filename: str, let: LET, current: float = None) -> float:
        """
        Returns the pulse width of the propagated fault.

            :param str path: Path from circuits file to circuit own file.
            :param str filename: Name of the file.
            :param LET let: Let to be simulated.
            :param float current: current to be simulated. If None then let.current will be used.
            :returns: Fault width at output.
        """
        with self.SET(let, current):
            SpiceRunner.file_manager.measure_pulse_width(let)
            os.system(f"cd {self.path_to_folder}{path} ; hspice {filename} | grep \"larg\" > ../output.txt")
            output = SpiceRunner.file_manager.get_output()
        
        try:
            if output["larg"].value == None:
                return None

            return abs(output["larg"].value)
        except KeyError:
            return None

    def run_simple_MC(self, path: str, circuit_name: str, name_name: str, output_name: str, sim_num: int, output_incl: str, vdd: float) -> int:
        """
        Returns the number of MC simulation that faulted.

            :param str path: Path from circuits file to circuit own file.
            :param str circuit_name: Name of the circuit.
            :param str name_name: Name of the node.
            :param str output_name: Name of the output.
            :param int sim_num: Number of simulations.
            :param str output_incl: Inclination of fault at the output.
            :param float vdd: Vdd of the simulation.
            :return: The number of simulations that faulted.
        """
        SpiceRunner.file_manager.measure_pulse(name_name, output_name)
        with self.Monte_Carlo(sim_num):
            os.system(f"cd {self.path_to_folder}{path} ; hspice {circuit_name}.cir| grep \"minout\|maxout\" > ../output.txt")
        return SpiceRunner.file_manager.get_mc_faults(path, circuit_name, sim_num, output_incl, vdd)

    def run_MC_var(self, path: str, filename: str, circuit_name: str, sim_num: int) -> dict:
        """
        Returns the number of MC simulation that faulted.

            :param str path: Path from circuits file to circuit own file.
            :param str filename: Name of the file
            :param str circuit_name: Name of the circuit.
            :param int sim_num: Number of simulations.
            :return: MC variability instances.
        """
        with self.Monte_Carlo(sim_num):
            os.system(f"cd {self.path_to_folder}{path} ; hspice {filename} > ../output.txt")
        return SpiceRunner.file_manager.get_mc_instances(path, circuit_name)

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
        assert abs(peak_node-expected_let_value) <= 10e-6, "SET SIMULATION FAILED"