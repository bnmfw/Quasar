"""
Module with LogicValue a Level 1 simulation responsible for finding the logical values of nodes given an input
"""
from .spiceInterface import SpiceRunner

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

        tolerance = 0.05 * vdd
        sim_num = 0
        logical_value_dict = {node: None for node in nodes}
        
        # Sets the inputs
        for inputi, signal in zip(self.circuit.entradas, input_signals):
            inputi.signal = signal

        # Runs the tensions of node
        with self.runner.Inputs(self.circuit.entradas, vdd):
            tension_value_dict = self.runner.run_nodes_value(self.circuit.arquivo, nodes)
            sim_num += 1 

        # Determines the nodes in high logical value
        for node, (min_ten, max_ten) in tension_value_dict.items():
            if abs(vdd-min_ten) < tolerance and abs(vdd-max_ten) < tolerance:
                if self.__report:
                    print(f"{node} in 1 (high) logical value")
                logical_value_dict[node] = 1
        
        # All nodes in high logical value
        if None not in logical_value_dict.values():
            return logical_value_dict


        """
        Ideia:
        Determinar quais nodos estão em nível lógico alto por que simplesmeste estarão em vdd.
        Mudar para que haja uma interface para mudar o vss e não fique sempre em gnd
        Tem que desambiguar o que estão flutuando e em 0, provavelmente mudando o vss.
        Tem que experimentar com os circuitos e realmente mudando o vss pra ver como faz pra descobrir os flutuando.
        """