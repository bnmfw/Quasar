"""
Spice Interface.
The interaction with Spice is always done through SpiceRunner.
No other file in the Project should know how to interact with Spice.
Both classes in this file are stateless, therefore the classes are instantiated and its instances are accessed 
"""

from ..utils.matematica import spice_to_float, InDir
from ..circuit.components import LET
from ..circuit.graph import Graph
from ..simconfig.simulationConfig import sim_config
from dataclasses import dataclass
from abc import ABC
import os
from os import path
from typing import TextIO

# Defines the start and end of the measuring window, must have only 2 elements
measure_window = (1.0, 3.8)

class SpiceFileManager():
    """
    Responsible for altering the .cir files used by Spice and reading its output.
    """
    def __init__(self, path_to_folder: str = path.join("project")) -> None:
        """
        Constructor.

        Args:
            path_to_folder (str): relative path into the folder that contain spice files.
        """
        self.path_to_folder = path_to_folder
        self.output: dict = None
    
    ################### ^ META | SETS v ###################
    
    def __write_peak_meas(self, file: TextIO, label: str, peak: str, quantity: str, node: str, start: float, finish: float) -> None:
        """
        Writes a peak measurement line in the measurement .cir file.

        Args:    
            file (TextIO): File object that is to be written to.
            label (str): Label of the measurement.
            peak (str): Type of peak to be measured. Either 'min' or 'max'.
            quantity (str): Physical quantity. Either 'V' or 'i'.
            node (str): Name of the node to be measured.
            start (float): Starting time of the measurement window.
            finish (float): Finishing time of the measurement window.
        """
        if not peak in {"min", "max"}:
            raise ValueError(f"peak cannot be {peak}, must be min or max")
        if not quantity in {"i", "V"}:
            raise ValueError(f"quantity cannot be {quantity}, must be i or V")
         
        file.write(f".meas tran {label} {peak} {quantity}({node}) from={start}n to={finish}n\n")

    def __write_trig_meas(self, file: TextIO, label: str, trig: str, trig_value: float, trig_inclin: str, targ: str, targ_value: float, targ_inclin: str) -> None:
        """
        Writes a trig measurement line in the measurement .cir file.

        Args:    
            file (TextIO): File object that is to be written to.
            label (str):s Label of the measurement.
            trig (str): Name of the monitored triggering node.
            trig_value (float): Value to trigger the measurement.
            trig_inclin (str): Inclination of trigger. Must be 'rise' or 'fall'.
            targ (targ): Name of the monitored target node.
            targ_value (float): Value of target node ot end the measurement.
            targ_inclin (str): Inclination of target. Must be 'rise' or 'fall'.
        """

        file.write(f".meas tran {label} TRIG v({trig}) val='{trig_value}' {trig_inclin}=1 TARG v({targ}) val='{targ_value}' {targ_inclin}=1\n")
    
    def measure_pulse(self, node: str, output: str) -> None:
        """
        Alters the measure.cir file to track min and max tension on given node and output

        Args:
            node (str): Node with to have min and max tensions measured
            output (str): Output to have min and max tensions measured
        """
        with open(path.join(self.path_to_folder,"include","measure.cir"), "w") as file:
            file.write("*File with measures of lowest and highest values in node and output\n")
            self.__write_peak_meas(file, "minout", "min", "V", output, *measure_window)
            self.__write_peak_meas(file, "maxout", "max", "V", output, *measure_window)
            self.__write_peak_meas(file, "minnod", "min", "V", node, *measure_window)
            self.__write_peak_meas(file, "maxnod", "max", "V", node, *measure_window)

    def measure_tension(self, node: str) -> None:
        """
        Alters the measure.cir file to track min and max tension on given node.

        Args:
            node (str): Node with to have min and max tensions measured.
        """
        with open(path.join(self.path_to_folder,"include","measure.cir"), "w") as file:
            file.write("*File with measures of lowest and highest values in node\n")
            self.__write_peak_meas(file, "minnod", "min", "V", node, *measure_window)
            self.__write_peak_meas(file, "maxnod", "max", "V", node, *measure_window) 
    
    def measure_nodes(self, nodes: list) -> None:
        """
        Alters the measure.cir file to track the min and max value of given nodes.

        Args:
            nodes (list[str]): List of node names to be measured.
        """
        with open(path.join(self.path_to_folder,"include","measure.cir"), "w") as file:
            file.write("*File with measured of lowest and highest values in list of nodes\n")
            for node in nodes:
                self.__write_peak_meas(file, f"min{node}", "min", "V", node, *measure_window)
                self.__write_peak_meas(file, f"max{node}", "max", "V", node, *measure_window)

    def set_vdd(self, vdd: float) -> None:
        """
        Alters the vdd.cir file to set the vdd of the simulations.

        Args:
            vdd (float): Defines the vdd of the simulation.
        """
        with open(path.join(self.path_to_folder,"include","vdd.cir"), "w") as file:
            file.write("*File with the vdd tension used by all circuits\n")
            file.write(f"Vvdd vdd gnd {vdd}\n")
            file.write(f"Vvcc vcc gnd {vdd}\n")
            # file.write(f"Vclk clk gnd PULSE(0 {vdd} 1n 0.01n 0.01n 1n 2n)")

    def set_vss(self, vss: float) -> None:
        """
        Alters the vss.cir file to set the vss of the simulations

        Args:
            vss (float): defines the vss of the simulation
        """
        with open(path.join(self.path_to_folder,"include","vss.cir"), "w") as file:
            file.write("*File with the vss tension used by all circuits\n")
            file.write(f"Vvss vss gnd {vss}\n")

    def set_signals(self, inputs: dict, vdd: float, vss: float = 0) -> None:
        """
        Alters the fontes.cir file defining the input values of the simulation.
        
        Args:
            vdd (float): the vdd of the simulation.
            inputs (dict): dict with input values in the form {input_name: input_value}
        """

        with open(path.join(self.path_to_folder,"include","fontes.cir"), "w") as file:
            file.write("*Input signals to be altered by Quasar\n")

            # Writes the signal from the signal dict
            for entrada, level in inputs.items():
                file.write(f"V{entrada} {entrada} gnd ")
                if level == 1:
                    file.write(f"{vdd}\n")
                elif level == 0:
                    if vss:
                        file.write(f"{vss}\n")
                    else:
                        file.write(f"0.0\n")
                elif level == "delay":
                    if vss:
                        file.write(f"PWL(0n {vss} 1n {vss} 1.01n {vdd} 3n {vdd} 3.01n {vss})\n")
                    else:
                        file.write(f"PWL(0n 0 1n 0 1.01n {vdd} 3n {vdd} 3.01n 0)\n")
                else:
                    raise ValueError("Invalid signal type recieved: ", level)

    def set_pulse(self, let: LET, current: float = None) -> None:
        """
        Alters the SETs.cir file wich models the fault.

        Args:
            let (LET): let to be modeled.
            current (float): current of the fault. If left as None let.current will be used.
        """

        if not let.orientacao[0] in {"fall", "rise", None}:
            raise ValueError(f"Recieved: {let.orientacao[0]} instead of a edge")
        if current == None:
            current = let.current

        with open(path.join(self.path_to_folder,"include","SETs.cir"), "w") as sets:
            sets.write("*SET faults\n")
            sets.write(sim_config.fault_model.spice_string(let.node_name, current, let.orientacao[0])+"\n")

    def measure_delay(self, input: str, out: str, vdd: float) -> None:
        """
        Altes the measure.cir file to measure the delay from one input to one output.

        Args:
            input (str): name of the input node.
            out (str): name of the output node.
            vdd (float): value of the vdd of the simulation.
        """

        with open(path.join(self.path_to_folder,"include","measure.cir"), "w") as file:
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

        Args:
            let (LET): let modeled.
        """
        with open(path.join(self.path_to_folder,"include","measure.cir"), "w") as file:
            file.write("*File with the fault width to be measured\n")
            tensao = str(let.vdd * 0.5)
            self.__write_trig_meas(file, "larg", let.node_name, tensao, "rise", let.node_name, tensao, "fall")

    def set_monte_carlo(self, simulations: int = 0) -> None:
        """
        Sets the monte carlo parameter in the monte_carlo.cir file.

        Args:
            simulations (int): number o Monte Carlo simulations.
        """
        with open(path.join(self.path_to_folder,"include","monte_carlo.cir"), "w") as mc:
            mc.write("*Arquivo Analise Monte Carlo\n")
            mc.write(".tran 0.01n 4n")
            if simulations: mc.write(f" sweep monte={simulations}")

    def set_variability(self, pvar: float = None, nvar: float = None) -> None:
        """
        Alterts the mc.cir file to set the variability parameters.

        Args:
            pvar (float): work function of pfet devices.
            nvar (float): work function of nfer devices.

        """
        with open (path.join(self.path_to_folder,"include","mc.cir"),"w") as mc:
            if pvar == None or nvar == None:
                mc.write("* Analise MC\n"
                ".param phig_var_p = gauss(4.8108, 0.05, 3)\n"
                ".param phig_var_n = gauss(4.372, 0.05, 3)")
            else:
                mc.write("* Analise MC\n"
                f".param phig_var_p = {pvar}\n"
                f".param phig_var_n = {nvar}")

    def set_variability_bulk(self, pvar: float = None, nvar: float = None) -> None:
        """
        Alterts the mc.cir file to set the variability parameters.

        Args:
            pvar (float): thershold voltage of pmos devices.
            nvar (float): thershold voltage of nmos devices.

        """
        with open (path.join(self.path_to_folder,"include","mc.cir"),"w") as mc:
            if pvar == None or nvar == None:
                mc.write("* Analise MC\n"
                ".param vth0_var_p = gauss(-0.49155, 0.1, 3)\n"
                ".param vth0_var_n = gauss(0.49396, 0.1, 3)")
            else:
                mc.write("* Analise MC\n"
                f".param vth0_var_p = {pvar}\n"
                f".param vth0_var_n = {nvar}")

    ################### ^ SETS | GETS v ###################

    @dataclass
    class Meas_from:
        """
        Measure struct of the from type.
        """
        label: str
        value: float
        time: float

    @dataclass
    class Meas_targ:
        """
        Measure struct of the trig targ type.
        """
        label: str
        value: float
        targ: float
        trig: float
    
    def __format_measure_from(self, line: str) -> Meas_from:
        """
        Gatters the data from a measurement from the from type.

        Args:
            line (str): line containing the data.
        
        Returns:
            Meas_from: An data object containing the data.
        """
        label_value, time = line.split("at=")
        label, value = label_value.split("=")
        return self.Meas_from(label.strip(), spice_to_float(value), spice_to_float(time))

    def __format_measure_trig(self, line: str) -> Meas_targ:
        """
        Gatters the data from a measurement from the trig trag type.

        Args:
            line (str): line containing the data.
        
        Returns:
            Meas_targ: An data object containing the data.
        """
        if "not found" in line:
            label, *_ = line.split("=")
            return self.Meas_targ(label.strip(), None, None, None)

        label_value_targ, trig = line.split("trig=")  
        label_value, targ= label_value_targ.split("targ=")
        label, value = label_value.split("=")
        return self.Meas_targ(label.strip(), spice_to_float(value), spice_to_float(targ), spice_to_float(trig))
    
    def __format_output_line(self, line: str) -> dict:
        """
        Recieves a measurement line and outputs it data.

        Args:
            line (str): line of output.
        
        Returns:
            dict: A dictionary in the format {label: value}
        """
        measure = None
        if "at=" in line:
            measure = self.__format_measure_from(line)
        elif "trig=" in line:
            measure = self.__format_measure_trig(line)
        elif "**warning**" in line:
            return []
        return {measure.label: measure}

    def get_nodes(self, circuit_name: str, tension_sources: list = None) -> set:
        """
        Parse a <circut_name>.cir file and gets all nodes connected to transistor devices.

        Args:
            curcuit_name (str): name of the circuit to be parsed.
            tension_sources (list[str]): List of tesion sources.

        Returns:
            set: a set containing the label of all nodes and a Graph object.
        """
        nodes = {"vdd", "gnd"}
        if tension_sources is None: tension_sources = ["vcc", "vdd", "gnd", "vss"]
        with open(path.join(self.path_to_folder,'circuits',circuit_name,f"{circuit_name}.cir"), "r") as file:
            transistor_list: list = []
            for i, line in enumerate(file):
                line = line.strip()
                if not i or not len(line): continue

                # A line starting with M identifies a transistor, wich means its connected to availabel nodes
                if "M" in line[0] or "X" in line[0]:
                    # Im not sure if those are actually source and drain, but doesent matter to identifing them
                    trantype, source, gate, drain, *_ = [token.lower() for token in line.split()]
                    transistor_list.append((trantype[1] == "p", [source, gate, drain]))
                    for node in [source, gate, drain]:
                        nodes.add(node)
        return {node for node in nodes if node not in tension_sources}, Graph(transistor_list, tension_sources)

    def get_output(self) -> dict:
        """
        Reads data in the output.txt file.

        Returns:    
            dict: a dict containing all data formatted as {'label': data}
        """
        data: dict = {}
        with open(path.join(self.path_to_folder,"output.txt"), "r") as output:
            for linha in output:
                data.update(self.__format_output_line(linha))
        self.output = data
        return data
    
    def get_peak_tension(self, inclination: str, nodMeas: bool = False) -> float:
        """
        Reads the peak tension of a node.

        Args:
            inclination (str): Inclination measured. Must be 'rise' or 'fall'.
            nodMeas (bool): Node measured is an output = False; is not an output = True.
        
        Returns:
            float: peak tension measured.
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

    def get_nodes_tension(self, nodes: list) -> dict:
        """
        Reads the max and min tension of given nodes.

        Args:
            nodes (list[str]): List of node names to be retrieved.
        
        Returns:
            Returns: a dict in the form {node: (min_tension, max_tension)}
        """
        output = self.get_output()
        return {node: (output[f"min{node}"].value, output[f"max{node}"].value) for node in nodes}
    
    def get_tension(self) -> tuple:
        """
        Reads the max and min tension of a node.

        Returns:
            tuple: A tuple containing the max and min tensions.
        """
        output = self.get_output()
        return (output["maxnod"].value, output["minnod"].value)
    
    def __get_csv_data(self, filename: str, start: str = None) -> dict:
        """
        Reads a csv file (usually mc0.csv or mt0.csv) as returns its data.

        Args:
            filename (str): name of the file to be read.
            start (str): substring which indicates the reading starts in the next line.
            
        Returns:    
            dict: The columns of the csv of the form data[label] = [column vector]
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
                    valor = None if valores[index].strip() == "failed" else spice_to_float(valores[index])
                    data[chave].append(valor)
        
        return data

    def get_mc_faults(self, circuit_name: str, sim_num: int, inclination: str, vdd: float) -> int:
        """
        Returns the number of simulations that resulted in a fault in a MC simulation.

        Args:    
            circuit_name (str): Name of the circuit.
            sim_num (int): Number of Monte Carlo simulations done.
            inclination (str): Inclination of fault on the output. Must be 'rise' or 'fall'.
            vdd (float): Vdd of the simulations.
        
        Returns:
            int: Number of simulations that faulted.
        """

        faults: int = 0

        data: dict = self.__get_csv_data(path.join(self.path_to_folder,'circuits',circuit_name,f"{circuit_name}.mt0.csv"), ".TITLE")

        inclination_corr = "mincor" if inclination == "fall" else "maxcor"
        inclination_tens = "minout" if inclination == "fall" else "maxout"

        for i in range(sim_num):
            # current_pico = dados[inclinacao_corr][i]
            peak_tension = data[inclination_tens][i]

            if inclination == "fall" and peak_tension < vdd / 2 or inclination == "rise" and peak_tension > vdd / 2:
                faults += 1
        return faults

    def get_delay(self) -> float:
        """
        Reads the delay measured from the output.txt file.
            
        Returns:    
            float: The delay measured.
        """

        output = self.get_output()

        delays: list = [output["atraso_rr"].value, output["atraso_ff"].value, output["atraso_rf"].value, output["atraso_fr"].value]
        if None in delays:
            return 0
        
        # Sorting
        for i, delay in enumerate(delays):
            delays[i] = abs(delay)
        delays.sort()

        # Basically because we are running all kinds of delay measures delays[2] and delays[3] contain nonsense so we get only delays[1] witch will be the gratest

        return delays[1]
    
    def get_mc_instances(self, circ_name: str) -> dict:
        """
        Reads the instances in <circuit>.mc0.csv.

        Args:    
            circ_name (str): Name of the circuit.
        
        Returns:
            dict: Instances of variability.
        """
        instances: dict = {}

        
        data: dict = self.__get_csv_data(path.join(self.path_to_folder,'circuits',circ_name,f"{circ_name}.mc0.csv"), "$ IRV")

        ps: str = "pmos_rvt:@:phig_var_p:@:IGNC"
        ns: str = "nmos_rvt:@:phig_var_n:@:IGNC"

        for i, pmos, nmos in zip(data["index"], data[ps], data[ns]):
            instances[int(float(i))] = [float(pmos), float(nmos)]
        return instances
    
    def get_mc_instances_bulk(self, circ_name: str) -> dict:
        """
        Reads the instances in <circuit>.mc0.csv.

        Args:    
            circ_name (str): Name of the circuit.
        
        Returns:
            dict: Instances of variability.
        """
        instances: dict = {}

        
        data: dict = self.__get_csv_data(path.join(self.path_to_folder,'circuits',circ_name,f"{circ_name}.mc0.csv"), "$ IRV")

        ps: str = "pmos_bulk:@:vth0_var_p:@:IGNC"
        ns: str = "nmos_bulk:@:vth0_var_n:@:IGNC"

        for i, pmos, nmos in zip(data["index"], data[ps], data[ns]):
            instances[int(float(i))] = [float(pmos), float(nmos)]
        return instances

class SpiceRunner(ABC):
    """ 
    Responsible for running spice. Used as a Interface for spice to the rest of the system.
    """

    # This is a huge problem, this variable is a class variable not a object variable
    # I want you to be able to call with SpiceRunner().Vdd(0.5) for example but for that the Vdd context manager
    # Must know path_to_folder of the SpiceRunner instance, wich seems to be very hard to do
    file_manager = None

    def __init__(self, path_to_folder: str = "project") -> None:
        """
        Constructor

        Args:
            path_to_folder (str): relative path into the folder that contain spice files.
        """
        self.path_to_folder = path_to_folder
        # self.default(0.7)
        SpiceRunner.file_manager = SpiceFileManager(path_to_folder=path_to_folder)

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
        def __init__ (self, let: LET, current: float = None):
            self.let = let
            if current == None:
                self.current = let.current
            else:
                self.current = current

        def __enter__(self):
            SpiceRunner.file_manager.set_pulse(self.let, self.current)
            SpiceRunner.file_manager.measure_pulse(self.let.node_name, self.let.output_name)

        def __exit__(self, type, value, traceback):
            pass
            # SpiceRunner.file_manager.set_pulse(self.let, 0)

    class Vss():
        """
        Context Manager that sets the vss of the simulation.
        """
        def __init__ (self, vss: float):
            self.vss = vss

        def __enter__(self):
            SpiceRunner.file_manager.set_vss(self.vss)

        def __exit__(self, type, value, traceback):
            pass
    
    class Vdd():
        """
        Context Manager that sets the vdd of the simulation.
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
        def __init__ (self, inputs: list, vdd: float, vss: float = 0):
            """
            Constructor.

                inputs (list[int]): Input logical values, either 0 or 1.
                vdd (float): Input vdd.
                vdd (float): Input vss.
            """
            self.vdd = vdd
            self.vss = vss
            self.inputs = {}
            for entrada in inputs:
                self.inputs[entrada.name] = entrada.signal

        def __enter__(self):
            SpiceRunner.file_manager.set_signals(self.inputs, self.vdd, self.vss)

        def __exit__(self, type, value, traceback):
            pass

    def _run_spice(self, filename: str, labels: list = None) -> None:
        """
        Runs spice and dumps labels into output.txt.

        Args:    
            filename (str): Name of the file.
            labels (list[str]): labels to be dumped
        """
        pass
    
    def default(self, vdd: float) -> None:
        """
        Sets circuit to default configuration, includind vdd, no fault and no MC.

        Args:
            vdd (float): Standard vdd of the simulation.
        """
        self.file_manager.set_vdd(vdd)
        self.file_manager.set_vss(0)
        self.file_manager.set_pulse(LET(0, vdd, "none", "none", [None, None]))
        self.file_manager.set_monte_carlo(0)

    def get_nodes(self, circ_name: str, tension_sources: list = None) -> set:
        """
        Parse a <circut_name>.cir file and gets all nodes connected to transistor devices.

        Args:    
            curcuit_name (str): name of the circuit to be parsed.
            tension_sources (list[str]): Nodes that should be ignored.
        
        Returns:
            set: The label of all nodes.
        """
        return SpiceRunner.file_manager.get_nodes(circ_name, tension_sources)

    def run_delay(self, filename: str, input_name: str, output_name: str, inputs: list) -> float:
        """
        Returns the delay of shortest path from a input to and output.

        Args:
            filename (str): Name of the file.
            input_name (str): Name of the input node from where the delay is propagated.
            output_name (str): Name of the output node where the delay propagates to.
            inputs (list[Signal_Input]): A list of Signal_Input objects.

        Returns:    
            float: The delay of shortest path from the input to the output.
        """
        
        # Set the signals to be simualted
        SpiceRunner.file_manager.measure_delay(input_name, output_name, sim_config.vdd)
        SpiceRunner.file_manager.set_signals({input.name: input.signal for input in inputs}, sim_config.vdd)
        # Runs the simulation in the respective folder
        self._run_spice(filename, ["atraso_rr", "atraso_rf", "atraso_fr", "atraso_ff"])
        # Gets and returns the results
        delay = SpiceRunner.file_manager.get_delay()
        return delay
    
    def run_SET(self, filename: str, let: LET, current: float = None) -> tuple:
        """
        Returns the peak voltage output for a given let.

        Args:    
            filename (str): Name of the file.
            let (LET): let simulated.
            current (float): current of the fault. If left as None let.current will be used.

        Returns:    
            tuple: A tuple containing the peak tension at the node where the fault originated and output.
        """
        # Sets the SET
        with self.SET(let, current):
            # Runs the simulation
            self._run_spice(filename, ["minout", "maxout", "minnod", "maxnod"])
            # Gets the peak tensions in the node and output
            peak_node = SpiceRunner.file_manager.get_peak_tension(let.orientacao[0], True)
            peak_output = SpiceRunner.file_manager.get_peak_tension(let.orientacao[1])
        return (peak_node, peak_output)
    
    def run_pulse_width(self, filename: str, let: LET, current: float = None) -> float:
        """
        Returns the pulse width of the propagated fault.

        Args:    
            filename (str): Name of the file.
            let (LET): Let to be simulated.
            current (float): current to be simulated. If None then let.current will be used.

        Returns:    
            float: Fault width at output.
        """
        with self.SET(let, current):
            SpiceRunner.file_manager.measure_pulse_width(let)
            self._run_spice(filename, ["larg"])
            output = SpiceRunner.file_manager.get_output()
        
        try:
            if output["larg"].value == None:
                return None

            return abs(output["larg"].value)
        except KeyError:
            return None

    def run_nodes_value(self, filename: str, nodes: list) -> dict:
        """
        Runs the standard circuit and retrieves all the nodes min and max tensions

        Args:    
            filename (str): Name of the file.
            vdd (float): Vdd of the simulation.
            nodes (list[str]): A list of node names to be measured.

        Returns:
            dict: a dict in the form {node: (min_tension, max_tension)}
        """
        measure_labels = [f"max{node}" for node in nodes] + [f"min{node}" for node in nodes]
        self.file_manager.measure_nodes(nodes)
        self._run_spice(filename, measure_labels)
        return self.file_manager.get_nodes_tension(nodes)

    def run_simple_MC(self, circuit_name: str, name_name: str, output_name: str, sim_num: int, output_incl: str, vdd: float) -> int:
        """
        Returns the number of MC simulation that faulted.

        Args:    
            circuit_name (str): Name of the circuit.
            name_name (str): Name of the node.
            output_name (str): Name of the output.
            sim_num (int): Number of simulations.
            output_incl (str): Inclination of fault at the output.
            vdd (float): Vdd of the simulation.

        Returns:    
            int: The number of simulations that faulted.
        """
        SpiceRunner.file_manager.measure_pulse(name_name, output_name)
        with self.Monte_Carlo(sim_num):
            self._run_spice(path.join(self.path_to_folder,"circuits",circuit_name), f"{circuit_name}.cir", ["minout", "maxout"])
        return SpiceRunner.file_manager.get_mc_faults(circuit_name, sim_num, output_incl, vdd)

    def run_MC_var(self, filename: str, circuit_name: str, sim_num: int) -> dict:
        """
        Returns the MC variability points.

        Args:
            filename (str): Name of the file
            circuit_name (str): Name of the circuit.
            sim_num (int): Number of simulations.

        Returns:    
            dict: MC variability instances.
        """
        with self.Monte_Carlo(sim_num):
            self._run_spice(filename)
        return SpiceRunner.file_manager.get_mc_instances(circuit_name)

