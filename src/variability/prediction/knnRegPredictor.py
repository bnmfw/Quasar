"""
Regression based on k-nearest neighbors.
"""

from .predictor import AbstractPredictor
from sklearn.neighbors import KNeighborsRegressor
from random import randint

class KnnRegPredictor(AbstractPredictor):
    """
    The Prediction is the average of all the observed data
    """

    def __init__(self):
        self._inputs = []
        self._outputs = []
        self._model = None
        self.name = hex(randint(1, 100000000))

    def add_data(self, var: tuple, current: float) -> None:
        #print(f"var: {var}")
        #print(f"current: {current}")
        self._inputs.append(var)
        self._outputs.append(current)
        self._model = None

    @property
    def model(self):
        # model already exists
        if self._model:
            return self._model
        
        if len(self._inputs) < 3:
            return None
        
        self._model = KNeighborsRegressor(n_neighbors=min(len(self._inputs), 5), weights="distance")
        return self._model.fit(self._inputs, self._outputs)

    def predict(self, var):
        model = self.model
        if model is None:
            return None
        return model.predict([var])[0]
