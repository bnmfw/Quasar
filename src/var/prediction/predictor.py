"""
Abstract Predictor class. This class recieve data, builds models and return predictions.
"""


class AbstractPredictor:
    """
    Abstract Predictor
    """

    def __init__(self):
        pass

    def add_data(self, var: tuple, current: float) -> None:
        """
        Adds that to the model

        Args:
            var (tuple): The domain variables
            current (float): The image
        """
        pass

    def predict(self, var: tuple) -> float:
        """
        Makes a prediction based on the model

        Args:
            var (tulpe): The domanin variables

        Returns:
            float: The image prediction
        """
        return None
