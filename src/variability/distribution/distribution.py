"""
Generate a Random distribution of points
"""

from abc import ABC
from dataclasses import dataclass


class RandomDistributor(ABC):

    def random_distribution(self, n_points: int, *args) -> dict:
        """
        Generates a random distribution

        Args:
            n_points (int): Number of points to be generated.
            *args: Other arguments for the distribution

        Returns:
            dict: A dict of the coordinates of each dimension in each point
        """


@dataclass
class Distribution(ABC):
    None
