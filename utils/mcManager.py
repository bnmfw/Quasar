"""
Monte Carlo Simulations Module.
"""

from .matematica import InDir, Time
from .spiceInterface import SpiceRunner
from .components import *
from .concorrencia import PersistentProcessMaster
from .arquivos import CManager
from .circuitManager import CircuitManager
from .predictor import Predictor

class MCManager:
    """
    Responsible for Monte Carlo simulations.
    """
    def __init__(self, circuit, delay: bool = False):
        """
        Constructor.

        Args:    
            circuit Circuito): Circuit to be simulated.
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

    def __determine_variability(self, n_analysis: int) -> list:
        """
        Generates variability points for MC simulation.

        Args:    
            n_analysis (int): Number of total simulations points.

        Returns:
            Returns: A list of items on the format (id, [pmos, nmos])
        """
        var: dict = SpiceRunner(self.circuito.path_to_circuits).run_MC_var(self.circuito.file, self.circuito.name, n_analysis)

        for i in var:
            var[i][0] = 4.8108 + var[i][0] * (0.05 * 4.8108)/3
            var[i][1] = 4.372 + var[i][1] * (0.05 * 4.372)/3

        items = list(var.items())
        return items

    def run_mc_iteration(self, index: int, point: tuple, delay: bool = False):
        """
        Runs a single Monte Carlo simulation.

        Args:
            index (int): Id of the simulation.
            point (tuple): A tuple of floats in the format (pmos, nmos)

        Returns:
            tuple: Data regarding the LETth fault
        """
        pmos, nmos = point
        with SpiceRunner(self.circuito.path_to_circuits).MC_Instance(pmos, nmos):
            if delay: self.circ_man.get_atrasoCC()
            self.circ_man.update_LETs(delay=delay, only_lowest=True, var={"pmos": pmos, "nmos": nmos})
            result = (round(pmos,4), round(nmos,4), self.circuito.LETth.node_name, self.circuito.LETth.output_name, self.circuito.LETth.orientacao, self.circuito.LETth.current, self.circuito.LETth.value, self.circuito.LETth.input_states)
        return result
    
    def full_mc_analysis(self, n_analysis: int, continue_backup: bool = False, delay: bool = False, progress_report = None):
        """
        Runs the full Monte Carlo simulation and puts the results in <path>/<circuit_name>_mc_LET.csv.

        Args:    
            n_analysis (int): Number of MC analysis.
            continue_backup (bool): Whether or not the simulation should continue from a backup if one exists.
            delay (bool): Whether or not delay should be taken into consideration.
            progress_report (Callable): Optional function that progress can be reported to.

        Returns:
            None: Nothing, puts data in <path>/<circuit_name>_mc_LET.csv.
        """

        manager = PersistentProcessMaster(self.run_mc_iteration, None, f"{self.circuito.path_to_my_dir}/MC", progress_report=progress_report, work_dir=self.circuito.path_to_my_dir)        

        # If there is a backup continues from where it stopped.
        if continue_backup and manager.check_backup():
            manager.load_backup()
        else:
            jobs = self.__determine_variability(n_analysis)
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
    print("Testing MC Manager...")
    from .circuito import Circuito

    print("\tTesting MC simulation...")
    with InDir("debug"):
        nand = Circuito("nand", "test_circuits").from_json()
        n = 4
        MCManager(nand).full_mc_analysis(20)
        with open("test_circuits/nand/nand_mc_LET.csv", "r") as file:
            assert file.read().count("\n") == 20, "MC SIMULATION FAILED"

    print("MC Manager OK")