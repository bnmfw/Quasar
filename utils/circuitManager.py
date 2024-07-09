"""
Circuit level simulation (Lvl 2) manager.
"""

from .matematica import all_vector_n_bits, InDir, Time
from .spiceInterface import HSRunner
from .components import *
from .letFinder import LetFinder
from .concorrencia import ProcessMaster
from .predictor import Predictor
from .components import LET, Node
from .circuito import Circuito
relatorio = False

class CircuitManager:
    """
    Circuit level simulations manager.
    """
    def __init__(self, circuit: Circuito, predictor: Predictor = None, report: bool = False):
        """
        Constructor.

        Args:
            circuit (Circuit): Circuit subject to the simulations.
            report (bool, optional): Whether or not print reports will be done.
        """
        self.circuit: Circuito = circuit
        self.let_manager = LetFinder(circuit, circuit.path_to_circuits, report=report)
        self.report: bool = report
        self.min_let_predictor = Predictor(circuit.path_to_my_dir) if predictor is None else predictor
    
    def __possible_LETs(self, nodes: list, outputs: list, inputs: list) -> list:
        """
        Recieves a list of nodes, outputs and the number of inputs and returns all possible lets.

        Args:    
            nodes (list[Node]): List of Node objects (Includes output nodes).
            outputs (list[Node]): List of Node objects interpreted as outputs.
            inputs (list): List of circuit inputs.
        
        Returns:
            list: A list of all possible lets.
        """
        if self.circuit.graph is None:
            lets = [[node, output, signals, None, None]\
                    for node in nodes\
                    for output in outputs\
                    for signals in all_vector_n_bits(len(inputs))]
        else:
            # Generates all valid lets from the circuit graph model
            f = lambda l: list(map(lambda n: n.name, l))
            lets = self.circuit.graph.generate_valid_let_configs(f(nodes), f(outputs), f(inputs), self.circuit.get_node)

        # Enumerates lets
        return lets
    
    def get_atrasoCC(self):
        """
        Sets the delay of shortest path of the circuit.
        """
        critical_input = None
        critical_output = None
        self.circuit.SPdelay = 0
        sim_num: int = 0

        # Todas as inputs em todas as saidas com todas as combinacoes
        for entrada_analisada in self.circuit.inputs:
            for output in self.circuit.saidas:
                for validacao in all_vector_n_bits(len(self.circuit.inputs)):

                    # Probabilly a better way to do it, but it is not just enumerate
                    index = 0
                    for entrada in self.circuit.inputs:
                        if entrada != entrada_analisada:
                            entrada.signal = validacao[index]
                            index += 1
                    entrada_analisada.signal = "delay"

                    # Etapa de medicao de delay
                    delay: float = HSRunner.run_delay(self.circuit.file, entrada_analisada.name, output.name, self.circuit.inputs)

                    sim_num += 1

                    if delay > self.circuit.SPdelay:
                        self.circuit.SPdelay = delay
                        critical_output = output.name
                        critical_input = entrada.name
        # with open("SPdelay.txt", "a") as arq:
        #     arq.write(f"entrada: {critical_input}\t saida: {critical_output}\n")
        print(f"Atraso CC do file: {self.circuit.SPdelay} simulacoes: {sim_num}")

    def update_LETs(self, delay: bool = False, only_lowest: bool = False, var: dict = None):
        """
        Updates the minimal LETs of the circuit.

        Args:    
            delay (bool, optional): Whether the delay will be considered in the simulations. Defaults to False.
            only_lowest (bool, optional): Whether LETs higher than the lowest should be ignored. Deafults to False
            var (dict, optional): Dict containing variability
        """
        sim_num: int = 0
        self.circuit.LETth = None
        ##### BUSCA DO LETs DO CIRCUITO #####
        nodo: Node
        for nodo in self.circuit.nodes:
            let: LET
            for let in nodo.LETs:
                ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                if relatorio: print(let.node_name, let.output_name, let.orientacao, let.input_states[0])

                # Determines a lower threshold 
                # upperth = None if not only_lowest or self.circuit.LETth is None else self.circuit.LETth.current * 1.3

                sim, current = self.let_manager.minimal_LET(let, let.input_states[0], safe=True, delay=delay)

                let.current = current
                sim_num += sim

                if let.current is None: continue
                if relatorio: print(f"current: {let.current}\n")

                # submits raw data
                for input_sig in let.input_states:
                    data = {"node": let.node_name, "output": let.output_name,
                            "in_dir": let.orientacao[0], "out_dir": let.orientacao[1], 
                            "let": let.current,
                            "input": "".join(map(lambda e: str(e), input_sig))}
                    if var is not None: data.update(var)

                    self.min_let_predictor.submit_data(data)

                if self.circuit.LETth is None and current is not None:
                    self.circuit.LETth = let
                elif let < self.circuit.LETth: 
                    self.circuit.LETth = let

    def run_let_job(self, _, node: Node, output: Node, input_signals: list, in_dir: str = None, out_dir: str = None, delay: bool = False) -> tuple:
        """
        Runs a single let job a returns the same let with its minimal current. 
        Method meant to be run cuncurrently.

        Args:
            _: Important for cuncurrency, dont you dare take it out.
            node (Node): Node object where fault originates.
            output (Node): Output where fault propagates to.
            input_signals (list): Signal values of inputs.
            in_dir (str): direction of fault. Either 'rise' or 'fall'.
            out_dir (str): direction of propagated fault at output. Either 'rise' or 'fall'.
            delay (bool): Whether or not delay will be taken into consideration.

        Returns:    
            tuple: A tuple with the minimal let and the input signals run.
        """
        let_analisado = LET(None, sim_config.vdd, node.name, output.name, [in_dir, out_dir])
        sim_num = self.let_manager.minimal_LET(let_analisado, input_signals, delay = delay, safe=True)[0]
        if let_analisado.current is not None:
            self.min_let_predictor.submit_data({"node": node.name, 
                                                "output": output.name, 
                                                "in_dir": in_dir, 
                                                "out_dir": out_dir, 
                                                "current": let_analisado.current, 
                                                "input": "".join(map(lambda e: str(e), input_signals))})
        return (let_analisado, input_signals, sim_num)
    
    def determine_LETs(self, delay: bool = False, progress_report = None):
        """
        Determines all the minimal LETs of the circuit from all possible configurations.

        Args:    
            delay (bool): Whether or not delay will be taken into consideration.
            progress_report (Callable): Optional function that progress can be reported to.
        """
        if self.circuit.loaded:
            # Gathers all jobs
            jobs = []
            for node in self.circuit.nodes:
                for let in node.LETs:
                    for input_config in let.input_states:
                        jobs.append([node, self.circuit.get_node(let.output_name), input_config, let.orientacao[0], let.orientacao[1]])

        else:
            self.circuit.loaded = True
            jobs = self.__possible_LETs(self.circuit.nodes, self.circuit.saidas, self.circuit.inputs)

        for i, job in enumerate(jobs):
            job.insert(0, i)

        for node in self.circuit.nodes:
                node.LETs = []

        if self.report or True:
            [print(j) for j in jobs]
            print()
        
        with self.min_let_predictor:
            manager = ProcessMaster(self.run_let_job, jobs, work_dir=self.circuit.path_to_my_dir, progress_report=progress_report)
            manager.work((delay,),1)

        lets = manager.return_done()

        # for let in lets:
        #     print(let)

        sim_num_acc = 0
        let: LET
        for (let, _, sim_num) in lets:
            sim_num_acc += sim_num

            # Ignora currents invalidas
            if let.current is None: continue

            node = self.circuit.get_node(let.node_name)

            # Updates circuits LETth
            if self.circuit.LETth is None or let < self.circuit.LETth:
                self.circuit.LETth = let
            
            node.add_let(let)
        
        # print(f"total simulations: {sim_num_acc}")

