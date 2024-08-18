from abc import ABC
from typing import Callable

class RootSearch(ABC):
    def __init__(self, f: Callable) -> None:
        pass

    def root() -> float:
        pass