class NGSpiceRunner(SpiceRunner):
    def _run_spice(self, filename: str, labels: list = None) -> None:
        """
        Runs spice and dumps labels into output.txt.

        Args:    
            filename (str): Name of the file.
            labels (list[str]): labels to be dumped
        """
        f = '\|'
        command = f"cd {path.join(self.path_to_folder,'circuits',filename.replace('.cir',''))} ; ngspice -b < {filename} 2>&1 "
        if labels is not None: command += f"| grep \"{f.join(labels)}\" "
        command += f"> {path.join('..','..','output.txt')}"
        os.system(command)

class HSpiceRunner(SpiceRunner):
    def _run_spice(self, filename: str, labels: list = None) -> None:
        """
        Runs spice and dumps labels into output.txt.

        Args:    
            filename (str): Name of the file.
            labels (list[str]): labels to be dumped
        """
        f = '\|'
        command = f"cd {path.join(self.path_to_folder,'circuits',filename.replace('.cir',''))} ; hspice {filename} "
        if labels is not None: command += f"| grep \"{f.join(labels)}\" "
        command += f"> {path.join('..','..','output.txt')}"
        os.system(command)

    def test_spice(self) -> bool:
        """
        Testes if spice is working. If not will exit as nothing can be done without spice.
        """
        os.system(f"hspice {path.join('debug','empty.cir')} > {path.join('debug','output.txt')}")
        with open("output.txt", "r") as file:
            for linha in file:
                if "Cannot connect to license server system" in linha:
                    return True
        return False

