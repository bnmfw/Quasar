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
        self._max = 0
        self._min = None

    def add_data(self, var: tuple, current: float) -> None:
        self.average = self.average * self.points + current
        self.points += 1
        self.average /= self.points
        self._max = max(self._max, current)
        if self._min is None:
            self._min = current
        else:
            self._min = min(self._min, current)
        self.range = 5 if self.points < 10 else (self._max - self._min) * 0.05

    def predict(self, var) -> tuple:
        if not self.points:
            return None
        return self.average, self.average - self.range, self.average + self.range
