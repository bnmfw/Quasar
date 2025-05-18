"""
This is the class responsible for writing .cir files. 
"""

from ..ckt.components import LET
from ..cfg.simulationConfig import sim_config
from os import path
from typing import TextIO
from contextlib import contextmanager

measure_window = (1.0, 3.8)


class SpiceFileWriter:
    """
    Responsible for writing the .cir files used by Spice.
    """

    def __init__(self, path_to_folder: str = path.join("project")) -> None:
        """
        Constructor.

        Args:
            path_to_folder (str): relative path into the folder that contain spice files.
        """
        self.path_to_folder = path_to_folder
        self.path_to_include = path.join(path_to_folder, "include")

        @contextmanager
        def custom_open(filename):
            f = open(path.join(self.path_to_include, filename), "w")
            try:
                yield f
            finally:
                f.close()

        self.write = custom_open

    def __write_peak_meas(
        self,
        file: TextIO,
        label: str,
        peak: str,
        quantity: str,
        node: str,
        start: float,
        finish: float,
    ) -> None:
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

        file.write(
            f".meas tran {label} {peak} {quantity}({node}) from={start}n to={finish}n\n"
        )

    def __write_trig_meas(
        self,
        file: TextIO,
        label: str,
        trig: str,
        trig_value: float,
        trig_inclin: str,
        targ: str,
        targ_value: float,
        targ_inclin: str,
    ) -> None:
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

        file.write(
            f".meas tran {label} TRIG v({trig}) val='{trig_value}' {trig_inclin}=1 TARG v({targ}) val='{targ_value}' {targ_inclin}=1\n"
        )

    def measure_pulse(self, node: str, output: str) -> None:
        """
        Alters the measure.cir file to track min and max tension on given node and output

        Args:
            node (str): Node with to have min and max tensions measured
            output (str): Output to have min and max tensions measured
        """
        with self.write("measure.cir") as file:
            file.write(
                "*File with measures of lowest and highest values in node and output\n"
            )
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
        with self.write("measure.cir") as file:
            file.write("*File with measures of lowest and highest values in node\n")
            self.__write_peak_meas(file, "minnod", "min", "V", node, *measure_window)
            self.__write_peak_meas(file, "maxnod", "max", "V", node, *measure_window)

    def measure_nodes(self, nodes: list) -> None:
        """
        Alters the measure.cir file to track the min and max value of given nodes.

        Args:
            nodes (list[str]): List of node names to be measured.
        """
        with self.write("measure.cir") as file:
            file.write(
                "*File with measured of lowest and highest values in list of nodes\n"
            )
            for node in nodes:
                self.__write_peak_meas(
                    file, f"min{node}", "min", "V", node, *measure_window
                )
                self.__write_peak_meas(
                    file, f"max{node}", "max", "V", node, *measure_window
                )

    def set_vdd(self, vdd: float) -> None:
        """
        Alters the vdd.cir file to set the vdd of the simulations.

        Args:
            vdd (float): Defines the vdd of the simulation.
        """
        with self.write("vdd.cir") as file:
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
        with self.write("vss.cir") as file:
            file.write("*File with the vss tension used by all circuits\n")
            file.write(f"Vvss vss gnd {vss}\n")

    def set_signals(self, inputs: dict, vdd: float, vss: float = 0) -> None:
        """
        Alters the fontes.cir file defining the input values of the simulation.

        Args:
            vdd (float): the vdd of the simulation.
            inputs (dict): dict with input values in the form {input_name: input_value}
        """

        with self.write("fontes.cir") as file:
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
                        file.write(
                            f"PWL(0n {vss} 1n {vss} 1.01n {vdd} 3n {vdd} 3.01n {vss})\n"
                        )
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

        if not let.orient[0] in {"fall", "rise", None}:
            raise ValueError(f"Recieved: {let.orient[0]} instead of a edge")
        if current == None:
            current = let.current

        with self.write("SETs.cir") as sets:
            sets.write("*SET faults\n")
            sets.write(
                sim_config.fault_model.spice_string(
                    let.node_name, current, let.orient[0]
                )
                + "\n"
            )

    def measure_delay(self, input: str, out: str, vdd: float) -> None:
        """
        Altes the measure.cir file to measure the delay from one input to one output.

        Args:
            input (str): name of the input node.
            out (str): name of the output node.
            vdd (float): value of the vdd of the simulation.
        """

        with self.write("measure.cir") as file:
            file.write("*File with the dealys to be measured\n")
            half_vdd = str(vdd / 2)
            self.__write_trig_meas(
                file, "atraso_rr", input, half_vdd, "rise", out, half_vdd, "rise"
            )
            self.__write_trig_meas(
                file, "atraso_rf", input, half_vdd, "rise", out, half_vdd, "fall"
            )
            self.__write_trig_meas(
                file, "atraso_ff", input, half_vdd, "fall", out, half_vdd, "fall"
            )
            self.__write_trig_meas(
                file, "atraso_fr", input, half_vdd, "fall", out, half_vdd, "rise"
            )
            # self.__write_trig_meas(file, "largura", out, half_vdd, "fall", out, half_vdd, "rise")

    def measure_pulse_width(self, let: LET) -> None:
        """
        Alters the measure.cir file to measure the fault width of the let on the output.
        The fault width is the time the output node is flipped by the fault.

        Args:
            let (LET): let modeled.
        """
        with self.write("measure.cir") as file:
            file.write("*File with the fault width to be measured\n")
            tensao = str(let.vdd * 0.5)
            self.__write_trig_meas(
                file,
                "larg",
                let.node_name,
                tensao,
                "rise",
                let.node_name,
                tensao,
                "fall",
            )

    def set_monte_carlo(self, simulations: int = 0) -> None:
        """
        Sets the monte carlo parameter in the monte_carlo.cir file.

        Args:
            simulations (int): number o Monte Carlo simulations.
        """
        with self.write("monte_carlo.cir") as mc:
            mc.write("*mc sweep file\n")
            mc.write(".tran 0.01n 4n")
            if simulations:
                mc.write(f" sweep monte={simulations}")
