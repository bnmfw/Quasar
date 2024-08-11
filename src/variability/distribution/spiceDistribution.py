"""
Uses the built in Spice distribution generation
"""

from .distribution import RandomDistribuition
from ...simconfig.simulationConfig import sim_config

class SpiceDistribution(RandomDistribuition):
    def __init__(self) -> None:
        super().__init__()

    def random_distribution(self, n_points: int, *args) -> dict: pass
        # CONTINUE: Here
        var: dict = sim_config.runner.run_MC_var(self.circuito.name, n_analysis)