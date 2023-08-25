"""
Miscellanious auxilary functions. 
"""
from time import perf_counter
import os

class Time():
    """
    Context manager that prints time in context.
    """
    def __init__(self) -> None:
        pass

    def __enter__(self) -> None:
        self.__start = perf_counter()

    def __exit__(self, a, b, c):
        end = perf_counter()
        tempo = int(end - self.__start)
        dias: int = tempo // 86400
        horas: int = (tempo % 86400) // 3600
        minutos: int = (tempo % 3600) // 60
        if dias: print(f"{dias} days, ", end='')
        if horas: print(f"{horas} hours, ", end='')
        if minutos: print(f"{minutos} minutes and ", end='')
        print(f"{tempo % 60} seconds of execution")

class InDir():
    """
    Context Manager that changes executions to a directory.
    """
    def __init__(self, dir: str):
        """
        Constructor.

            :param str dir: Directory to be changed to.
        """
        self.dir = dir
        self.depth = dir.count("/")+1

    def __enter__(self):
        os.chdir(self.dir)
    
    def __exit__(self, a, b, c):
        os.chdir("/".join([".."] * self.depth))

def all_vector_n_bits(bits: int) -> int:
    """
    Returns of all values from 0 to 2 ^ size in the format of a list of its binary digits.

    Args:
        bits (int): Number of bits

    Returns:
        int: A list of lists of digits.
    """
    total: int = 2 ** bits
    combinations: list = []
    for i in range(total):
        binary = bin(i)[2:]
        combination: list = []
        for _ in range(bits - len(binary)):
            combination.append(0)
        for digit in binary:
            combination.append(int(digit))
        combinations.append(combination)
    return combinations

def spice_to_float(value: str) -> float:
    """
    Recieves a spice value string and returns the value converted to a float.

    Args:
        value (str): Value to be converted.

    Raises:
        ValueError: The input value cannot be interpreted as a spice string value.

    Returns:
        float: Converted value.
    """

    value = value.strip()
    scale_factor: dict = {"a": -18, "f": -15, "p": -12,  
                          "n": -9, "u": -6, "m": -3,
                          "k": 3, "mega": 6, "x": 6, "g": 9, "t": 12}
    # Failed guard
    if value == "failed":
        return None
    
    # No scale
    if value[-1] in {"0","1","2","3","4","5","6","7","8","9","."}:
        return float(value)
    
    # Mega guard
    if value[-4] == "mega":
        return float(value[:-4]) * 10 ** 6
    
    # Other scales
    if value[-1] in scale_factor.keys():
        return float(value[:-1]) * 10 ** scale_factor[value[-1]]

    # Nao reconhecido
    raise ValueError(f"Recieved \"{value}\" as an input os spice_to_float")

def current_to_let(current: float) -> float:
    """
    Converts a current value to a let value in its weird unit.

    Args:
        current (float): Current to be converted.

    Returns:
        float: The Let value.
    """
    if current is None: return None
    return (current * 10 ** -6) * (0.000000000164 - (5 * 10 ** -11)) / ((1.08 * 10 ** -14) * 0.000000021)

if __name__ == "__main__":
    print("Testing Math Module...")
    assert spice_to_float("  24.56u ") == (24.56 * 10 ** -6), "convert_value FAILED"
    assert spice_to_float("2.349e-02") == 0.02349, "convert_value FAILED"
    #assert converter_binario("0b10", ["x","x","x","x","x"], 5) == [0,0,0,1,0], "converter_binario FALHOU"
    assert current_to_let(100) == 50264550.26455026, "current_to_let FAILED" # DEFINIDO PELA PROPRIA FUNCAO
    print("Math Module OK")