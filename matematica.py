from math import sqrt
from time import perf_counter

class Time():
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
        if dias: print(f"{dias} dias, ", end='')
        if horas: print(f"{horas} horas, ", end='')
        if minutos: print(f"{minutos} minutos e ", end='')
        print(f"{tempo % 60} segundos de execucao")

# Recebe um inteiro e retorna uma lista de validacoes possiveis
def combinacoes_possiveis(tamanho: int):
    total: int = 2 ** tamanho
    combinacoes: list = []
    for i in range(total):
        binario = bin(i)[2:]
        combinacao: list = []
        for _ in range(tamanho - len(binario)):
            combinacao.append(0)
        for digito in binario:
            combinacao.append(int(digito))
        combinacoes.append(combinacao)
    return combinacoes

# Esta funcao recebe uma sting do tipo numeroEscala como 10.0p ou 24.56m e retorna um float ajustando as casas decimais
def ajustar(tensao: str) -> float:
    tensao = tensao.strip()
    fator_escala: dict = {"a": -18, "f": -15, "p": -12,  
                          "n": -9, "u": -6, "m": -3,
                          "k": 3, "mega": 6, "x": 6, "g": 9, "t": 12}
    # Guarda failed
    if tensao == "failed":
        return None
    
    # Sem grandeza
    if tensao[-1] in {"0","1","2","3","4","5","6","7","8","9","."}:
        return float(tensao)
    
    # Guarda de mega
    if tensao[-4] == "mega":
        return float(tensao[:-4]) * 10 ** 6
    
    # Outras grandezas
    if tensao[-1] in fator_escala.keys():
        return float(tensao[:-1]) * 10 ** fator_escala[tensao[-1]]

    # Nao reconhecido
    raise ValueError(f"Recebi \"{tensao}\" como entrada de ajuste")

# Converte uma corrente para LET
def corrente_para_let(corrente: float) -> float:
    if corrente is None: return None
    return (corrente * 10 ** -6) * (0.000000000164 - (5 * 10 ** -11)) / ((1.08 * 10 ** -14) * 0.000000021)

# Retorna a media dos valores numa lista
def media(lista: list) -> float:
    acumulador: float = 0
    for num in lista:
        acumulador += num
    return acumulador/len(lista)

def desvio_padrao(lista: list, media: float) -> float:
    acumulador: float = 0
    for num in lista:
        acumulador += (media-num) ** 2
    acumulador = acumulador/(len(lista)-1)
    return sqrt(acumulador)


if __name__ == "__main__":
    assert ajustar("  24.56u ") == (24.56 * 10 ** -6), "ajuste_valor FALHOU"
    assert ajustar("2.349e-02") == 0.02349, "ajuste_valor FALHOU"
    #assert converter_binario("0b10", ["x","x","x","x","x"], 5) == [0,0,0,1,0], "converter_binario FALHOU"
    assert corrente_para_let(100) == 50264550.26455026, "corrente_para_let FALHOU" # DEFINIDO PELA PROPRIA FUNCAO
    assert media([1.1, 2.8, 3.6, 4.1]) == 2.9, "media FALHOU"
    assert desvio_padrao([4, 9, 11, 12, 17, 5, 8, 12, 14], media([4, 9, 11, 12, 17, 5, 8, 12, 14])) == 4.176654695380556, "desvio_padrao FALHOU"