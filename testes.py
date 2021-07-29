from dataclasses import dataclass, field  # , default_factory
from typing import List


@dataclass(order=True)
class LET:
    valor: float
    vdd: float
    nodo: str
    saida: str
    orientacao: str
    def __post_init__(self):
        self.validacoes = []


let1 = LET(0.0, 0.0, "a", "b", "c")
let1.validacoes.append(10)
let1.validacoes.append(5)
let2 = LET(0.0, 0.0, "a", "b", "c")
print(let1.validacoes)
let2.validacoes.append(7)
let2.validacoes.append(8)
print(let1 == let2)