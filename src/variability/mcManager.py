"""
Monte Carlo Simulations Module.
"""

from ..utils.matematica import InDir, Time
from ..circuit.components import *
from ..utils.concorrencia import PersistentProcessMaster
from ..utils.arquivos import CManager
from ..simconfig.simulationConfig import sim_config
from ..circuit.circuitManager import CircuitManager
from .distribution.spiceDistribution import SpiceDistributor, SpiceGaussianDist
from .predictor import Predictor
from os import path

class MCManager:
    """
    Responsible for Monte Carlo simulations.
    """
    def __init__(self, circuit, delay: bool = False):
        """
        Constructor.

        Args:    
            circuit (Circuito): Circuit to be simulated.
            delay (bool): Whether or not delay will be taken into consideration.
        """
        self.circuito = circuit
        # TODO o processo do preditor é inicializado na instanciação, ent o componente circ_man n eh reutilizavel pra multiplas chamadas de analise MC
        self.predictor = Predictor(circuit.path_to_my_dir)
        self.circ_man = CircuitManager(circuit, self.predictor)
        self.delay = delay

        # Estado de simulacoes MC
        self.em_analise: bool = False
        self.total_jobs: int = None
        self.done_jobs: int = 0   

    def determine_variability(self, n_analysis: int, distributions: list) -> list:
        """
        Generates variability points for MC simulation.

        Args:    
            n_analysis (int): Number of total simulations points.
            distributions (list[Distribution]): List of random distributions.

        Returns:
            Returns: A list of items on the format ([pmos, nmos])
        """

        # TODO Isso aqui vai ordenar mal os pontos... Tem que garantir que a ordem dos pontos seja mantida
        # Provavelmente so pode rodar spice distribuions adjacentes

        points = [[] for _ in range(n_analysis)]

        spice_dists = list(filter(lambda d: type(d) == SpiceGaussianDist, distributions))
        if len(spice_dists):
            spice_points = SpiceDistributor().random_distribution(n_analysis, spice_dists)
            for i, p in enumerate(spice_points):
                points[i] += p
        return list(map(lambda i: [i], points))

    def run_mc_iteration(self, point: list, delay: bool = False):
        """
        Runs a single Monte Carlo simulation.

        Args:
            point (list): A list of tuples in the format (model_name, param, value)

        Returns:
            tuple: Data regarding the LETth fault
        """
        result = []
        for model, param, value in point:
            sim_config.model_manager[model][param] = value
            result += [round(value, 4)]

        if delay: self.circ_man.get_atrasoCC()
        
        self.circ_man.update_LETs(delay=delay, var={f"{model}_{param}_param": value for model, param, value in point})
        LETth = self.circuito.LETth
        result += [LETth.node_name, 
                  LETth.output_name, 
                  LETth.orientacao, 
                  LETth.current, 
                  LETth.value, 
                  LETth.input_states]
        return tuple(result)
    
    def full_mc_analysis(self, n_analysis: int, distributions: list, continue_backup: bool = False, delay: bool = False, progress_report = None):
        """
        Runs the full Monte Carlo simulation and puts the results in <path>/<circuit_name>_mc_LET.csv.

        Args:    
            n_analysis (int): Number of MC analysis.
            distributions (list[Distribution]): List random distributions.
            continue_backup (bool): Whether or not the simulation should continue from a backup if one exists.
            delay (bool): Whether or not delay should be taken into consideration.
            progress_report (Callable): Optional function that progress can be reported to.

        Returns:
            None: Nothing, puts data in <path>/<circuit_name>_mc_LET.csv.
        """

        manager = PersistentProcessMaster(self.run_mc_iteration, None, path.join(self.circuito.path_to_my_dir,"MC"), progress_report=progress_report, work_dir=self.circuito.path_to_my_dir)        

        # If there is a backup continues from where it stopped.
        if not continue_backup or not manager.load_backup():
            jobs = self.determine_variability(n_analysis, distributions)
            manager.load_jobs(jobs)

        # Concurrent execution, where the magic happens.
        with self.predictor:
            manager.work((delay,))
            # Dumps data into a csv.
            saida = manager.return_done()
        CManager.tup_to_csv(f"{self.circuito.path_to_my_dir}",f"{self.circuito.name}_mc_LET.csv", saida)

        # Deletes the backup files.
        manager.delete_backup()

