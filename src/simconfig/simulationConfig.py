"""
Configurations of the simulation, such as the modeled fault, transistor model and vdd of the simulation
"""

from .transistorModel import Transistor, FinFET, Bulk32
from .faultModel import FaultModel, FinFETMessengerStandard, DoubleExponential
# from .spiceInterface import SpiceRunner, NGSpiceRunner, HSpiceRunner
from ..spiceInterface.spiceModelManager import SpiceModelManager
# from ..circuit.circuito import Circuito
from typing import Type
from os import path

class SimulationConfig:
    """
    Simulation data
    """
    def __init__(self, vdd: float = 0.9,
                 fault_model: FaultModel = FinFETMessengerStandard(), 
                 transistor_model: Transistor = Bulk32(),
                 runner_type = None,
                 circuit = None) -> None:
        """
        Main simulation parameters

        Args:
            vdd (float, optional): Vdd of the circuit simulation. Defaults to 0.7.
            fault_model (FaultModel, optional): Fault model. Defaults to a new instance FinFETMessengerStandard.
            transistor_model (Transistor, optional): Transistor Model. Defaults to a new instance FinFET.
        """
        self.vdd: float = vdd
        self.fault_model: FaultModel = fault_model
        self.transistor_model: Transistor = transistor_model
        self.__circuit = circuit
        self.__runner_type = runner_type
        if runner_type is not None:
            self.runner__ = runner_type()
        self.__model_manager = None
        self.model_obsolete = False

    @property
    def runner_type(self):
        return self.__runner_type
    
    @runner_type.setter
    def runner_type(self, rt):
        self.__runner_type = rt
        self.runner = rt()

    @property
    def circuit(self):
        return self.__circuit
    
    @circuit.setter
    def circuit(self, mm):
        self.__circuit = mm
        self.__model_manager = SpiceModelManager(path.join(self.circuit.path_to_my_dir, self.circuit.file))
        self.model_obsolete = True

    @property
    def model_manager(self):
        self.model_obsolete = True
        return self.__model_manager

    def update(self) -> None:
        if self.model_obsolete:
            self.__model_manager.writeModelFile()
        self.model_obsolete = False

    def current_to_let(self, current_micro: float) -> float:
        """
        Calculates the LET in MeVcm²/mg

        Args:
            current_micro (float): Current of the modeled fault in micro amps.

        Returns:
            float: LET calculated in MeVcm²/mg
        """
        return self.fault_model.current_to_let(current_micro, self.transistor_model)

    def dump(self, path_to_folder: str) -> None:
        with open(path.join(path_to_folder,"config"), "w") as file:
            file.write(f"vdd={self.vdd}\n"
                       f"colection_time={self.fault_model.colect_time}\n"
                       f"track_establishment={self.fault_model.track_estab}\n"
                       f"transistor_depth={self.transistor_model.charge_collection_depth_nano}\n"
                       f"runner={self.runner_type.__name__}")

    def load(self, path_to_folder: str) -> bool:
        if not path.exists(path.join(path_to_folder,"config")):
            return False
        with open(path.join(path_to_folder,"config")) as file:
            tokens: dict = {}
            for line in file:
                a, b = line.split("=")
                tokens[a] = b
        self.vdd = float(tokens["vdd"])
        self.fault_model = DoubleExponential(float(tokens["colection_time"]), float(tokens["track_establishment"]))
        self.transistor_model = Transistor(float(tokens["transistor_depth"]))
        from ..spiceInterface.spiceRunner import NGSpiceRunner, HSpiceRunner
        runners = {classe.__name__: classe for classe in [NGSpiceRunner, HSpiceRunner]}
        self.runner_type = runners[tokens["runner"]]
        return True

sim_config = SimulationConfig()