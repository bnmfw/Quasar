"""
Module with LogicValue a Level 1 simulation responsible for finding the logical values of nodes given an input
"""
from .spiceInterface import SpiceRunner
from .matematica import InDir
from .circuito import Circuito

class logicValueFinder:
    """
    Class responsible for finding the logical value of indicated nodes in a circuit.
    """
    def __init__(self, circuit, path_to_folder: str = "circuitos", report: bool = False):
        """
        Constructor.

            :param Circuit circuit: A Circuit object to have its let found.
            :param str path_to_folder: relative path into the folder that contain spice files.
            :param bool report: Whether or not the run will report to terminal with prints.
        """
        self.circuit = circuit
        self.runner = SpiceRunner(path_to_folder=path_to_folder)
        self.__report = report
    
    def determine_logic_values(self, vdd: float, nodes: list, input_signals: list):
        """
        Determines the logical values of all given nodes.

            :param float vdd: Vdd of the simulation.
            :param list[str] nodes: List of node names.
            :param list[int] input_signals: Logical value of inputs.
        """

        # tolerance = 0.05 * vdd
        # sim_num = 0
        # logical_value_dict = {node: None for node in nodes}
        
        # # Sets the inputs
        # for inputi, signal in zip(self.circuit.entradas, input_signals):
        #     inputi.signal = signal

        # # Runs the tensions of node
        # with self.runner.Inputs(self.circuit.entradas, vdd):
        #     tension_value_dict = self.runner.run_nodes_value(self.circuit.arquivo, nodes)
        #     sim_num += 1 

        # # Determines the nodes in high logical value
        # for node, (min_ten, max_ten) in tension_value_dict.items():
        #     if abs(vdd-min_ten) < tolerance and abs(vdd-max_ten) < tolerance:
        #         if self.__report:
        #             print(f"{node} in 1 (high) logical value")
        #         logical_value_dict[node] = 1
        
        # # All nodes in high logical value
        # if None not in logical_value_dict.values():
        #     return logical_value_dict


        # Testing vss
        vdd = 0.0
        vss = -0.7

        def lv(x):
            return 1 if abs(x-vdd) < abs(x-vss) else 0

        with self.runner.Vdd(vdd), self.runner.Vss(vss):
            for in_sig in [[0,0], [0,1], [1,0], [1,1]]:
                self.circuit.set_signals(in_sig)
                print(self.circuit.entradas, end = "\t")
                with self.runner.Inputs(self.circuit.entradas, vdd, vss):
                    dici = self.runner.run_nodes_value(self.circuit.arquivo, ["i1", "g1"])
                    for key, value in dici.items():
                        print(key, round((value[0]+value[1])/2,1), end="\t")
                    for key, value in dici.items():
                        print(key, lv((value[0]+value[1])/2), end="\t")
                        if abs(value[0] - value[1]) > 0.01:
                            print("ESQUISITO")
                    print()

        """
        Ideia:
        Determinar quais nodos estão em nível lógico alto por que simplesmeste estarão em vdd.
        Mudar para que haja uma interface para mudar o vss e não fique sempre em gnd
        Tem que desambiguar o que estão flutuando e em 0, provavelmente mudando o vss.
        Tem que experimentar com os circuitos e realmente mudando o vss pra ver como faz pra descobrir os flutuando.
        """

if __name__ == "__main__":

    with InDir("debug"):
        nand = Circuito("nand", "test_circuits", 0.7).from_json()
        logicValueFinder(nand, "test_circuits", True).determine_logic_values(0.7, ["i1", "g1"], [0, 0])