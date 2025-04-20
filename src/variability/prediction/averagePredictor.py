"""
Average Predictor class
"""

from .predictor import AbstractPredictor
    
class AveragePredictor (AbstractPredictor):
    """
    The Prediction is the average of all the observed data
    """

    def __init__(self):
        self.points = set()

    def add_data(self, var: tuple, current: float) -> None:
        self.points.add(var, current)

    def predict(self, var):
        return sum(map(lambda point: point[1], self.points)) / len(self.points)