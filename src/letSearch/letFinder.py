"""
Module with LetFinder a Level 1 simulation responsible for calculating the minimal Let for a fault given some parameters.
"""
from ..simconfig.simulationConfig import sim_config
from ..circuit.components import LET

class LetFinder:
    """
    Responsible for finding the minimal LET value from a faulted node to an output.
    """
    def __init__(self, circuit, path_to_folder: str = "project", report: bool = False):
        """
        Constructor.

        Args:
            circuit (Circuit): A Circuit object to have its let found.
            path_to_folder (str): relative path into the folder that contain spice files.
            report (bool): Whether or not the run will report to terminal with prints.
        """
        self.circuito = circuit
        self.runner = sim_config.runner(path_to_folder=path_to_folder)
        self.__report = report
        self.__upper_bound: float = 300 # Valor maximo considerado da falha
        # 200 é um numero bem razoavel de quanto é uma falha real
        # Pede pro rafael o tga ou tfa ?
        self.__limite_sim: int = 50

    def __fault_inclination(self, node_name: str, vdd: float, let: LET) -> str:
        """
        Returns the fault inclination on the given node.

        Args:
            node_name (str): Relevant node.
            vdd (float): Vdd of the simulation.
            let (LET): Let of the simulation.

        Returns:    
            str: A string representing the inclination, either 'rise' or 'fall'
        """
        with self.runner.SET(let, 0):
            min_ten, max_ten = self.runner.run_nodes_value(self.circuito.file, [node_name])[node_name]
        if (max_ten - min_ten) > 0.1 * vdd:
            raise RuntimeError(f"Max and Min vdd have too much variation max: {max_ten} min: {min_ten}")
        return "rise" if max_ten < 0.5 * vdd else "fall"

    def __verify_let_validity(self, vdd: float, let: LET) -> tuple:
        """
        Verifies the validity of the Let, if in this configuration a fault in the node will have an effect on the output.

        Args:    
            vdd (float): Vdd of the simulation.
            let (LET): Let being validated.
            
        Returns:    
            tuple: A tuple with a boolean informing the validity of the let and the number of Spice runs.
        """
        node_inclination, output_inclination = let.orientacao
        
        # Checks if the fault is logically masked
        lower_tolerance: float = 0.2
        upper_tolerance: float = 0.8

        node_peak, output_peak = self.runner.run_SET(self.circuito.file, let,self.__upper_bound)

        if self.__report:
            print(f"masking\tnode: {node_peak:.3f} ({int(100*node_peak/vdd)}%)\t output: {output_peak:.3f}")
        if (output_inclination == "rise" and output_peak < vdd * lower_tolerance) or\
            (output_inclination == "fall" and output_peak > vdd * upper_tolerance) or\
            (node_inclination == "rise" and node_peak < vdd * lower_tolerance) or\
            (node_inclination == "fall" and node_peak > vdd * upper_tolerance):
            if self.__report: print("Invalid Let - Masked Fault\n")
            return (False, 1)
        
        # Greater then 10*vdd, weird stuff
        if abs(node_peak/vdd) > 10:
            # print(f"Let too great {node_peak/vdd} times! {let} {self.debug_signals}\n")
            return (False, 1)

        return (True, 1)

    def __find_maximal_current(self, let: LET) -> float:
        """
        Finds the upper limit for the current of the Let.

        Args:
            let (LET): Let to have the upper limit found.
        
        Returns:
            float: The maximal current for the Let.
        """
        self.__upper_bound = 400

        output_inclination = let.orientacao[1]

        for _ in range(10):
            _, output_peak = self.runner.run_SET(self.circuito.file, let, self.__upper_bound)

            # Fault effect on the output was found
            if (output_inclination == "rise" and output_peak > sim_config.vdd/2) or\
                (output_inclination == "fall" and output_peak < sim_config.vdd/2):
                if self.__report: print(f"Upper current bound: ({self.__upper_bound})")
                return self.__upper_bound

            self.__upper_bound += 100
        
        print("Upper current too big")
        return 800

    def __find_minimal_current(self, let: LET) -> float:
        """
        Finds the lower limit for the current of the Let.

        Args:
            let (LET): Let to have the upper limit found.
            
        Returns: 
            float: The minimal current for the Let.
        """

        # Variables for the minary search of the current
        limite_sup: float = self.__upper_bound
        csup: float = self.__upper_bound
        cinf: float = 0
        current: float = (csup + cinf)/2

        # Busca binaria para largura de pulso
        diferenca_largura: float = 100
        precisao_largura: float = 0.05e-9

        # Binary search for minimal current
        for _ in range(self.__limite_sim):
            # Encontra a largura minima de pulso pra vencer o delay
            largura = self.runner.run_pulse_width(self.circuito.file, let, current)
            diferenca_largura: float = None if largura is None else largura - self.circuito.SPdelay

            # checks if minimal width is satisfied
            if diferenca_largura and -precisao_largura < diferenca_largura < precisao_largura:
                if self.__report: print(f"PULSO MINIMO ENCONTRADO - PRECISAO SATISFEITA ({current})")
                return current


            if abs(csup - cinf) < 1:
                if self.__report: print(f"PULSO MINIMO ENCONTRADO - DIFERENCA DE BORDAS PEQUENA ({current})")
                return current
            if diferenca_largura == None:
                cinf = current
            elif diferenca_largura > precisao_largura:
                csup = current
            elif diferenca_largura < -precisao_largura:
                cinf = current
            current = (csup + cinf) / 2

        if self.__report: print(f"PULSO MINIMO NAO ENCONTRADO - LIMITE DE SIMULACOES ATINGIDO")
        return None

    def minimal_LET(self, let: LET, input_signals: list, safe: bool = False, delay: bool = False, lowerth: float = None, upperth: float = None) -> tuple:
        """
        Returns the minimal current of a modeled Set to propagate a fault from the node to the output.

        Args:
            let (LET): Let modeled including node and output.
            input_signals (list): Logical value of each input.
            safe (bool): Whether the Let is already known to be valid.
            delay (bool): Whether the delay of the circuit will be taken into consideration.
            lowerth (float, optional): The lowest value the current can get. Defaults to None.
            upperth (float, optional): The highest value the current can get. Defaults to None.
        
        Returns:
            tuple: A tuple containing the simulation number and the current found, if any.
        """
        # self.__report = True
        limite_sup = self.__upper_bound
        precision: float = 0.1
        vdd: float = sim_config.vdd
        lower_tolerance: float = (1 - precision) * vdd / 2
        upper_tolerance: float = (1 + precision) * vdd / 2
        step_up = 100
        sim_num: int = 0
        inputs: list = self.circuito.inputs

        # Sets the input signals
        self.debug_signals = input_signals
        for i in range(len(inputs)):
            inputs[i].signal = input_signals[i]
        
        with self.runner.Inputs(inputs, vdd):
            
            # Figures the inclination of the simulation
            if let.orientacao[0] is None or not safe:
                let.orientacao[0] = self.__fault_inclination(let.node_name, vdd, let)
                sim_num += 1
            if let.orientacao[1] is None or not safe:
                let.orientacao[1] = self.__fault_inclination(let.output_name, vdd, let)
                sim_num += 1
              # debugging report

            if self.__report:
                print("Starting a LET finding job\n"+
                      f"node: {let.node_name}\toutput: {let.output_name}\n"+
                      f"vdd: {vdd}\tsafe: {safe}\n"+
                      f"inc1: {let.orientacao[0]}\tinc2: {let.orientacao[1]}\n"+
                      f"input vector: {' '.join([inp.name+':'+str(inp.signal) for inp in inputs])}")

            # Checks if the Let configuration is valid
            if not safe:
                valid_let, sim_num = self.__verify_let_validity(vdd, let)
                if not valid_let:
                    let.current = None
                    return sim_num, None

            # Binary search variables
            csup: float = limite_sup
            cinf: float = 0 if not delay else self.__find_minimal_current(let)
            current: float = cinf
            sup_flag: bool = False
            peak_tension: float = None
            peak_tension_lower: float = None
            peak_tension_upper: float = None    

            # Rejects a circuit with a LETth higher than upperth
            if upperth is not None:
                csup = upperth
                _, peak_tension = self.runner.run_SET(self.circuito.file, let, csup)
                peak_tension_upper = peak_tension
                if let.orientacao[1] == "fall":
                    if peak_tension <= lower_tolerance:
                        return sim_num, None
                else:
                    if peak_tension >= upper_tolerance:
                        return sim_num, None

            # Rejects a circuit with a LETth lower than lowerth
            if lowerth is not None:
                cinf = lowerth
                _, peak_tension = self.runner.run_SET(self.circuito.file, let, cinf)
                peak_tension_lower = peak_tension
                if let.orientacao[1] == "fall":
                    if peak_tension >= upper_tolerance:
                        return sim_num, None
                else:
                    if peak_tension <= lower_tolerance:
                        return sim_num, None

            # Figures tolerances if not defined
            if peak_tension_lower is None:
                _, peak_tension_lower = self.runner.run_SET(self.circuito.file, let, cinf)
                sim_num += 1
            if peak_tension_upper is None:
                _, peak_tension_upper = self.runner.run_SET(self.circuito.file, let, csup)
                sim_num += 1

            # Binary Search
            for i in range(self.__limite_sim):

                current = float((csup + cinf) / 2)

                try:
                    _, peak_tension = self.runner.run_SET(self.circuito.file, let, current)
                except KeyError:
                    print(let, current, input_signals)
                if self.__report:
                    print(f"{i}\tcurrent: {current:.1f}\tpeak_tension: {peak_tension:.3f}\tbottom: {cinf:.1f}\ttop: {csup:.1f}")
                sim_num += 1

                # print(f"csup: {csup} cinf: {cinf}")
                ##### Precision Satisfied #####
                # if lower_tolerance < peak_tension < upper_tolerance:
                #     if self.__report: print("Minimal Let Found - Precision Satisfied\n")
                #     let.current = current
                #     let.append(input_signals)
                #     return sim_num, current

                ##### Convergence #####
                if csup - cinf < precision:
                    # To an exact value #
                    if 1 < current < limite_sup-1 and peak_tension_upper - peak_tension_lower < 3 * (upper_tolerance - lower_tolerance):
                        if self.__report: print("Minimal Let Found - Convergence\n")
                        let.current = current
                        let.append(input_signals)
                        return sim_num, current
                    # To 0 #
                    elif current <= 1:
                        if self.__report: print("Minimal Let NOT Found - Lower Divergence\n")
                        let.current = None
                        return sim_num, current
                    # To the upper bound #
                    elif current >= limite_sup-1:
                        if self.__report: print("Upper Divergence - Upper Bound Increased\n")
                        csup += step_up
                        limite_sup += step_up
                        step_up += 100
                        sup_flag = True

                # Next current calculation #
                if let.orientacao[1] == "fall":
                    # More intense current = lower peak tension
                    if peak_tension < vdd/2:
                        csup = current
                        peak_tension_lower = peak_tension
                    else:
                        cinf = current
                        peak_tension_upper = peak_tension
                else:
                    # More intense current = higher peak tension
                    if peak_tension < vdd/2:
                        cinf = current
                        peak_tension_lower = peak_tension
                    else:
                        csup = current
                        peak_tension_upper = peak_tension

            # simulation number limit reached (Very rare) #

            # By chance converges to an exact value #
            if 1 < current < self.__upper_bound - 1:
                if self.__report: print("Minimal Let Found - Maximum Simulation Number Reached\n")
                let.current = current
                let.append(input_signals)
            
            # Did not converge #
            else:
                if self.__report: print("Minimal Let NOT Found - Maximum Simulation Number Reached\n")
                let.current = None
            return sim_num, None

