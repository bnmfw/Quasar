"""
Monte Carlo Simulations Module.
"""

from ..utils.matematica import InDir, Time
from ..circuit.components import *
from ..utils.concorrencia import PersistentProcessMaster
from ..utils.arquivos import CManager
from ..simconfig.simulationConfig import sim_config
from ..circuit.circuitManager import CircuitManager
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
        var: dict = sim_config.runner.run_MC_var(self.circuito.name, n_analysis)

        for i in var:
            var[i][0] = 4.8108 + var[i][0] * (0.05 * 4.8108)/3
            var[i][1] = 4.372 + var[i][1] * (0.05 * 4.372)/3

        # for i in var:
        #     var[i][0] = -0.49155 + var[i][0] * (0.1 * -0.49155)/3
        #     var[i][1] = 0.49396 + var[i][1] * (0.1 * 0.49396)/3

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
        with sim_config.runner.MC_Instance(pmos, nmos):
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

        manager = PersistentProcessMaster(self.run_mc_iteration, None, path.join(self.circuito.path_to_my_dir,"MC"), progress_report=progress_report, work_dir=self.circuito.path_to_my_dir)        

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
    from ..circuit.circuito import Circuito

    print("\tTesting MC simulation...")
    with InDir("debug"):
        nand = Circuito("nand", "test_circuits").from_json()
        sim_config.circuit = nand
        n = 4
        MCManager(nand).full_mc_analysis(4)
        with open(path.join("project","circuits","nand","nand_mc_LET.csv"), "r") as file:
            assert file.read().count("\n") == 4, "MC SIMULATION FAILED"
        
        with open(path.join("project","circuits","nand","Raw_data.csv"), "r") as file:
            data = sorted(list(map(lambda e: e.split(","), file.read().split()[1:])))
            for line in data: line[4] = int(float(line[4]))
            assert data == [['g1', 'g1', 'fall', 'fall', 125, '01', '4.7442987080000005', '4.313604653333333'], ['g1', 'g1', 'fall', 'fall', 125, '10', '4.7442987080000005', '4.313604653333333'], ['g1', 'g1', 'fall', 'fall', 154, '01', '4.8108', '4.372'], ['g1', 'g1', 'fall', 'fall', 154, '10', '4.8108', '4.372'], ['g1', 'g1', 'fall', 'fall', 161, '01', '4.8280387000000005', '4.3524935933333335'], ['g1', 'g1', 'fall', 'fall', 161, '10', '4.8280387000000005', '4.3524935933333335'], ['g1', 'g1', 'fall', 'fall', 181, '01', '4.882529028', '4.494102673333333'], ['g1', 'g1', 'fall', 'fall', 181, '10', '4.882529028', '4.494102673333333'], ['g1', 'g1', 'rise', 'rise', 111, '11', '4.8108', '4.372'], ['g1', 'g1', 'rise', 'rise', 116, '11', '4.8280387000000005', '4.3524935933333335'], ['g1', 'g1', 'rise', 'rise', 127, '11', '4.7442987080000005', '4.313604653333333'], ['g1', 'g1', 'rise', 'rise', 71, '11', '4.882529028', '4.494102673333333'], ['i1', 'g1', 'fall', 'fall', 125, '10', '4.7442987080000005', '4.313604653333333'], ['i1', 'g1', 'fall', 'fall', 154, '10', '4.8108', '4.372'], ['i1', 'g1', 'fall', 'fall', 161, '10', '4.8280387000000005', '4.3524935933333335'], ['i1', 'g1', 'fall', 'fall', 181, '10', '4.882529028', '4.494102673333333'], ['i1', 'g1', 'rise', 'rise', 136, '11', '4.882529028', '4.494102673333333'], ['i1', 'g1', 'rise', 'rise', 195, '11', '4.8108', '4.372'], ['i1', 'g1', 'rise', 'rise', 203, '11', '4.8280387000000005', '4.3524935933333335'], ['i1', 'g1', 'rise', 'rise', 219, '11', '4.7442987080000005', '4.313604653333333']]

    print("MC Manager OK")