from abc import ABC
from typing import Callable

class RootSearch(ABC):
    def __init__(self, f: Callable, report: bool = False) -> None:
        self.__report = report

    def root() -> float:
        pass

    def _log(self, text: str) -> None:
        if self.__report: print(text)