if __name__ == "__main__":


    import sys
    sys.setrecursionlimit(50)
    print("Testing Circuit Manager...")

    from .circuito import Circuito
    ptf = "debug/test_circuits"

    # print("\tTesting update of minimal LETs...")
    # nand_test = Circuito("nand", ptf, 0.7).from_json()
    # manager = CircuitManager(nand_test, report=False)
    # manager.update_LETs()
    
    print("\tTesting determining minimal LETs...")
    with InDir("debug"):
        ptf = "test_circuits"
        nor_test = Circuito("nor", ptf).from_nodes(["a", "b"], ["g1"])
        manager = CircuitManager(nor_test, report=False)
        manager.determine_LETs()
        with open(f"{ptf}/nor/Raw_data.csv", "r") as file:
            data = sorted(list(map(lambda e: e.split(","), file.read().split()[1:])))
            for line in data: line[4] = int(float(line[4]))
            assert data == [['g1', 'g1', 'fall', 'fall', 65, '00'],
                            ['g1', 'g1', 'rise', 'rise', 112, '01'], 
                            ['g1', 'g1', 'rise', 'rise', 113, '10'], 
                            ['g1', 'g1', 'rise', 'rise', 223, '11'], 
                            ['i1', 'g1', 'rise', 'rise', 113, '10']], "LET DETERMINING FAILED"

    print("Circuit Manager OK.")