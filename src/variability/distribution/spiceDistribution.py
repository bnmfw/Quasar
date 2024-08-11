"""
Uses the built in Spice distribution generation
"""

from .distribution import RandomDistributor, Distribution
from ...simconfig.simulationConfig import sim_config
from dataclasses import dataclass

@dataclass
class SpiceGaussianDist(Distribution):
    model: str
    var: str
    mean: float
    sigmas: int
    std_dev: float

class SpiceDistributor(RandomDistributor):
    def __init__(self) -> None:
        super().__init__()

    def random_distribution(self, n_points: int, distributions: list) -> dict:

        points = sim_config.runner.run_MC_var(n_points, distributions)
        treated_points = [[] for _ in points[0]]
        
        dist: SpiceGaussianDist
        for i, dist in enumerate(distributions):
            model = dist.model
            param = dist.var
            mean: float = sim_config.model_manager[model][param]
            for j, p in enumerate(points[i]):
                treated_points[j].append((model, param, mean + p * (dist.std_dev * mean)/dist.sigmas))
    
        treated_points = list(map(lambda p: tuple(p), treated_points))
        return treated_points