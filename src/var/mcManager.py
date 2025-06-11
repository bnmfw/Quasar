"""
Monte Carlo Simulations Module.
"""

from ..utl.math import InDir, Time
from ..ckt.components import *
from ..utl.parallel import ProcessMaster
from ..utl.files import CManager
from ..cfg.simulationConfig import sim_config
from ..ckt.circuitManager import CircuitManager
from .distribution.spiceDistribution import SpiceDistributor, SpiceGaussianDist

# from .distribution import SpiceDistributor, SpiceGaussianDist
from .predictionServer import PredictionServer
from os import path


class MCManager:
    """
    Responsible for Monte Carlo simulations.
    """

    def __init__(self, delay: bool = False, PredictionServer_kwargs: dict = {}):
        """
        Constructor.

        Args:
            circuit (Circuito): Circuit to be simulated.
            delay (bool): Whether or not delay will be taken into consideration.
        """
        # TODO o processo do preditor é inicializado na instanciação, ent o componente circ_man n eh reutilizavel pra multiplas chamadas de analise MC
        self.predictor = PredictionServer(
            sim_config.circuit.path_to_my_dir, **PredictionServer_kwargs
        )
        self.circ_man = CircuitManager(self.predictor)
        self.delay = delay

        # MC simulation states
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

        spice_dists = list(
            filter(lambda d: type(d) == SpiceGaussianDist, distributions)
        )
        if len(spice_dists):
            spice_points = SpiceDistributor().random_distribution(
                n_analysis, spice_dists
            )
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

        if delay:
            self.circ_man.get_atrasoCC()

        sim_num = self.circ_man.update_LETs(
            delay=delay,
            var={f"{model}_{param}_param": value for model, param, value in point},
        )
        LETth = sim_config.circuit.LETth
        result += [
            LETth.node_name,
            LETth.output_name,
            LETth.orient,
            LETth.current,
            LETth.value,
            LETth.input_states,
        ]
        return tuple(result), sim_num

    def full_mc_analysis(
        self,
        n_analysis: int,
        distributions: list,
        continue_backup: bool = False,
        delay: bool = False,
        progress_report=None,
        single_threaded: bool = False,
    ):
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

        jobs = self.determine_variability(n_analysis, distributions)

        manager = ProcessMaster(
            self.run_mc_iteration,
            jobs,
            progress_report=progress_report,
            work_dir=sim_config.circuit.path_to_my_dir,
        )

        # Concurrent execution, where the magic happens.
        with self.predictor:
            if single_threaded:
                manager.work((delay,), 1)
            else:
                manager.work((delay,))
            # Dumps data into a csv.
            output = manager.return_done()
        true_output = []
        total_sim_num = 0
        sim_numbers = []
        for this_output, sim_num in output:
            true_output.append(this_output)
            total_sim_num += sim_num
            sim_numbers.append(sim_num)

        with open(
            f"{f'{sim_config.circuit.path_to_my_dir}/{sim_config.circuit.name}_sim_num.csv'}",
            "w",
        ) as file:
            file.write("sim_num\n")
            for sim_num in sim_numbers:
                file.write(f"{sim_num/sim_config.circuit.distinct_fault_config_num}\n")

        CManager.tup_to_csv(
            f"{sim_config.circuit.path_to_my_dir}",
            f"{sim_config.circuit.name}_mc_LET.csv",
            true_output,
        )

        print(
            f"simulations per fault config = {total_sim_num/(n_analysis*sim_config.circuit.distinct_fault_config_num):.2f}"
        )

    @property
    def results_file(self):
        return path.join(
            sim_config.circuit.path_to_my_dir, sim_config.circuit.name + "_mc_LET.csv"
        )