if __name__ == "__main__":
    
    from ..spiceInterface.spiceRunner import HSpiceRunner
    from ..circuit.circuito import Circuito
    sim_config.runner_type = HSpiceRunner
    if sim_config.runner.test_spice():
        exit(1)
    sim_config.vdd = 0.9

    print("Testing MC Manager...")

    print("\tTesting MC simulation...")
    with InDir("debug"):
        nand = Circuito("nand_fin").from_json()
        sim_config.circuit = nand
        n = 4
        pvar = SpiceGaussianDist('pmos_rvt', 'phig', sim_config.model_manager['pmos_rvt']['phig'], 3, 0.05)
        nvar = SpiceGaussianDist('nmos_rvt', 'phig', sim_config.model_manager['nmos_rvt']['phig'], 3, 0.05)
        MCManager(nand).full_mc_analysis(4, [pvar, nvar])
        with open(path.join("project","circuits","nand_fin","nand_fin_mc_LET.csv"), "r") as file:
            assert file.read().count("\n") == 4, "MC SIMULATION FAILED"
        
        with open(path.join("project","circuits","nand_fin","Raw_data.csv"), "r") as file:
            data = sorted(list(map(lambda e: e.split(","), file.read().split()[1:])))
            for line in data: 
                line[4] = int(float(line[4]))
            assert sorted(data) == sorted([['g1', 'g1', 'fall', 'fall', 225, '01', '4.7442987080000005', '4.313604653333333'], 
                            ['g1', 'g1', 'fall', 'fall', 225, '10', '4.7442987080000005', '4.313604653333333'], 
                            ['g1', 'g1', 'fall', 'fall', 247, '01', '4.8108', '4.372'], 
                            ['g1', 'g1', 'fall', 'fall', 247, '10', '4.8108', '4.372'], 
                            ['g1', 'g1', 'fall', 'fall', 251, '01', '4.8280387000000005', '4.3524935933333335'], 
                            ['g1', 'g1', 'fall', 'fall', 251, '10', '4.8280387000000005', '4.3524935933333335'], 
                            ['g1', 'g1', 'fall', 'fall', 265, '01', '4.882529028', '4.494102673333333'], 
                            ['g1', 'g1', 'fall', 'fall', 265, '10', '4.882529028', '4.494102673333333'], 
                            ['g1', 'g1', 'rise', 'rise', 144, '11', '4.882529028', '4.494102673333333'], 
                            ['g1', 'g1', 'rise', 'rise', 176, '11', '4.8108', '4.372'], 
                            ['g1', 'g1', 'rise', 'rise', 180, '11', '4.8280387000000005', '4.3524935933333335'], 
                            ['g1', 'g1', 'rise', 'rise', 188, '11', '4.7442987080000005', '4.313604653333333'], 
                            ['i1', 'g1', 'fall', 'fall', 226, '10', '4.7442987080000005', '4.313604653333333'], 
                            ['i1', 'g1', 'fall', 'fall', 247, '10', '4.8108', '4.372'], 
                            ['i1', 'g1', 'fall', 'fall', 252, '10', '4.8280387000000005', '4.3524935933333335'], 
                            ['i1', 'g1', 'fall', 'fall', 265, '10', '4.882529028', '4.494102673333333'], 
                            ['i1', 'g1', 'rise', 'rise', 246, '11', '4.882529028', '4.494102673333333'], 
                            ['i1', 'g1', 'rise', 'rise', 286, '11', '4.8108', '4.372'], 
                            ['i1', 'g1', 'rise', 'rise', 291, '11', '4.8280387000000005', '4.3524935933333335'], 
                            ['i1', 'g1', 'rise', 'rise', 299, '11', '4.7442987080000005', '4.313604653333333']])


    print("MC Manager OK")