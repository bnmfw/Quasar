"""
Circuit level simulation (Lvl 2) manager.
"""

from .matematica import combinacoes_possiveis, InDir, Time
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

            :param Circuit circuit: Circuit subject to the simulations.
            :param bool report: Whether or not print reports will be done.
        """
        self.circuito = circuit
        self.let_manager = LetFinder(circuit, circuit.path_to_circuits, report=report)
        self.__limite_sup: float = 400
        self.__limite_sim: int = 25
    
    def __possible_LETs(self, nodes: list, outputs: list, input_num: int) -> list:
        """
        Recieves a list of nodes, outputs and the number of inputs and returns all possible lets.

            :param list nodes: List of Node objects (Includes output nodes).
            :param list outputs: List of Node objects interpreted as outputs.
            :param int input_num: Number of inputs in circuit.
            :returns: A list of all possible lets.
        """
        if self.circuito.graph is None:
            lets = [[node, output, signals]\
                    for node in nodes\
                    for output in outputs\
                    for signals in combinacoes_possiveis(input_num)]
        else:
            lets = [[node, output, signals]\
                    for node in nodes\
                    for output in outputs\
                    for signals in combinacoes_possiveis(input_num) if self.circuito.graph.sees(node.nome, output.nome)]
        lets = list(filter(lambda e: e[0].nome not in {"a", "b", "cin"}, lets))
        for i, let in enumerate(lets):
            let.insert(0, i)
        return lets
    
    def get_atrasoCC(self):
        """
        Sets the delay of shortest path of the circuit.
        """
        critical_input = None
        critical_output = None
        self.circuito.atrasoCC = 0
        sim_num: int = 0

        # Todas as entradas em todas as saidas com todas as combinacoes
        for entrada_analisada in self.circuito.entradas:
            for output in self.circuito.saidas:
                for validacao in combinacoes_possiveis(len(self.circuito.entradas)):

                    # Probabilly a better way to do it, but it is not just enumerate
                    index = 0
                    for entrada in self.circuito.entradas:
                        if entrada != entrada_analisada:
                            entrada.sinal = validacao[index]
                            index += 1
                    entrada_analisada.sinal = "atraso"

                    # Etapa de medicao de atraso
                    delay: float = HSRunner.run_delay(self.circuito.arquivo, entrada_analisada.nome, output.nome, self.circuito.vdd, self.circuito.entradas)

                    sim_num += 1

                    if delay > self.circuito.atrasoCC:
                        self.circuito.atrasoCC = delay
                        critical_output = output.nome
                        critical_input = entrada.nome
        # with open("atrasoCC.txt", "a") as arq:
        #     arq.write(f"entrada: {critical_input}\t saida: {critical_output}\n")
        print(f"Atraso CC do arquivo: {self.circuito.atrasoCC} simulacoes: {sim_num}")

    def atualizar_LETths(self, delay: bool = False):
        """
        Updates the minimal LETs of the circuit.

            :param bool delay: Whether the delay will be considered in the simulations.
        """
        with HSRunner.Vdd(self.circuito.vdd):
            sim_num: int = 0
            self.circuito.LETth = None
            ##### BUSCA DO LETs DO CIRCUITO #####
            for nodo in self.circuito.nodos:
                for let in nodo.LETs:
                    # try: 
                    ##### ATUALIZA OS LETHts COM A PRIMEIRA VALIDACAO #####
                    if relatorio: print(let.nodo_nome, let.saida_nome, let.orientacao, let.validacoes[0])
                    sim, current = self.let_manager.definir_corrente(let, let.validacoes[0], safe=True, delay=delay)
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
                    #         erro.write(f"pmos {pmos} nmos {nmos} {let.nodo_nome} {let.saida_nome} {let.orientacao} {let.validacoes[0]}\n")  
            # print(f"{sim_num} simulacoes feitas na atualizacao")

    def run_let_job(self, _, node, output, input_signals: list, delay: bool) -> tuple:
        """
        Runs a single let job a returns the same let with its minimal current. 
        Method meant to be run cuncurrently 

            :param _: Important for cuncurrency, dont you dare take it out.
            :param Nodo node: Node object where fault originates.
            :param Node output: Output where fault propagates to.
            :param list input_signals: Signal values of inputs.
            :param bool delay: Whether or not delay will be taken into consideration.
            :returns: A tuple with the minimal let and the input signals run.
        """
        let_analisado = LET(None, self.circuito.vdd, node.nome, output.nome, [None, None])
        self.let_manager.definir_corrente(let_analisado, input_signals, delay = delay)
        return (let_analisado, input_signals)
    
    def determinar_LETths(self, delay: bool = False):
        """
        Determines all the minimal LETs of the circuit from all possible configurations.

            :param bool delay: Whether or not delay will be taken into consideration.
        """
        for node in self.circuito.nodos:
            node.LETs = []
    
        jobs = self.__possible_LETs(self.circuito.nodos, self.circuito.saidas, len(self.circuito.entradas))
        
        for j in jobs:
            print(j)
        print()

        manager = ProcessMaster(self.run_let_job, jobs, work_dir=self.circuito.path_to_circuits)
        manager.work((delay,),1)

        lets = manager.return_done()

        for (let, validacao) in lets:
            # Ignora correntes invalidas
            if let.corrente is None or let.corrente > 10000: continue

            for nodo_ in self.circuito.nodos:
                if nodo_.nome == let.nodo_nome:
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
    manager.atualizar_LETths()
    
    print("\tTesting determining minimal LETs...")
    with InDir("debug"):
        ptf = "test_circuits"
        nor_test = Circuito("nor", ptf, 0.7).from_nodes(["a", "b"], ["g1"])
        manager = CircuitManager(nor_test, report=False)
        manager.determinar_LETths()

    print("Circuit Manager OK.")