HSRunner = HSpiceRunner()
sim_config.runner = NGSpiceRunner

# Runs a bunch of routine checks to see if the Spice Interface is running accordingly
if __name__ == "__main__":

    with InDir("debug"):
        print("Testing Spice Interface...")
        ptf = path.join("project")
        from ..circuit.circuito import Circuito
        TestRunner = NGSpiceRunner(path_to_folder=ptf)
        TestManager = SpiceFileManager(path_to_folder=ptf)
        vdd = 0.9
        TestRunner.default(vdd)

        # TestRunner.test_spice()
        
        # igl = ["a","b","cin","na","nb","ncin","ncout","nsum","gate_p15", "drain_p15", "gate_p16", "drain_p16", "gate_q15", "drain_q15", "gate_q16", "drain_q16"]
        # fadder = Circuito("fadder", ptf, 0.7).from_nodes(["a1","b1","cin1"],["sum","cout"], igl)
        # fadder.graph.set_logic([("a1",0), ("b1",0), ("cin1",0),("vdd",1),("gnd",0),("vss",0),("vcc",1)])
        # assert fadder.graph.is_affected_by("sum") == {'a1', 'cin1', 'p9_n6', 'b1', 'p3_p4', 'p1_p2', 'p11_p12', 'n6_n7', 'p10_p11', 'sum', 'p2_n1'}, "IS AFFECTED BY FUNCTION FAILED"
        
        # exit()

        print("\tTesting node tensions...")
        nand_test = Circuito("nand").from_json()
        for vi, entrada in zip([0,0], nand_test.inputs): entrada.signal = vi
        with TestRunner.Vdd(vdd), TestRunner.Inputs(nand_test.inputs, vdd):
            assert TestRunner.run_nodes_value(nand_test.file, ["i1", "g1"])["i1"][0] - 0.104784 < 10e-3, "TENSIONS RUN FAILED"

        print("\tTesting circuit parsing...")
        nor_test = Circuito("nor").from_nodes(["a","b"],["g1"])
        assert {nodo.name for nodo in nor_test.nodes} == {"g1", "i1", "a", "b", "ng1"}, "CIRCUIT PARSING FAILED"

        print("\tTesting SET simulation with known SET value...")
        nand_test = Circuito("nand").from_json()
        valid_input = [0, 1] 
        valid_let = LET(156.25, vdd, "g1", "g1", ["fall", "fall"], valid_input)
        expected_let_value = 0.36585829999999997
        for vi, entrada in zip(valid_input, nand_test.inputs): entrada.signal = vi
        with TestRunner.Vdd(vdd), TestRunner.Inputs(nand_test.inputs, vdd):#, TestRunner.MC_Instance(4.7443, 4.3136):
            peak_node, peak_output = TestRunner.run_SET(nand_test.file, valid_let)
            assert abs(peak_node-expected_let_value) <= 10e-1, f"SET SIMULATION FAILED simulated: {peak_node} expected: {expected_let_value}"

        # print("\tTesting delay simulation with known delay value...")
        # delay_input = [1, "delay"]
        # expected_delay_value = 9.1557e-12
        # for vi, entrada in zip(delay_input, nand_test.inputs): entrada.signal = vi
        # with TestRunner.Vdd(vdd), TestRunner.Inputs(nand_test.inputs, vdd):
        #     delay = TestRunner.run_delay(nand_test.file, "b", "g1", nand_test.inputs)
        #     assert abs(delay - expected_delay_value) <= 10e-6, "DELAY SIMULATION FAILED"

        # print("\tTesting MC points generation...")
        # assert len(TestRunner.run_MC_var(nand_test.file, nand_test.name, 10)) == 10, "MC POINTS GENERATION FAILED"
        
        print("Spice Interface OK.")