"""
Module with LetFinder a Level 1 simulation responsible for calculating the minimal Let for a fault given some parameters.
"""
from .spiceInterface import SpiceRunner
from .components import LET

class LetFinder:
    """
    Responsible for finding the minimal LET value from a faulted node to an output.
    """
    def __init__(self, circuit, path_to_folder: str = "circuitos", report: bool = False):
        """
        Constructor.

            :param Circuit circuit: A Circuit object to have its let found.
            :param str path_to_folder: relative path into the folder that contain spice files.
            :param bool report: Whether or not the run will report to terminal with prints
        """
        self.circuito = circuit
        self.runner = SpiceRunner(path_to_folder=path_to_folder)
        self.__report = report
        self.__upper_bound: float = 300
        self.__limite_sim: int = 25

    def __fault_inclination(self, node_name: str, vdd: float, let: LET) -> str:
        """
        Returns the fault inclination on the given node.

            :param str node_name: Relevant node.
            :param float vdd: Vdd of the simulation.
            :param LET let: Let of the simulation.
            :returns: A string representing the inclination, either 'rise' or 'fall'
        """
        with self.runner.SET(let, 0):
            min_ten, max_ten = self.runner.run_nodes_value(self.circuito.arquivo, [node_name])[node_name]
        if (max_ten - min_ten) > 0.1 * vdd:
            raise RuntimeError(f"Max and Min vdd have too much variation max: {max_ten} min: {min_ten}")
        return "rise" if max_ten < 0.5 * vdd else "fall"

    def __verify_let_validity(self, vdd: float, let: LET) -> tuple:
        """
        Verifies the validity of the Let, if in this configuration a fault in the node will have an effect on the output.

            :param float vdd: Vdd of the simulation.
            :param LET let: Let being validated.
            :returns: A tuple with a boolean informing the validity of the let and the number of Spice runs.
        """
        node_inclination, output_inclination = let.orientacao
        
        # Checks if the fault is logically masked
        lower_tolerance: float = 0.2
        upper_tolerance: float = 0.8

        node_peak, output_peak = self.runner.run_SET(self.circuito.arquivo, let,self.__upper_bound)

        if self.__report:
            print(f"masking\tnode: {node_peak:.3f} ({int(100*node_peak/vdd)}%)\t output: {output_peak:.3f}")
        if (output_inclination == "rise" and output_peak < vdd * lower_tolerance) or\
            (output_inclination == "fall" and output_peak > vdd * upper_tolerance) or\
            (node_inclination == "rise" and node_peak < vdd * lower_tolerance) or\
            (node_inclination == "fall" and node_peak > vdd * upper_tolerance):
            if self.__report: print("Invalid Let - Masked Fault\n")
            return (False, 1)
        
        # Greater then 2* vdd, weird stuff
        if abs(node_peak/vdd) > 5:
            print("Weird Masking, DIE!\n")
            return (False, 1)

        return (True, 1)

    def __find_maximal_current(self, let: LET) -> float:
        """
        Finds the upper limit for the current of the Let.

            :param LET let: Let to have the upper limit found.
            :returns: The maximal current for the Let.
        """
        self.__upper_bound = 400

        output_inclination = let.orientacao[1]

        for _ in range(10):
            _, output_peak = self.runner.run_SET(self.circuito.arquivo, let, self.__upper_bound)

            # Fault effect on the output was found
            if (output_inclination == "rise" and output_peak > self.circuito.vdd/2) or\
                (output_inclination == "fall" and output_peak < self.circuito.vdd/2):
                if self.__report: print(f"Upper current bound: ({self.__upper_bound})")
                return self.__upper_bound

            self.__upper_bound += 100
        
        print("Upper current too big")
        return 800

    def __find_minimal_current(self, let: LET) -> float:
        """
        Finds the lower limit for the current of the Let.

            :param LET let: Let to have the upper limit found.
            :returns: The minimal current for the Let.
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
            # Encontra a largura minima de pulso pra vencer o atraso
            largura = self.runner.run_pulse_width(self.circuito.arquivo, let, current)
            diferenca_largura: float = None if largura is None else largura - self.circuito.atrasoCC

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

    def definir_corrente(self, let: LET, input_signals: list, safe: bool = False, delay: bool = False) -> tuple:
        """
        Returns the minimal current of a modeled Set to propagate a fault from the node to the output.

            :param LET let: Let modeled including node and output.
            :param list input_signals: Logical value of each input.
            :param bool False: Whether the Let is already known to be valid.
            :param bool delay: Whether the delay of the circuit will be taken into consideration.
            :returns: A tuple containing the simulation number and the current found, if any.
        """
        limite_sup = self.__upper_bound
        precision: float = 0.01
        vdd: float = self.circuito.vdd
        lower_tolerance: float = (1 - precision) * vdd / 2
        upper_tolerance: float = (1 + precision) * vdd / 2
        sim_num: int = 0
        inputs: list = self.circuito.entradas

        # Sets the input signals
        for i in range(len(inputs)):
            inputs[i].sinal = input_signals[i]
        
        with self.runner.Inputs(vdd, inputs):
            
            # Figures the inclination of the simulation
            if let.orientacao[0] is None or not safe:
                let.orientacao[0] = self.__fault_inclination(let.nodo_nome, vdd, let)
                sim_num += 1
            if let.orientacao[1] is None or not safe:
                let.orientacao[1] = self.__fault_inclination(let.saida_nome, vdd, let)
                sim_num += 1
              # debugging report

            if self.__report:
                print("Starting a LET finding job\n"+
                      f"node: {let.nodo_nome}\toutput: {let.saida_nome}\n"+
                      f"vdd: {vdd}\tsafe: {safe}\n"+
                      f"inc1: {let.orientacao[0]}\tinc2: {let.orientacao[1]}\n"+
                      f"input vector: {' '.join([inp.nome+':'+str(inp.sinal) for inp in inputs])}")

            # Checks if the Let configuration is valid
            if not safe:
                valid_let, sim_num = self.__verify_let_validity(vdd, let)
                if not valid_let:
                    let.corrente = None
                    return sim_num, None

            # Binary search variables
            csup: float = limite_sup
            cinf: float = 0 if not delay else self.__find_minimal_current(let)
            current: float = cinf
            sup_flag: bool = False
            peak_tension: float = None
            peak_tension_lower: float = None
            peak_tension_upper: float = None

            # Binary Search
            for i in range(self.__limite_sim):

                _, peak_tension = self.runner.run_SET(self.circuito.arquivo, let, current)
                if self.__report:
                    print(f"{i}\tcurrent: {current:.1f}\tpeak_tension:{peak_tension:.3f}")
                sim_num += 1

                ##### Precision Satisfied #####
                if lower_tolerance < peak_tension < upper_tolerance:
                    if self.__report: print("Minimal Let Found - Precision Satisfied\n")
                    let.corrente = current
                    let.append(input_signals)
                    return sim_num, current

                ##### Convergence ####
                elif csup - cinf < 0.5:
                    # To an exact value #
                    if 1 < current < limite_sup-1 and peak_tension_upper - peak_tension_lower < 3 * (upper_tolerance - lower_tolerance):
                        if self.__report: print("Minimal Let Found - Convergence\n")
                        let.corrente = current
                        let.append(input_signals)
                        return sim_num, current
                    # To 0 #
                    elif current <= 1:
                        if self.__report: print("Minimal Let NOT Found - Lower Divergence\n")
                        let.corrente = None
                        return sim_num, current
                    # To the upper bound #
                    else:
                        if self.__report: print("Upper Divergence - Upper Bound Increased\n")
                        csup += 100
                        limite_sup += 100
                        sup_flag = True

                # Next current calculation #
                elif let.orientacao[1] == "fall":
                    # More intense current = lower peak tension
                    if peak_tension <= lower_tolerance:
                        csup = current
                        peak_tension_lower = peak_tension
                    elif peak_tension >= upper_tolerance:
                        cinf = current
                        peak_tension_upper = peak_tension
                else:
                    # More intense current = higher peak tension
                    if peak_tension <= lower_tolerance:
                        cinf = current
                        peak_tension_lower = peak_tension
                    elif peak_tension >= upper_tolerance:
                        csup = current
                        peak_tension_upper = peak_tension

                current: float = float((csup + cinf) / 2)

            # simulation number limit reached (Very rare) #

            # By chance converges to an exact value #
            if 1 < current < self.__upper_bound - 1:
                if self.__report: print("Minimal Let Found - Maximum Simulation Number Reached\n")
                let.corrente = current
                let.append(input_signals)
            
            # Did not converge #
            else:
                if self.__report: print("Minimal Let NOT Found - Maximum Simulation Number Reached\n")
                let.corrente = 99999 if sup_flag else 11111
            return sim_num, current

if __name__ == "__main__":

    # from .circuito import Circuito
    # fadder = Circuito("fadder", "debug/test_circuits", 0.7).from_nodes(["a","b","cin"],["cout","sum"])
    # let = LET(0, 0.7, "i10", "cout", ["fall", "fall"], [0,0,0])
    # LetFinder(fadder, fadder.path_to_circuits, True).definir_corrente(let, [0,0,0])
    # exit()
   
    # from .circuito import Circuito
    # nand_test = Circuito("nand", "debug/test_circuits", 0.7).from_json()
    # SpiceRunner(nand_test.path_to_circuits).default(0.7)
    # exit()

    print("Testing LET finder...")
    from .circuito import Circuito
    nand = Circuito("nand", "debug/test_circuits", 0.7).from_json()
    
    print("\tTesting Finding Current of safe Let...")
    valid_input = [1,1]
    let = LET(140.625, 0.7, "g1", "g1", [None, None], valid_input)
    assert LetFinder(nand, "debug/test_circuits", False).definir_corrente(let, valid_input, safe=True)[1] == 140.625

    # print("\tTesting Finding Current of invalid unsafe Let...")
    # invalid_let = LET(314.152, 0.7, "g1", "g1", [None, None], valid_input)
    # print(LetFinder(nand, "debug/test_circuits", False).definir_corrente(invalid_let, valid_input, safe=False))

    print("\tTesting Finding Current of valid unsafe Let...")
    valid_input = [1,1]
    unsafe_valid_let = LET(140.625, 0.7, "i1", "g1", [None, None], valid_input)
    assert LetFinder(nand, "debug/test_circuits", False).definir_corrente(unsafe_valid_let, valid_input, safe=False)[1] == 248.4375
    
    print("LET Finder OK")