"""
Model of the fault to be inserted in the circuit.
"""

from abc import ABC
from .transistorModel import Transistor


class FaultModel(ABC):
    def __init__(self) -> None:
        """
        Constructor
        """
        pass

    def spice_string(
        self, node_name: str, current_micro: float, orientation: str, vss: str = "gnd"
    ) -> str:
        """
        Returns the fault expressed as a spice string

        Args:
            orientation (str): Either rise or fall.
            node_name (str): Name of the node where the fault originates.
            current_micro (float): Current of the modeled fault in micro amps.
            vss (str, optional): Vss of the circuit. Defaults to 'gnd'.

        Returns:
            str: the spice string.
        """

        """
        Exponential Current Source Format:

        I<source_name> <node+> <node-> EXP(<initial_value[0]> <peak_value> <time_when_pulse_starts> <rise_time_constant> <time_when_fall_starts> <fall_time_constant>)
        I out gnd EXP(0 30u 20n 55p 20.05n 164p)
        """
        return None

    def current_to_let(self, current_micro: float, transistor: Transistor) -> float:
        """
        Calculates the LET in MeVcm²/mg

        Args:
            current_micro (float): Current of the modeled fault in micro amps.
            transitor (Transistor): Transistor model used.

        Returns:
            float: LET calculated in MeVcm²/mg
        """
        return None


class DoubleExponential(FaultModel):
    """Double exponential model"""

    def __init__(
        self,
        colection_time_constant_pico: float,
        track_establishment_constant_pico: float,
    ) -> None:
        """
        Constructs the double exponential

        Args:
            colection_time_constant_pico (float): Messenger's equation collection time constant in pico seconds.
            track_establishment_constant_pico (float): Messenger's equation track establishment contant in pico <unit>.
        """
        self.colect_time = colection_time_constant_pico
        self.track_estab = track_establishment_constant_pico
        # Iseu gnd {let.node_name} EXP(0 {current}u 2n 50p 164p 200p)

    def spice_string(
        self,
        node_name: str,
        current_micro: float,
        orientation: str,
        vss: str = "gnd",
        start_time_ns: float = 2,
    ) -> str:
        """
        Returns the fault expressed as a spice string

        Args:
            orientation (str): Either rise or fall.
            node_name (str): Name of the node where the fault originates.
            current_micro (float): Current of the modeled fault in micro amps.
            vss (str, optional): Vss of the circuit. Defaults to 'gnd'.
            start_time_ns (float, optional): Time when the pulse starts in nanoseconds. Defaults to 2.
        Returns:
            str: the spice string.
        """
        return_str = "Iseu "
        if orientation == "rise":
            return_str += f"{vss} {node_name} "
        else:
            return_str += f"{node_name} {vss} "
        return_str += f"EXP(0 {current_micro}u {start_time_ns}n {self.track_estab}p {start_time_ns+self.track_estab/1000}n {self.colect_time}p)"
        return return_str

    def current_to_let(self, current_micro: float, transistor: Transistor) -> float:
        """
        Calculates the LET in MeVcm²/mg

        Args:
            current_micro (float): Current of the modeled fault in micro amps.
            transitor (Transistor): Transistor model used.

        Returns:
            float: LET calculated in MeVcm²/mg
        """
        if current_micro is None:
            return None
        return (
            (current_micro * 1e-6)
            * (self.colect_time * 1e-12 - self.track_estab * 1e-12)
            / (1.08e-14 * transistor.charge_collection_depth_nano * 1e-9)
        )


class FinFETMessengerStandard(DoubleExponential):
    """
    Standard Double Exponential Model for the FinFET
    """

    def __init__(self) -> None:
        super().__init__(164, 50)


if __name__ == "__main__":
    print("Testing Fault Model...")

    print("\tTesting Standard Double Exponential Generation...")
    model = FinFETMessengerStandard()
    assert (
        model.spice_string("test", 100, "rise")
        == "Iseu gnd test EXP(0 100u 2n 50p 2.05n 164p)"
    ), "STANDARD DOUBLE EXPONENTIAL GENERATION"

    from .transistorModel import FinFET

    print("\tTesting Current to LET Conversion...")
    assert (
        model.current_to_let(100, FinFET()) == 50264550.26455026
    ), "current_to_let FAILED"  # DEFINIDO PELA PROPRIA FUNCAO
    print("Fault Model OK")
