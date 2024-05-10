"""
Configurations of the simulation, such as the modeled fault, transistor model and vdd of the simulation
"""

from .transistorModel import Transistor, FinFET
from .faultModel import FaultModel, FinFETMessengerStandard
# from .spiceInterface import SpiceRunner, NGSpiceRunner, HSpiceRunner
from typing import Type

class SimulationConfig:
    """
    Simulation data
    """
    def __init__(self, vdd: float = 0.7, 
                 fault_model: FaultModel = FinFETMessengerStandard(), 
                 transistor_model: Transistor = FinFET(),
                 runner = None) -> None:
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
        self.runner = runner
    
    def current_to_let(self, current_micro: float) -> float:
        """
        Calculates the LET in MeVcm²/mg

        Args:
            current_micro (float): Current of the modeled fault in micro amps.

        Returns:
            float: LET calculated in MeVcm²/mg
        """
        return self.fault_model.current_to_let(current_micro, self.transistor_model)
    
sim_config = SimulationConfig()