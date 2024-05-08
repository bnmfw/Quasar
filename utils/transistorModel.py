"""
Class containing the pertinent information for the transistor used in simulations
"""

from dataclasses import dataclass

@dataclass
class Transistor:
    """ Transistor model """
    charge_collection_depth_nano: float

@dataclass
class FinFET(Transistor):
    """ FinFET Standard Model """
    def __init__(self) -> None: super().__init__(charge_collection_depth_nano=21)

if __name__ == "__main__":
    pass
