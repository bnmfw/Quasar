"""
Average Predictor class
"""

from .predictor import AbstractPredictor


class AveragePredictor(AbstractPredictor):
    """
    The Prediction is the average of all the observed data
    """

    def __init__(self):
        self.points = 0
        self.average = 0

    def add_data(self, var: tuple, current: float) -> None:
        self.average = self.average * self.points + current
        self.points += 1
        self.average /= self.points

    def predict(self, var):
        if not self.points:
            return None
        return self.average
