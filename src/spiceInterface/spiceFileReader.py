"""
Spice Interface.
The interaction with Spice is always done through SpiceRunner.
No other file in the Project should know how to interact with Spice.
Both classes in this file are stateless, therefore the classes are instantiated and its instances are accessed 
"""

from ..utils.math import spice_to_float, InDir
from ..circuit.components import LET
from ..circuit.graph import Graph
from ..simconfig.simulationConfig import sim_config
from os import path
from dataclasses import dataclass
from typing import TextIO
from contextlib import contextmanager

# Defines the start and end of the measuring window, must have only 2 elements
measure_window = (1.0, 3.8)


class SpiceError(Exception):
    pass


class SpiceFileReader:
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
        self.path_to_include = path.join(path_to_folder, "include")

        self.output: dict = None

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
        return self.Meas_from(
            label.strip(), spice_to_float(value), spice_to_float(time)
        )

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
        label_value, targ = label_value_targ.split("targ=")
        label, value = label_value.split("=")
        return self.Meas_targ(
            label.strip(),
            spice_to_float(value),
            spice_to_float(targ),
            spice_to_float(trig),
        )

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
        elif "Error" or "error" in line:
            import sys

            print(
                f"An error was raised during Spice Simulation!\nFull Spice Error Log:"
            )
            sim_config.runner.log_error(sim_config.circuit.file)
            with open(path.join(self.path_to_folder, "error_log.txt")) as file:
                print(file.read())
            sys.exit(1)
        return {measure.label: measure}

    def get_nodes(
        self, circuit_name: str, tension_sources: list = None, inputs: list = None
    ) -> set:
        """
        Parse a <circut_name>.cir file and gets all nodes connected to transistor devices.

        Args:
            curcuit_name (str): name of the circuit to be parsed.
            tension_sources (list[str]): List of tesion sources.
            inputs (list[str]): List of circuit input names

        Returns:
            set: a set containing the label of all nodes and a Graph object.
        """
        nodes = {"vdd", "gnd"}
        if inputs is None:
            inputs = []
        if tension_sources is None:
            tension_sources = ["vcc", "vdd", "gnd", "vss"]
        with open(
            path.join(
                self.path_to_folder, "circuits", circuit_name, f"{circuit_name}.cir"
            ),
            "r",
        ) as file:
            transistor_list: list = []
            for i, line in enumerate(file):
                line = line.strip()
                if not i or not len(line):
                    continue

                # A line starting with M identifies a transistor, wich means its connected to available nodes
                if "M" in line[0] or "X" in line[0]:
                    # Im not sure if those are actually source and drain, but doesent matter to identifing them
                    trantype, source, gate, drain, *_ = [
                        token.lower() for token in line.split()
                    ]
                    transistor_list.append((trantype[1] == "p", [source, gate, drain]))
                    for node in [source, gate, drain]:
                        nodes.add(node)
        return {node for node in nodes if node not in tension_sources}, Graph(
            transistor_list, tension_sources + inputs
        )

    def get_output(self) -> dict:
        """
        Reads data in the output.txt file.

        Returns:
            dict: a dict containing all data formatted as {'label': data}
        """
        data: dict = {}
        with open(path.join(self.path_to_folder, "output.txt"), "r") as output:
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
        return {
            node: (output[f"min{node}"].value, output[f"max{node}"].value)
            for node in nodes
        }

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
                    valor = (
                        None
                        if valores[index].strip() == "failed"
                        else spice_to_float(valores[index])
                    )
                    data[chave].append(valor)

        return data

    def get_mc_faults(
        self, circuit_name: str, sim_num: int, inclination: str, vdd: float
    ) -> int:
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

        data: dict = self.__get_csv_data(
            path.join(
                self.path_to_folder, "circuits", circuit_name, f"{circuit_name}.mt0.csv"
            ),
            ".TITLE",
        )

        inclination_corr = "mincor" if inclination == "fall" else "maxcor"
        inclination_tens = "minout" if inclination == "fall" else "maxout"

        for i in range(sim_num):
            # current_pico = dados[inclinacao_corr][i]
            peak_tension = data[inclination_tens][i]

            if (
                inclination == "fall"
                and peak_tension < vdd / 2
                or inclination == "rise"
                and peak_tension > vdd / 2
            ):
                faults += 1
        return faults

    def get_delay(self) -> float:
        """
        Reads the delay measured from the output.txt file.

        Returns:
            float: The delay measured.
        """

        output = self.get_output()

        delays: list = [
            output["atraso_rr"].value,
            output["atraso_ff"].value,
            output["atraso_rf"].value,
            output["atraso_fr"].value,
        ]
        if None in delays:
            return 0

        # Sorting
        for i, delay in enumerate(delays):
            delays[i] = abs(delay)
        delays.sort()

        # Basically because we are running all kinds of delay measures delays[2] and delays[3] contain nonsense so we get only delays[1] witch will be the gratest

        return delays[1]

    def get_mc_instances(self, circ_name: str, model_vars: list) -> dict:
        """
        Reads the instances in <circuit>.mc0.csv.

        Args:
            circ_name (str): Name of the circuit.
            model_vars (list[tuple[str]]): A list of tuples of the type (model, var).

        Returns:
            list: A list of os lists, each list is the value of that variable in that point.
        """

        data: dict = self.__get_csv_data(
            path.join(
                self.path_to_folder, "circuits", circ_name, f"{circ_name}.mc0.csv"
            ),
            "$ IRV",
        )

        point_headers = [
            f"{model}:@:{var}_{model}_param:@:IGNC" for (model, var) in model_vars
        ]

        return [list(map(lambda v: float(v), data[header])) for header in point_headers]
