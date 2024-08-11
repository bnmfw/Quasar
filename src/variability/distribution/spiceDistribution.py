"""
Uses the built in Spice distribution generation
"""

from .distribution import RandomDistribuition, GaussianDist
from ...simconfig.simulationConfig import sim_config

class SpiceDistribution(RandomDistribuition):
    def __init__(self) -> None:
        super().__init__()

    def random_distribution(self, n_points: int, model_params: list) -> dict:

        distributions = []
        for model, param in model_params:
            distributions.append(GaussianDist(model, param, sim_config.model_manager[model][param], 3, 0.05))

        points = sim_config.runner.run_MC_var(n_points, distributions)
        treated_points = [[] for _ in points[0]]
        
        for i, (model, param) in enumerate(model_params):
            mean: float = sim_config.model_manager[model][param]
            for j, p in enumerate(points[i]):
                treated_points[j].append((model, param, mean + p * (0.05 * mean)/3))
    
        treated_points = list(map(lambda p: tuple(p), treated_points))
        return treated_points