if __name__ == "__main__":

    from ..circuit.circuito import Circuito
    from ..spiceInterface.spiceInterface import NGSpiceRunner
    from os import path

    print("Testing LET finder...")
    sim_config.runner = NGSpiceRunner
    nand = Circuito("nand").from_json()
    sim_config.circuit = nand
    
    print("\tTesting Finding Current of safe Let...")
    valid_input = [1,1]
    # target = 111.2548828125
    target = 59.7290039062
    let = LET(target, 0.9, "g1", "g1", [None, None], valid_input)
    measured = LetFinder(nand, report=False).minimal_LET(let, valid_input, safe=True)[1]
    assert abs(measured-target) <= 10e-1, f"LET FINDING FAILED simulated:{measured} expected:{target}"

    # print("\tTesting Finding Current of invalid unsafe Let...")
    # invalid_let = LET(314.152, 0.7, "g1", "g1", [None, None], valid_input)
    # print(LetFinder(nand, "debug/test_circuits", False).minimal_LET(invalid_let, valid_input, safe=False))

    print("\tTesting Finding Current of valid unsafe Let...")
    valid_input = [1,1]
    # target = 140.625
    target = 115.2
    unsafe_valid_let = LET(target, 0.9, "i1", "g1", [None, None], valid_input)
    assert abs(LetFinder(nand, report=False).minimal_LET(unsafe_valid_let, valid_input, safe=False)[1] - target) < 1
    
    print("LET Finder OK")