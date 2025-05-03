"""
Regression based on k-nearest neighbors.
"""

import warnings
from sklearn.neighbors import KNeighborsRegressor
from random import randint

from .predictor import AbstractPredictor


class KnnRegPredictor(AbstractPredictor):
    """
    The Prediction is the average of all the observed data
    """

    def __init__(
        self,
        n_neighbors: int = 3,
        weights: str = "distance",
        KNeighborsRegressor_kwargs: dict = {},
    ):
        self._n_neighbors = n_neighbors
        self._weights = weights
        self._kwargs = KNeighborsRegressor_kwargs.copy()

        if "n_neighbors" in self._kwargs:
            self._n_neighbors = self._kwargs["n_neighbors"]
            del self._kwargs["n_neighbors"]
            warnings.warn(
                f"KnnRegPredictor: Using 'n_neighbors' found in the 'KNeighborsRegressor_kwargs' (n_neighbors = {self._n_neighbors})."
            )
        if "weights" in self._kwargs:
            self._weights = self._kwargs["weights"]
            del self._kwargs["weights"]
            warnings.warn(
                f"KnnRegPredictor: Using 'weights' found in the 'KNeighborsRegressor_kwargs' (weights = {self._weights})"
            )

        self._inputs = []
        self._outputs = []
        self._model = None
        self._new_points = 0

    def add_data(self, var: tuple, current: float) -> None:
        self._new_points += 1
        self._inputs.append(var)
        self._outputs.append(current)

    @property
    def model(self):
        if self._new_points == 0:
            return self._model
        if len(self._inputs) == 0:
            return None

        # updates the model
        self._new_points = 0
        self._model = KNeighborsRegressor(
            n_neighbors=min(len(self._inputs), self._n_neighbors),
            weights=self._weights,
            **self._kwargs,
        )
        return self._model.fit(self._inputs, self._outputs)

    def predict(self, var: tuple) -> float:
        model = self.model
        if model is None:
            return None
        return model.predict([var])[0]
