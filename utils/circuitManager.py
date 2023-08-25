"""
Circuit level simulation (Lvl 2) manager.
"""

from .matematica import all_vector_n_bits, InDir, Time
from .spiceInterface import HSRunner
from .components import *
from .letFinder import LetFinder
from .concorrencia import ProcessMaster
relatorio = False

class CircuitManager:
    """
    Circuit level simulations manager.
    """
    def __init__(self, circuit, report: bool = False):
        """
        Constructor.

        Args:
            circuit (Circuit): Circuit subject to the simulations.
            report (bool, optional): Whether or not print reports will be done.
        """
        self.circuito = circuit
        self.let_manager = LetFinder(circuit, circuit.path_to_circuits, report=report)
        self.report = report
    
    def __possible_LETs(self, nodes: list, outputs: list, inputs: list) -> list:
        """
        Recieves a list of nodes, outputs and the number of inputs and returns all possible lets.

        Args:    
            nodes (list): List of Node objects (Includes output nodes).
            outputs (list): List of Node objects interpreted as outputs.
            input_num (list): List of circuit inputs.
        
        Returns:
            list: A list of all possible lets.
        """
        if self.circuito.graph is None:
            lets = [[node, output, signals]\
                    for node in nodes\
                    for output in outputs\
                    for signals in all_vector_n_bits(len(inputs))]
        else:
            lets = []
            #Iterates over all input combinations 
            for signals in all_vector_n_bits(len(inputs)):
                # Sets the inputs
                logic_signals = [(inp.name, sig) for inp, sig in zip(inputs, signals)] + [("vdd", 1), ("vcc", 1), ("gnd", 0), ("vss", 0)]
                # print(logic_signals)
                self.circuito.graph.set_logic(logic_signals)
                for output in outputs:
                    # Gets the nodes that affect it
                    effect_group = list(filter(lambda e: e in map(lambda e: e.name, nodes), self.circuito.graph.is_affected_by(output.name)))
                    effect_group = list(filter(lambda e: e[0] not in {"f"}, effect_group))
                    lets += [[self.circuito.get_node(node), output, signals] for node in effect_group]

                # lets = [[node, output, signals]\
                #         for node in nodes\
                #         for output in outputs\
                #         for signals in combinacoes_possiveis(input_num) if self.circuito.graph.sees(node.name, output.name)]
        
        # lets = list(filter(lambda e: e[0].name not in {"a", "b", "cin"}, lets))
        
        # Enumerates lets
        for i, let in enumerate(lets):
            let.insert(0, i)
        return lets
    
    def get_atrasoCC(self):
        """
        Sets the delay of shortest path of the circuit.
        """
        critical_input = None
        critical_output = None
        self.circuito.SPdelay = 0
        sim_num: int = 0

        # Todas as inputs em todas as saidas com todas as combinacoes
        for entrada_analisada in self.circuito.inputs:
            for output in self.circuito.saidas:
                for validacao in all_vector_n_bits(len(self.circuito.inputs)):

                    # Probabilly a better way to do it, but it is not just enumerate
                    index = 0
                    for entrada in self.circuito.inputs:
                        if entrada != entrada_analisada:
                            entrada.signal = validacao[index]
                            index += 1
                    entrada_analisada.signal = "delay"

                    # Etapa de medicao de delay
                    delay: float = HSRunner.run_delay(self.circuito.file, entrada_analisada.name, output.name, self.circuito.vdd, self.circuito.inputs)

                    sim_num += 1

                    if delay > self.circuito.SPdelay:
                        self.circuito.SPdelay = delay
                        critical_output = output.name
                        critical_input = entrada.name
        # with open("SPdelay.txt", "a") as arq:
        #     arq.write(f"entrada: {critical_input}\t saida: {critical_output}\n")
        print(f"Atraso CC do file: {self.circuito.SPdelay} simulacoes: {sim_num}")

    def update_LETs(self, delay: bool = False):
        """
        Updates the minimal LETs of the circuit.

        Args:    
            delay (bool): Whether the delay will be considered in the simulations.
        """
        with HSRunner.Vdd(self.circuito.vdd):
            sim_num: int = 0
            self.circuito.LETth = None
            ##### BUSCA DO LETs DO CIRCUITO #####
            for nodo in self.circuito.nodes:
                for let in nodo.LETs:
                    # try: 
                    ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                    if relatorio: print(let.node_nome, let.saida_nome, let.orientacao, let.validacoes[0])
                    sim, current = self.let_manager.minimal_LET(let, let.validacoes[0], safe=True, delay=delay)
                    sim_num += sim
                    if relatorio: print(f"corrente: {let.corrente}\n")
                    if not self.circuito.LETth:
                        self.circuito.LETth = let
                    elif let < self.circuito.LETth: 
                        self.circuito.LETth = let
                    # except KeyboardInterrupt:
                    #     exit() 
                    # except (ValueError, KeyError):
                    #     with open("erros.txt", "a") as erro:
                    #         erro.write(f"pmos {pmos} nmos {nmos} {let.node_nome} {let.saida_nome} {let.orientacao} {let.validacoes[0]}\n")  
            # print(f"{sim_num} simulacoes feitas na atualizacao")

    def run_let_job(self, _, node, output, input_signals: list, delay: bool) -> tuple:
        """
        Runs a single let job a returns the same let with its minimal current. 
        Method meant to be run cuncurrently.

        Args:
            _: Important for cuncurrency, dont you dare take it out.
            node (Node): Node object where fault originates.
            output (Node): Output where fault propagates to.
            input_signals (list): Signal values of inputs.
            delay (bool): Whether or not delay will be taken into consideration.

        Returns:    
            tuple: A tuple with the minimal let and the input signals run.
        """
        let_analisado = LET(None, self.circuito.vdd, node.name, output.name, [None, None])
        self.let_manager.minimal_LET(let_analisado, input_signals, delay = delay)
        return (let_analisado, input_signals)
    
    def determine_LETs(self, delay: bool = False):
        """
        Determines all the minimal LETs of the circuit from all possible configurations.

        Args:    
            delay (bool): Whether or not delay will be taken into consideration.
        """
        for node in self.circuito.nodes:
            node.LETs = []
    
        jobs = self.__possible_LETs(self.circuito.nodes, self.circuito.saidas, self.circuito.inputs)

        if self.report:
            [print(j) for j in jobs]
            print()
        
        manager = ProcessMaster(self.run_let_job, jobs, work_dir=self.circuito.path_to_circuits)
        manager.work((delay,),)

        lets = manager.return_done()

        for (let, validacao) in lets:
            # Ignora correntes invalidas
            if let.corrente is None or let.corrente > 10000: continue

            for nodo_ in self.circuito.nodes:
                if nodo_.name == let.node_nome:
                    node = nodo_

            # Atualizacao do LETth do circuito
            if self.circuito.LETth is None or let < self.circuito.LETth:
                self.circuito.LETth = let
            
            for let_possivel in node.LETs:
                if let_possivel == let:
                    if let < let_possivel:
                        node.LETs.remove(let_possivel)
                        node.LETs.append(let)
                    elif let.corrente == let_possivel.corrente:
                        let_possivel.append(validacao)
                    break
            else:
                node.LETs.append(let)

if __name__ == "__main__":
    print("Testing Circuit Manager...")

    from .circuito import Circuito
    ptf = "debug/test_circuits"

    print("\tTesting update of minimal LETs...")
    nand_test = Circuito("nand", ptf, 0.7).from_json()
    manager = CircuitManager(nand_test, report=False)
    manager.update_LETs()
    
    print("\tTesting determining minimal LETs...")
    with InDir("debug"):
        ptf = "test_circuits"
        nor_test = Circuito("nor", ptf, 0.7).from_nodes(["a", "b"], ["g1"])
        # fadder_test = Circuito("fadder", ptf, 0.7).from_nodes(["a", "b", "cin"], ["sum", "cout"])
        manager = CircuitManager(nor_test, report=False)
        manager.determine_LETs()

    print("Circuit Manager OK.")